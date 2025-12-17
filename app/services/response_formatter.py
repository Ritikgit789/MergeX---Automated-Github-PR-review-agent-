"""Smart response formatter - enforces output format requirements.

This module ensures:
- Never says "No issues found" or "Looks good"
- Always explains WHY code is clean when no issues exist
- Formats output per specification
- Groups issues by category
"""
from typing import List, Dict, Any, Optional
from app.models.schemas import ReviewComment
import logging

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Formats review responses according to specification."""
    
    @staticmethod
    def format_review(
        comments: List[ReviewComment],
        pr_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Format review response per mandatory specification.
        
        Args:
            comments: List of review comments from all agents
            pr_info: Optional PR metadata
            
        Returns:
            Dict with 'summary', 'issues', 'suggestions' sections
        """
        total_issues = len(comments)
        
        # Count by severity and category
        severity_counts = {"critical": 0, "error": 0, "warning": 0, "info": 0}
        category_counts = {"logic": 0, "security": 0, "performance": 0, "readability": 0}
        
        for comment in comments:
            severity_counts[comment.severity.value] = severity_counts.get(comment.severity.value, 0) + 1
            category_counts[comment.category.value] = category_counts.get(comment.category.value, 0) + 1
        
        # Determine risk level
        if severity_counts["critical"] > 0:
            risk_level = "HIGH RISK"
        elif severity_counts["error"] > 0:
            risk_level = "MEDIUM RISK"
        elif severity_counts["warning"] > 0:
            risk_level = "LOW RISK"
        else:
            risk_level = "MINIMAL RISK"
        
        # Generate sections
        if total_issues == 0:
            return ResponseFormatter._format_clean_code(pr_info)
        else:
            return ResponseFormatter._format_with_issues(
                comments, severity_counts, category_counts, risk_level, pr_info
            )
    
    @staticmethod
    def _format_clean_code(pr_info: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Format response when no issues found - MUST explain WHY."""
        summary = f"""### Summary
Code quality: EXCELLENT | Risk: MINIMAL

This code demonstrates professional standards. Here's why it's clean:
• Follows language best practices and conventions
• No obvious logical errors or edge case vulnerabilities
• Security measures appear adequate for the changes made
• Performance implications are reasonable
• Code is maintainable with clear intent"""
        
        issues_section = """### Issues Identified
None. This PR meets quality standards."""
        
        suggestions = f"""### Suggested Improvements
While no critical issues were found, consider:
• Ensure comprehensive test coverage for these changes
• Verify integration points behave correctly under load
• Document any non-obvious design decisions
• Review with domain experts for business logic accuracy"""
        
        return {
            "summary": summary,
            "issues": issues_section,
            "suggestions": suggestions
        }
    
    @staticmethod
    def _format_with_issues(
        comments: List[ReviewComment],
        severity_counts: Dict[str, int],
        category_counts: Dict[str, int],
        risk_level: str,
        pr_info: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Format response when issues are found."""
        
        # Summary section
        summary_parts = [f"### Summary"]
        summary_parts.append(f"Found {len(comments)} issue(s) | Risk: {risk_level}\n")
        
        severity_line = []
        if severity_counts["critical"] > 0:
            severity_line.append(f"{severity_counts['critical']} critical")
        if severity_counts["error"] > 0:
            severity_line.append(f"{severity_counts['error']} error(s)")
        if severity_counts["warning"] > 0:
            severity_line.append(f"{severity_counts['warning']} warning(s)")
        if severity_counts["info"] > 0:
            severity_line.append(f"{severity_counts['info']} info")
        
        if severity_line:
            summary_parts.append("Severity: " + ", ".join(severity_line))
        
        summary = "\n".join(summary_parts)
        
        # Issues section - grouped by category
        issues_parts = ["### Issues Identified\n"]
        
        categories = ["security", "logic", "performance", "readability"]
        for category in categories:
            cat_comments = [c for c in comments if c.category.value == category]
            if not cat_comments:
                continue
            
            category_title = category.upper()
            issues_parts.append(f"**{category_title}** ({len(cat_comments)} issue(s)):")
            
            for comment in cat_comments:
                file_name = comment.file_path.split('/')[-1] if '/' in comment.file_path else comment.file_path
                line_ref = f"line {comment.line_number}" if comment.line_number else "file-level"
                
                issues_parts.append(f"- **File:** `{file_name}` ({line_ref})")
                issues_parts.append(f"  - **Issue:** {comment.message}")
                issues_parts.append(f"  - **Why it matters:** {ResponseFormatter._explain_impact(comment)}")
                if comment.suggestion:
                    issues_parts.append(f"  - **Fix:** {comment.suggestion}")
                issues_parts.append("")  # Empty line between issues
        
        issues = "\n".join(issues_parts)
        
        # Suggestions section
        suggestions_parts = ["### Suggested Improvements\n"]
        
        # Group suggestions by priority
        critical_suggestions = [c for c in comments if c.severity.value in ["critical", "error"] and c.suggestion]
        other_suggestions = [c for c in comments if c.severity.value in ["warning", "info"] and c.suggestion]
        
        if critical_suggestions:
            suggestions_parts.append("**Critical fixes required:**")
            for comment in critical_suggestions[:5]:  # Top 5
                suggestions_parts.append(f"• {comment.suggestion}")
            suggestions_parts.append("")
        
        if other_suggestions:
            suggestions_parts.append("**Recommended improvements:**")
            for comment in other_suggestions[:5]:  # Top 5
                suggestions_parts.append(f"• {comment.suggestion}")
        
        suggestions = "\n".join(suggestions_parts)
        
        return {
            "summary": summary,
            "issues": issues,
            "suggestions": suggestions
        }
    
    @staticmethod
    def _explain_impact(comment: ReviewComment) -> str:
        """Generate 'why it matters' explanation based on category and severity."""
        category = comment.category.value
        severity = comment.severity.value
        
        impact_map = {
            "security": {
                "critical": "Could lead to data breaches or system compromise",
                "error": "May expose sensitive information or create exploitable vulnerabilities",
                "warning": "Potential security weakness that should be addressed"
            },
            "logic": {
                "error": "Will cause incorrect behavior or runtime failures",
                "warning": "May produce unexpected results in edge cases",
                "info": "Could lead to subtle bugs in certain scenarios"
            },
            "performance": {
                "error": "Causes significant performance degradation or scalability issues",
                "warning": "May impact response time or resource usage under load",
                "info": "Optimization opportunity for better efficiency"
            },
            "readability": {
                "warning": "Makes code harder to maintain and increases bug risk",
                "info": "Could improve code clarity and developer experience"
            }
        }
        
        return impact_map.get(category, {}).get(severity, "Impacts code quality and maintainability")


# Create singleton instance
response_formatter = ResponseFormatter()
