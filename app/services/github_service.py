"""GitHub service for API interactions."""
from typing import Dict, Any, Optional
from github import Github, GithubException
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for GitHub API operations."""
    
    def __init__(self):
        """Initialize GitHub client."""
        self.github_token = settings.github_token
        self.client = Github(self.github_token) if self.github_token else None
    
    def validate_pr_url(self, pr_url: str) -> Dict[str, Any]:
        """
        Validate and parse GitHub PR URL.
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            Dict with owner, repo, and pr_number
            
        Raises:
            ValueError: If URL format is invalid
        """
        parts = pr_url.rstrip('/').split('/')
        
        if len(parts) < 7 or parts[-2] != 'pull':
            raise ValueError(f"Invalid GitHub PR URL format: {pr_url}")
        
        return {
            "owner": parts[-4],
            "repo": parts[-3],
            "pr_number": int(parts[-1])
        }
    
    def get_pr_metadata(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Get PR metadata from GitHub.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            PR metadata dictionary
        """
        if not self.client:
            raise ValueError("GitHub token not configured")
        
        try:
            repository = self.client.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            
            return {
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
                "url": pr.html_url,
            }
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            raise


# Singleton instance
github_service = GitHubService()
