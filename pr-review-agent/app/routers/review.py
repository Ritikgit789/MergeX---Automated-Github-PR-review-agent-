"""Review router for PR review endpoints."""
from fastapi import APIRouter, HTTPException, status
from app.models import GitHubPRRequest, ManualDiffRequest, ReviewResponse
from app.services import review_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/review", tags=["review"])


@router.post("/github", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
async def review_github_pr(request: GitHubPRRequest):
    """
    Review a GitHub Pull Request.
    
    Args:
        request: GitHub PR URL
        
    Returns:
        Review response with comments and summary
        
    Raises:
        HTTPException: If review fails
    """
    try:
        logger.info(f"Received GitHub PR review request: {request.pr_url}")
        
        # Execute review
        response = review_service.review_github_pr(str(request.pr_url))
        
        # Check if review failed
        if response.status == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.summary
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in GitHub PR review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/diff", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
async def review_manual_diff(request: ManualDiffRequest):
    """
    Review a manual diff.
    
    Args:
        request: Manual diff content with language and context
        
    Returns:
        Review response with comments and summary
        
    Raises:
        HTTPException: If review fails
    """
    try:
        logger.info(f"Received manual diff review request (language: {request.language})")
        
        # Execute review
        response = review_service.review_manual_diff(
            diff=request.diff,
            language=request.language or "python",
            context=request.context
        )
        
        # Check if review failed
        if response.status == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.summary
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in manual diff review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/categories")
async def get_review_categories():
    """
    Get available review categories.
    
    Returns:
        List of review categories
    """
    return {
        "categories": [
            {
                "name": "logic",
                "description": "Logical errors, edge cases, and correctness issues"
            },
            {
                "name": "security",
                "description": "Security vulnerabilities and risks"
            },
            {
                "name": "performance",
                "description": "Performance issues and optimization opportunities"
            },
            {
                "name": "readability",
                "description": "Code readability, style, and maintainability"
            }
        ]
    }


@router.get("/severities")
async def get_severity_levels():
    """
    Get available severity levels.
    
    Returns:
        List of severity levels
    """
    return {
        "severities": [
            {
                "level": "critical",
                "description": "Critical issues that must be fixed immediately"
            },
            {
                "level": "error",
                "description": "Errors that should be fixed before merging"
            },
            {
                "level": "warning",
                "description": "Warnings that should be reviewed"
            },
            {
                "level": "info",
                "description": "Informational suggestions for improvement"
            }
        ]
    }
