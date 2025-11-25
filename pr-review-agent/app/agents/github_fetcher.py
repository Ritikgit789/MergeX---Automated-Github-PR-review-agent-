"""GitHub PR fetcher agent - retrieves PR data from GitHub API."""
from typing import Dict, Any, Optional
from github import Github, GithubException
from app.config import settings
from app.models import AgentState
import logging

logger = logging.getLogger(__name__)


class GitHubFetcherAgent:
    """Agent responsible for fetching PR data from GitHub."""
    
    def __init__(self):
        """Initialize GitHub client."""
        self.github_token = settings.github_token
        self.client = Github(self.github_token) if self.github_token else None
    
    def fetch_pr_data(self, state: AgentState) -> AgentState:
        """
        Fetch PR data from GitHub API.
        
        Args:
            state: Current agent state with pr_url
            
        Returns:
            Updated state with pr_data and diff_content
        """
        if not state.pr_url:
            logger.info("No PR URL provided, skipping GitHub fetch")
            return state
        
        if not self.client:
            state.error = "GitHub token not configured. Please set GITHUB_TOKEN in .env"
            logger.error(state.error)
            return state
        
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
            
            # Get repository and PR
            repo = self.client.get_repo(f"{owner}/{repo_name}")
            pr = repo.get_pull(pr_number)
            
            # Extract PR metadata
            state.pr_data = {
                "number": pr.number,
                "title": pr.title,
                "description": pr.body or "",
                "author": pr.user.login,
                "state": pr.state,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "files_changed": pr.changed_files,
                "additions": pr.additions,
                "deletions": pr.deletions,
            }
            
            # Get diff content
            files = pr.get_files()
            diff_parts = []
            
            for file in files:
                if file.patch:  # Some files may not have patches (e.g., binary files)
                    diff_parts.append(f"--- a/{file.filename}")
                    diff_parts.append(f"+++ b/{file.filename}")
                    diff_parts.append(file.patch)
                    diff_parts.append("")  # Empty line between files
            
            state.diff_content = "\n".join(diff_parts)
            
            logger.info(f"Successfully fetched PR data: {pr.changed_files} files changed")
            
        except GithubException as e:
            state.error = f"GitHub API error: {e.data.get('message', str(e))}"
            logger.error(state.error)
        except Exception as e:
            state.error = f"Error fetching PR data: {str(e)}"
            logger.error(state.error)
        
        return state


# Create singleton instance
github_fetcher = GitHubFetcherAgent()


def fetch_github_pr(state: AgentState) -> AgentState:
    """LangGraph node function for fetching GitHub PR data."""
    return github_fetcher.fetch_pr_data(state)
