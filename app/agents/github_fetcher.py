"""GitHub PR fetcher agent - retrieves PR data from GitHub API."""
from typing import Dict, Any, Optional
from app.config.settings import settings
from app.models.schemas import AgentState
import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)


class GitHubFetcherAgent:
    """Agent responsible for fetching PR data from GitHub."""
    
    def __init__(self):
        """Initialize GitHub client."""
        self.github_token = settings.github_token
        self.timeout = settings.github_api_timeout
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "PR-Review-Agent"
        }
        if self.github_token:
            # Use Bearer token format (modern standard, works with both classic and fine-grained tokens)
            self.headers["Authorization"] = f"Bearer {self.github_token}"
    
    def _get_auth_token(self, state: AgentState) -> Optional[str]:
        """
        Get authentication token from state (user-provided) or fallback to env token.
        Prioritizes user-provided token for private repos.
        
        Args:
            state: Agent state that may contain github_token
            
        Returns:
            Token string or None
        """
        # Priority: 1. User-provided token (from request), 2. Environment token
        if state.github_token:
            return state.github_token
        return self.github_token
    
    def _mask_token(self, token: Optional[str]) -> str:
        """
        Mask token for logging (security: never log full tokens).
        
        Args:
            token: Token to mask
            
        Returns:
            Masked token string (e.g., "ghp_****...****")
        """
        if not token:
            return "None"
        if len(token) <= 8:
            return "****"
        return f"{token[:4]}...{token[-4:]}"
    
    async def fetch_pr_data(self, state: AgentState) -> AgentState:
        """
        Fetch PR data from GitHub API using async httpx.
        
        Args:
            state: Current agent state with pr_url and optional github_token
            
        Returns:
            Updated state with pr_data and diff_content
            
        Security:
            - Token from state (user-provided) takes priority over env token
            - Token is never logged in full (only masked)
            - Token is cleared from state after use
        """
        if not state.pr_url:
            logger.info("No PR URL provided, skipping GitHub fetch")
            return state
        
        # Get token (user-provided or env fallback)
        auth_token = self._get_auth_token(state)
        
        if not auth_token:
            state.error = "GitHub token not configured. " \
                         f"For public repositories, set GITHUB_TOKEN in .env. " \
                         f"For private repositories, provide github_token in the request body."
            logger.error(state.error)
            return state
        
        # Log with masked token (security: never log full tokens)
        masked_token = self._mask_token(auth_token)
        token_source = "user-provided" if state.github_token else "environment"
        logger.info(f"Using GitHub token from {token_source} (masked: {masked_token})")
        
        try:
            # Parse PR URL: https://github.com/owner/repo/pull/123
            pr_url = str(state.pr_url)
            parts = pr_url.rstrip('/').split('/')
            
            if len(parts) < 7 or parts[-2] != 'pull':
                state.error = f"Invalid GitHub PR URL format: {pr_url}"
                logger.error(state.error)
                return state
            
            owner = parts[-4]
            repo_name = parts[-3]
            pr_number = int(parts[-1])
            
            logger.info(f"Fetching PR #{pr_number} from {owner}/{repo_name}")
            
            # Build headers with the appropriate token (user-provided or env)
            request_headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "PR-Review-Agent"
            }
            if auth_token:
                request_headers["Authorization"] = f"Bearer {auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Fetch PR details and files in parallel
                pr_url_api = f"{self.base_url}/repos/{owner}/{repo_name}/pulls/{pr_number}"
                files_url_api = f"{self.base_url}/repos/{owner}/{repo_name}/pulls/{pr_number}/files"
                
                # Make parallel requests
                pr_response, files_response = await asyncio.gather(
                    client.get(pr_url_api, headers=request_headers),
                    client.get(files_url_api, headers=request_headers),
                    return_exceptions=True
                )
                
                # Handle PR response
                if isinstance(pr_response, Exception):
                    raise pr_response
                
                if pr_response.status_code != 200:
                    # Parse error message
                    try:
                        error_data = pr_response.json()
                        error_msg = error_data.get('message', f"HTTP {pr_response.status_code}")
                    except Exception:
                        error_msg = f"HTTP {pr_response.status_code}"
                    
                    # Provide specific error messages for common cases
                    token_hint = "If this is a private repository, provide your github_token in the request body." if not state.github_token else ""
                    
                    if pr_response.status_code == 401:
                        state.error = f"GitHub authentication failed. Please check your token is valid and not expired. {token_hint}"
                    elif pr_response.status_code == 403:
                        state.error = f"Access denied to repository '{owner}/{repo_name}'. This may be a private repository. " \
                                    f"Ensure your GitHub token has access to this repository and the 'repo' scope (for classic tokens) " \
                                    f"or 'Pull requests: Read-only' permission (for fine-grained tokens). {token_hint}"
                    elif pr_response.status_code == 404:
                        state.error = f"Repository '{owner}/{repo_name}' or PR #{pr_number} not found. " \
                                    f"If this is a private repository, ensure your GitHub token has access to it. {token_hint}"
                    else:
                        state.error = f"GitHub API error: {error_msg}"
                    
                    logger.error(f"GitHub API error ({pr_response.status_code}): {state.error}")
                    return state
                
                pr_data = pr_response.json()
                
                # Extract PR metadata
                state.pr_data = {
                    "number": pr_data["number"],
                    "title": pr_data["title"],
                    "description": pr_data.get("body") or "",
                    "author": pr_data["user"]["login"],
                    "state": pr_data["state"],
                    "base_branch": pr_data["base"]["ref"],
                    "head_branch": pr_data["head"]["ref"],
                    "files_changed": pr_data["changed_files"],
                    "additions": pr_data["additions"],
                    "deletions": pr_data["deletions"],
                }
                
                # Handle files response
                if isinstance(files_response, Exception):
                    raise files_response
                
                if files_response.status_code != 200:
                    # Parse error message
                    try:
                        error_data = files_response.json()
                        error_msg = error_data.get('message', f"HTTP {files_response.status_code}")
                    except Exception:
                        error_msg = f"HTTP {files_response.status_code}"
                    
                    # Provide specific error messages for common cases
                    token_hint = "If this is a private repository, provide your github_token in the request body." if not state.github_token else ""
                    
                    if files_response.status_code == 401:
                        state.error = f"GitHub authentication failed. Please check your token is valid and not expired. {token_hint}"
                    elif files_response.status_code == 403:
                        state.error = f"Access denied to repository '{owner}/{repo_name}'. This may be a private repository. " \
                                    f"Ensure your GitHub token has access to this repository and the 'repo' scope (for classic tokens) " \
                                    f"or 'Pull requests: Read-only' permission (for fine-grained tokens). {token_hint}"
                    elif files_response.status_code == 404:
                        state.error = f"Repository '{owner}/{repo_name}' or PR #{pr_number} not found. " \
                                    f"If this is a private repository, ensure your GitHub token has access to it. {token_hint}"
                    else:
                        state.error = f"GitHub API error fetching files: {error_msg}"
                    
                    logger.error(f"GitHub API error fetching files ({files_response.status_code}): {state.error}")
                    return state
                
                files_data = files_response.json()
                
                # Build diff content from files
                diff_parts = []
                files_with_patch = 0
                
                for file_info in files_data:
                    filename = file_info.get("filename", "")
                    patch = file_info.get("patch")
                    status = file_info.get("status", "")
                    
                    if patch:
                        diff_parts.append(f"--- a/{filename}")
                        diff_parts.append(f"+++ b/{filename}")
                        diff_parts.append(patch)
                        diff_parts.append("")  # Empty line between files
                        files_with_patch += 1
                    else:
                        logger.warning(f"No patch found for file: {filename} (status: {status})")
                
                state.diff_content = "\n".join(diff_parts)
                
                logger.info(f"Successfully fetched PR data: {pr_data['changed_files']} files changed, {files_with_patch} files with patches")
                logger.info(f"Diff content length: {len(state.diff_content)}")

                if not state.diff_content and pr_data['changed_files'] > 0:
                    state.error = "No analyzable text changes found. The PR may contain only binary files (PDFs, images, docs) or large files."
                    logger.warning(state.error)
                    return state
            
            # Clear user-provided token from state after successful fetch (security)
            if state.github_token:
                state.github_token = None
                logger.debug("Cleared user-provided token from state after successful fetch")
            
        except httpx.TimeoutException:
            state.error = f"GitHub API request timed out after {self.timeout} seconds"
            logger.error(state.error)
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors with better messages
            status_code = e.response.status_code
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message', e.response.text[:200])
            except Exception:
                error_msg = e.response.text[:200] if e.response.text else "Unknown error"
            
            if status_code == 401:
                state.error = "GitHub authentication failed. Please check your GITHUB_TOKEN is valid and not expired."
            elif status_code == 403:
                state.error = f"Access denied. This may be a private repository. " \
                            f"Ensure your GitHub token has access to the repository and appropriate permissions."
            elif status_code == 404:
                state.error = f"Repository or PR not found. If this is a private repository, ensure your GitHub token has access to it."
            else:
                state.error = f"GitHub API error: HTTP {status_code} - {error_msg}"
            
            logger.error(f"GitHub API HTTP error ({status_code}): {state.error}")
        except Exception as e:
            state.error = f"Error fetching PR data: {str(e)}"
            logger.error(state.error, exc_info=True)
        finally:
            # Always clear user-provided token from state (security: never persist tokens)
            if state.github_token:
                state.github_token = None
                logger.debug("Cleared user-provided token from state")
        
        return state


# Create singleton instance
github_fetcher = GitHubFetcherAgent()


async def fetch_github_pr(state: AgentState) -> AgentState:
    """LangGraph node function for fetching GitHub PR data."""
    return await github_fetcher.fetch_pr_data(state)
