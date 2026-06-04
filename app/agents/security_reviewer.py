"""Security reviewer agent - identifies security vulnerabilities."""
from typing import Dict
from app.config.settings import settings
from app.models.schemas import AgentState, ReviewComment, ReviewSeverity, ReviewCategory
from app.services.llm_gateway import get_llm_gateway
from app.utils.comment_format import CLEAR_COMMENT_RULES, build_review_comment
import logging
import json

logger = logging.getLogger(__name__)


class SecurityReviewerAgent:
    """Agent responsible for reviewing security vulnerabilities."""
    
    def __init__(self):
        """Initialize the security reviewer."""
        self.gateway = get_llm_gateway()
        
        # Ultra-strict: ONLY visible vulnerabilities
        self.system_prompt = """Expert security reviewer. ONLY REPORT VISIBLE VULNERABILITIES:

REPORT ONLY IF YOU SEE:
- Hardcoded password/key: password = "admin123"
- SQL concatenation: "SELECT * WHERE id=" + user_input  
- eval/exec with user data
- subprocess with shell=True

NEVER REPORT:
- "Potential" anything
- "May have" security issue
- "Should validate" (you don't know if it's validated elsewhere)
- Generic "review for security"

MANDATORY:
- Be 100% certain
- Explain risk in plain English

""" + CLEAR_COMMENT_RULES + """

Return JSON (EMPTY if no PROVEN vulnerabilities):
[
  {
    "file_path": "path/to/file",
    "line_number": 42,
    "severity": "critical",
    "message": "Problem: ... Impact: ... Code: ...",
    "suggestion": "Fix: ..."
  }
]

When in doubt, return []. False positives destroy trust."""
    
    async def review_security(self, state: AgentState) -> dict:
        """
        Review code for security vulnerabilities.
        
        Args:
            state: Current agent state with parsed_changes
            
        Returns:
            dict: Update for security_comments
        """
        if not state.parsed_changes:
            logger.warning("No parsed changes available for security review")
            return {"security_comments": []}
        
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
                return {"security_comments": []}
            
            combined_changes = "\n".join(all_files_text)
            primary_language = state.language or "unknown"
            
            user_prompt = f"""Review for security issues (multiple files):

{combined_changes}

Primary Language: {primary_language}
Context: {state.context or 'No additional context'}

IMPORTANT: Include correct file_path for each issue."""
            
            # Call LLM via gateway
            result = await self.gateway.call_llm(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                agent_name="security_reviewer"
            )
            
            if not result["success"]:
                logger.error(f"Security review LLM call failed: {result['error']}")
                return {"security_comments": []}
            
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
                    # Skip if issue is not a dict (malformed response)
                    if not isinstance(issue, dict):
                        logger.warning(f"Skipping malformed issue (not a dict): {issue}")
                        continue
                    
                    comments.append(
                        build_review_comment(
                            issue,
                            ReviewCategory.SECURITY,
                            "warning",
                            "security_reviewer",
                        )
                    )
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse security review response: {e}")
            except Exception as e:
                logger.error(f"Error processing security review response: {e}")
            
            logger.info(f"Security review found {len(comments)} issues")
            return {"security_comments": comments}
            
        except Exception as e:
            logger.error(f"Error in security review: {str(e)}", exc_info=True)
            return {"security_comments": []}


# Create singleton instance
security_reviewer = SecurityReviewerAgent()


async def review_security(state: AgentState) -> dict:
    """LangGraph node function for security review."""
    return await security_reviewer.review_security(state)
