"""Logic reviewer agent - identifies logical errors and edge cases."""
from typing import Dict
from app.config.settings import settings
from app.models.schemas import AgentState, ReviewComment, ReviewSeverity, ReviewCategory
from app.services.llm_gateway import get_llm_gateway
from app.utils.comment_format import CLEAR_COMMENT_RULES, build_review_comment
import logging
import json

logger = logging.getLogger(__name__)


class LogicReviewerAgent:
    """Agent responsible for reviewing code logic and correctness."""
    
    def __init__(self):
        """Initialize the logic reviewer."""
        self.gateway = get_llm_gateway()
        
        # Ultra-strict: ONLY observable issues
        self.system_prompt = """Expert code logic reviewer. ULTRA-STRICT RULES:

ONLY REPORT THESE:
1. Syntax errors you can SEE (missing comma, unclosed bracket)
2. Direct contradictions (if x > 5 and x < 3)
3. Obvious typos in visible function/variable names
4. Division by zero with literal 0

NEVER REPORT:
- "Missing X" (you can't know what's missing)
- "Function not defined" (you don't see the whole file)
- "Edge cases" (speculation)
- "Should add" / "Needs" (speculation)
- Line number claims without quoting the actual line

MANDATORY:
- Be 100% certain
- If uncertain, DON'T report it

""" + CLEAR_COMMENT_RULES + """

Return JSON (EMPTY if nothing 100% certain):
[
  {
    "file_path": "path/to/file",
    "line_number": 42,
    "severity": "error",
    "message": "Problem: ... Impact: ... Code: ...",
    "suggestion": "Fix: ..."
  }
]

When in doubt, return []. Better to miss issues than hallucinate."""
    
    async def review_logic(self, state: AgentState) -> dict:
        """
        Review code for logical issues - batches all files in a single LLM call.
        
        Args:
            state: Current agent state with parsed_changes
            
        Returns:
            dict: Update for logic_comments
        """
        if not state.parsed_changes:
            logger.warning("No parsed changes available for logic review")
            return {"logic_comments": []}
        
        try:
            # Build batched changes text for all files
            all_files_text = []
            
            for idx, file_change in enumerate(state.parsed_changes):
                file_path = file_change.get('file_path', 'unknown')
                file_language = file_change.get('language', state.language or 'unknown')
                
                # Build changes text for this file
                changes_text = []
                for hunk in file_change.get('hunks', []):
                    for change in hunk.get('changes', []):
                        if change['type'] == 'addition':
                            changes_text.append(f"+ {change['content']} (line {change.get('line_number', '?')})")
                        elif change['type'] == 'deletion':
                            changes_text.append(f"- {change['content']}")
                
                if changes_text:
                    # Limit to 100 lines per file to avoid token limits
                    file_changes_str = "\n".join(changes_text[:100])
                    file_section = f"\n\n=== File {idx + 1}: {file_path} (Language: {file_language}) ===\n{file_changes_str}"
                    all_files_text.append(file_section)
            
            if not all_files_text:
                return {"logic_comments": []}
            
            # Combine all files into one prompt
            combined_changes = "\n".join(all_files_text)
            primary_language = state.language or "unknown"
            
            user_prompt = f"""Review these code changes (may include multiple files):

{combined_changes}

Primary Language: {primary_language}
Context: {state.context or 'No additional context'}

IMPORTANT: For each issue, include the correct file_path from changes above."""
            
            # Call LLM via gateway
            result = await self.gateway.call_llm(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                agent_name="logic_reviewer"
            )
            
            if not result["success"]:
                logger.error(f"Logic review LLM call failed: {result['error']}")
                return {"logic_comments": []}
            
            # Parse JSON response
            comments = []
            try:
                content = result["content"].strip()
                
                # Remove markdown code blocks if present
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
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
                            ReviewCategory.LOGIC,
                            "warning",
                            "logic_reviewer",
                        )
                    )
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse logic review response: {e}")
            except Exception as e:
                logger.error(f"Error processing logic review response: {e}")
            
            logger.info(f"Logic review found {len(comments)} issues")
            return {"logic_comments": comments}
            
        except Exception as e:
            logger.error(f"Error in logic review: {str(e)}", exc_info=True)
            return {"logic_comments": []}


# Create singleton instance
logic_reviewer = LogicReviewerAgent()


async def review_logic(state: AgentState) -> dict:
    """LangGraph node function for logic review."""
    return await logic_reviewer.review_logic(state)
