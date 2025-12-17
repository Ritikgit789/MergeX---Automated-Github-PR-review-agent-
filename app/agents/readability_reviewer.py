"""Readability reviewer agent - checks code readability and style."""
from typing import Dict
from app.config.settings import settings
from app.models.schemas import AgentState, ReviewComment, ReviewSeverity, ReviewCategory
from app.services.llm_gateway import get_llm_gateway
import logging
import json

logger = logging.getLogger(__name__)


class ReadabilityReviewerAgent:
    """Agent responsible for reviewing code readability and style."""
    
    def __init__(self):
        """Initialize the readability reviewer."""
        self.gateway = get_llm_gateway()
        
        # Ultra-strict: ONLY obvious style issues
        self.system_prompt = """Expert readability reviewer. ONLY REPORT OBVIOUS ISSUES:

REPORT ONLY IF YOU SEE:
- Single letter variables (outside loops): x = get_user_data()
- Magic numbers: sleep(86400) instead of SECONDS_PER_DAY
- Extreme duplication (exact same block 3+ times)

NEVER REPORT:
- Good variable names (result, data, payload, config are FINE)
- "Could be more descriptive" (subjective)
- "Add comments" (generic)
- "Function too long" (you don't see full function)

MANDATORY:
- Quote the problematic code
- Be 100% certain it's bad

Return JSON (EMPTY if code is reasonable):
[
  {
    "file_path": "path/to/file",
    "line_number": 42,
    "severity": "info",
    "message": "Style issue: [quote code]",
    "suggestion": "Improvement"
  }
]

When in doubt, return []."""
    
    async def review_readability(self, state: AgentState) -> dict:
        """
        Review code for readability issues.
        
        Args:
            state: Current agent state with parsed_changes
            
        Returns:
            dict: Update for readability_comments
        """
        if not state.parsed_changes:
            logger.warning("No parsed changes available for readability review")
            return {"readability_comments": []}
        
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
                return {"readability_comments": []}
            
            combined_changes = "\n".join(all_files_text)
            primary_language = state.language or "unknown"
            
            user_prompt = f"""Review for readability and style (multiple files):

{combined_changes}

Primary Language: {primary_language}
Context: {state.context or 'No additional context'}

IMPORTANT: Include correct file_path for each issue."""
            
            # Call LLM via gateway
            result = await self.gateway.call_llm(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                agent_name="readability_reviewer"
            )
            
            if not result["success"]:
                logger.error(f"Readability review LLM call failed: {result['error']}")
                return {"readability_comments": []}
            
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
                    comments.append(ReviewComment(
                        file_path=issue.get('file_path', 'unknown'),
                        line_number=issue.get('line_number'),
                        severity=ReviewSeverity(issue.get('severity', 'info')),
                        category=ReviewCategory.READABILITY,
                        message=issue.get('message', ''),
                        suggestion=issue.get('suggestion'),
                        source_agent="readability_reviewer"
                    ))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse readability review response: {e}")
            except Exception as e:
                logger.error(f"Error processing readability review response: {e}")
            
            logger.info(f"Readability review found {len(comments)} issues")
            return {"readability_comments": comments}
            
        except Exception as e:
            logger.error(f"Error in readability review: {str(e)}", exc_info=True)
            return {"readability_comments": []}


# Create singleton instance
readability_reviewer = ReadabilityReviewerAgent()


async def review_readability(state: AgentState) -> dict:
    """LangGraph node function for readability review."""
    return await readability_reviewer.review_readability(state)
