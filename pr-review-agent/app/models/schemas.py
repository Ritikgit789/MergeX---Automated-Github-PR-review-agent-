"""Pydantic models for request/response schemas."""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum


class ReviewSeverity(str, Enum):
    """Severity levels for review comments."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReviewCategory(str, Enum):
    """Categories of review feedback."""
    LOGIC = "logic"
    SECURITY = "security"
    PERFORMANCE = "performance"
    READABILITY = "readability"
    BEST_PRACTICES = "best_practices"


class ReviewComment(BaseModel):
    """A single review comment on code."""
    file_path: str = Field(..., description="Path to the file")
    line_number: Optional[int] = Field(None, description="Line number in the file")
    severity: ReviewSeverity = Field(..., description="Severity of the issue")
    category: ReviewCategory = Field(..., description="Category of the review")
    message: str = Field(..., description="Detailed review message")
    suggestion: Optional[str] = Field(None, description="Suggested fix or improvement")


class GitHubPRRequest(BaseModel):
    """Request to review a GitHub PR."""
    pr_url: HttpUrl = Field(..., description="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")


class ManualDiffRequest(BaseModel):
    """Request to review a manual diff."""
    diff: str = Field(..., description="Unified diff format")
    language: Optional[str] = Field("python", description="Programming language")
    context: Optional[str] = Field(None, description="Additional context about the changes")


class ReviewResponse(BaseModel):
    """Response containing review results."""
    status: str = Field(..., description="Review status (success/error)")
    pr_info: Optional[Dict[str, Any]] = Field(None, description="PR metadata")
    comments: List[ReviewComment] = Field(default_factory=list, description="List of review comments")
    summary: str = Field(..., description="Overall review summary")
    total_issues: int = Field(0, description="Total number of issues found")


class AgentState(BaseModel):
    """State object for LangGraph workflow."""
    # Input
    pr_url: Optional[str] = None
    manual_diff: Optional[str] = None
    language: Optional[str] = "python"
    context: Optional[str] = None
    
    # Intermediate data
    pr_data: Optional[Dict[str, Any]] = None
    diff_content: Optional[str] = None
    parsed_changes: Optional[List[Dict[str, Any]]] = None
    
    # Review results
    logic_comments: List[ReviewComment] = Field(default_factory=list)
    security_comments: List[ReviewComment] = Field(default_factory=list)
    performance_comments: List[ReviewComment] = Field(default_factory=list)
    readability_comments: List[ReviewComment] = Field(default_factory=list)
    
    # Final output
    all_comments: List[ReviewComment] = Field(default_factory=list)
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
