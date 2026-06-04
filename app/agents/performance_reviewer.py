"""Performance reviewer agent - identifies performance issues."""
from typing import Dict
from app.config.settings import settings
from app.models.schemas import AgentState, ReviewComment, ReviewSeverity, ReviewCategory
from app.services.llm_gateway import get_llm_gateway
from app.utils.comment_format import CLEAR_COMMENT_RULES, build_review_comment
import logging
import json

logger = logging.getLogger(__name__)


class PerformanceReviewerAgent:
    """Agent responsible for reviewing performance issues."""
    
    def __init__(self):
        """Initialize the performance reviewer."""
        self.gateway = get_llm_gateway()
        
        # Ultra-strict: ONLY visible bottlenecks
        self.system_prompt = """Expert performance reviewer. ONLY REPORT VISIBLE BOTTLENECKS:

REPORT ONLY IF YOU SEE:
- Nested loops: for x in items: for y in items:
- DB call in loop: for x in items: db.query(x)
- Blocking await missing: def async_func(): requests.get()

NEVER REPORT:
- "May be slow" (speculation)
- "N+1 queries" (unless you see loop + query)
- "Missing caching" (speculation)
- "Could be faster" (vague)

MANDATORY:
- Be 100% certain there is a real pattern (loops, repeated I/O, hot event handlers)
- Explain in simple English, not only a code paste

""" + CLEAR_COMMENT_RULES + """

Return JSON (EMPTY if no visible bottlenecks):
[
  {
    "file_path": "path/to/file",
    "line_number": 42,
    "severity": "warning",
    "message": "Problem: ... Impact: ... Code: ...",
    "suggestion": "Fix: ..."
  }
]

When in doubt, return []."""
    
    async def review_performance(self, state: AgentState) -> dict:
        """
        Review code for performance issues.
        
        Args:
            state: Current agent state with parsed_changes
            
        Returns:
            dict: Update for performance_comments
        """
        if not state.parsed_changes:
            logger.warning("No parsed changes available for performance review")
            return {"performance_comments": []}
        
        try:
            # Build batched changes text
            all_files_text = []
            
            for idx, file_change in enumerate(state.parsed_changes):
                file_path = file_change.get('file_path', 'unknown')
                file_language = file_change.get('language', state.language or 'unknown')
                
                changes_text = []
                for hunk in file_change.get('hunks', []):
                    for change in hunk.get('changes', []):
                        if change['type'] == 'addition':
                            changes_text.append(f"+ {change['content']} (line {change.get('line_number', '?')})")
                        elif change['type'] == 'deletion':
                            changes_text.append(f"- {change['content']}")
                
                if changes_text:
                    file_changes_str = "\n".join(changes_text[:100])
                    file_section = f"\n\n=== File {idx + 1}: {file_path} (Language: {file_language}) ===\n{file_changes_str}"
                    all_files_text.append(file_section)
            
            if not all_files_text:
                return {"performance_comments": []}
            
            combined_changes = "\n".join(all_files_text)
            primary_language = state.language or "unknown"
            
            user_prompt = f"""Review for performance issues (multiple files):

{combined_changes}

Primary Language: {primary_language}
Context: {state.context or 'No additional context'}

IMPORTANT: Include correct file_path for each issue."""
            
            # Call LLM via gateway
            result = await self.gateway.call_llm(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                agent_name="performance_reviewer"
            )
            
            if not result["success"]:
                logger.error(f"Performance review LLM call failed: {result['error']}")
                return {"performance_comments": []}
            
            # Parse response
            comments = []
            try:
                content = result["content"].strip()
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                data = json.loads(content)
                # Handle both list and dict responses
                if isinstance(data, list):
                    issues = data
                elif isinstance(data, dict):
                    issues = data.get('issues', data.get('findings', []))
                else:
                    issues = []
                
                for issue in issues:
                    comments.append(
                        build_review_comment(
                            issue,
                            ReviewCategory.PERFORMANCE,
                            "warning",
                            "performance_reviewer",
                        )
                    )
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse performance review response: {e}")
            except Exception as e:
                logger.error(f"Error processing performance review response: {e}")
            
            logger.info(f"Performance review found {len(comments)} issues")
            return {"performance_comments": comments}
            
        except Exception as e:
            logger.error(f"Error in performance review: {str(e)}", exc_info=True)
            return {"performance_comments": []}


# Create singleton instance
performance_reviewer = PerformanceReviewerAgent()


async def review_performance(state: AgentState) -> dict:
    """LangGraph node function for performance review."""
    return await performance_reviewer.review_performance(state)
