"""Review service for orchestrating PR reviews."""
from typing import Dict, Any
from app.models import AgentState, ReviewResponse
from app.orchestration import review_workflow
import logging

logger = logging.getLogger(__name__)


class ReviewService:
    """Service for orchestrating PR reviews."""
    
    def review_github_pr(self, pr_url: str) -> ReviewResponse:
        """
        Review a GitHub PR.
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            ReviewResponse with comments and summary
        """
        try:
            # Create initial state
            initial_state = AgentState(pr_url=pr_url)
            
            # Run workflow
            logger.info(f"Starting review workflow for PR: {pr_url}")
            final_state = review_workflow.invoke(initial_state)
            
            # Check for errors
            if final_state.error:
                return ReviewResponse(
                    status="error",
                    summary=f"Review failed: {final_state.error}",
                    comments=[],
                    total_issues=0
                )
            
            # Build response
            return self._build_response(final_state)
            
        except Exception as e:
            logger.error(f"Error reviewing GitHub PR: {str(e)}")
            return ReviewResponse(
                status="error",
                summary=f"Unexpected error: {str(e)}",
                comments=[],
                total_issues=0
            )
    
    def review_manual_diff(self, diff: str, language: str = "python", context: str = None) -> ReviewResponse:
        """
        Review a manual diff.
        
        Args:
            diff: Unified diff content
            language: Programming language
            context: Additional context
            
        Returns:
            ReviewResponse with comments and summary
        """
        try:
            # Create initial state
            initial_state = AgentState(
                manual_diff=diff,
                language=language,
                context=context
            )
            
            # Run workflow
            logger.info("Starting review workflow for manual diff")
            final_state = review_workflow.invoke(initial_state)
            
            # Check for errors
            if final_state.error:
                return ReviewResponse(
                    status="error",
                    summary=f"Review failed: {final_state.error}",
                    comments=[],
                    total_issues=0
                )
            
            # Build response
            return self._build_response(final_state)
            
        except Exception as e:
            logger.error(f"Error reviewing manual diff: {str(e)}")
            return ReviewResponse(
                status="error",
                summary=f"Unexpected error: {str(e)}",
                comments=[],
                total_issues=0
            )
    
    def _build_response(self, state: AgentState) -> ReviewResponse:
        """Build review response from final state."""
        comments = state.all_comments
        
        # Generate summary
        total_issues = len(comments)
        
        if total_issues == 0:
            summary = "✅ No issues found. Code looks good!"
        else:
            # Count by severity
            critical = sum(1 for c in comments if c.severity.value == "critical")
            errors = sum(1 for c in comments if c.severity.value == "error")
            warnings = sum(1 for c in comments if c.severity.value == "warning")
            info = sum(1 for c in comments if c.severity.value == "info")
            
            # Count by category
            logic = sum(1 for c in comments if c.category.value == "logic")
            security = sum(1 for c in comments if c.category.value == "security")
            performance = sum(1 for c in comments if c.category.value == "performance")
            readability = sum(1 for c in comments if c.category.value == "readability")
            
            summary_parts = [f"Found {total_issues} issue(s):"]
            
            if critical > 0:
                summary_parts.append(f"🔴 {critical} critical")
            if errors > 0:
                summary_parts.append(f"❌ {errors} error(s)")
            if warnings > 0:
                summary_parts.append(f"⚠️ {warnings} warning(s)")
            if info > 0:
                summary_parts.append(f"ℹ️ {info} info")
            
            summary_parts.append("\nCategories:")
            if logic > 0:
                summary_parts.append(f"  • Logic: {logic}")
            if security > 0:
                summary_parts.append(f"  • Security: {security}")
            if performance > 0:
                summary_parts.append(f"  • Performance: {performance}")
            if readability > 0:
                summary_parts.append(f"  • Readability: {readability}")
            
            summary = " ".join(summary_parts)
        
        return ReviewResponse(
            status="success",
            pr_info=state.pr_data,
            comments=comments,
            summary=summary,
            total_issues=total_issues
        )


# Singleton instance
review_service = ReviewService()
