"""Logic reviewer agent - identifies logical errors and edge cases."""
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.config.settings import settings
from app.models.schemas import AgentState, ReviewComment, ReviewSeverity, ReviewCategory
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


class LogicReviewerAgent:
    """Agent responsible for reviewing code logic and correctness."""
    
    def __init__(self):
        """Initialize Gemini LLM."""
        self._llm = None
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert code reviewer specializing in logic analysis.
Review the provided code changes and identify:
- Logical errors and bugs
- Edge cases not handled
- Null pointer/undefined reference issues
- Incorrect algorithms or business logic
- Off-by-one errors
- Off-by-one errors
- Race conditions or concurrency issues

Also consider the logical impact of deleted code (e.g., removing critical steps, tests, or validation logic).

Return your findings as a JSON array of objects with this structure:
[
  {{
    "file_path": "path/to/file",
    "line_number": 42,
    "severity": "error|warning|info",
    "message": "Clear description of the issue",
    "suggestion": "How to fix it"
  }}
]

If no issues found, return an empty array: []
Be concise and actionable. Focus only on logic issues."""),
            ("human", """Review these code changes (may include multiple files):

{changes}

Primary Language: {language}
Context: {context}

IMPORTANT: For each issue, make sure to include the correct file_path from the changes above.""")
        ])

    @property
    def llm(self):
        """Lazy initialization of LLM."""
        if not self._llm:
            self._llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                temperature=settings.gemini_temperature,
                max_output_tokens=settings.gemini_max_tokens,
                google_api_key=settings.google_api_key,
                response_mime_type="application/json"
            )
        return self._llm
    
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
            file_paths_map = {}  # Track which file each section belongs to
            
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
                    # Limit each file to 100 lines to avoid token limits
                    file_changes_str = "\n".join(changes_text[:100])
                    file_section = f"\n\n=== File {idx + 1}: {file_path} (Language: {file_language}) ===\n{file_changes_str}"
                    all_files_text.append(file_section)
                    file_paths_map[idx] = {
                        "file_path": file_path,
                        "language": file_language
                    }
            
            if not all_files_text:
                return {"logic_comments": []}
            
            # Combine all files into one prompt
            combined_changes = "\n".join(all_files_text)
            primary_language = state.language or "unknown"
            
            # Call LLM once for all files with timeout
            try:
                chain = self.prompt | self.llm
                response = await asyncio.wait_for(
                    chain.ainvoke({
                        "file_path": "Multiple files (see changes below)",
                        "changes": combined_changes,
                        "language": primary_language,
                        "context": state.context or "No additional context"
                    }),
                    timeout=settings.llm_api_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"LLM call timed out after {settings.llm_api_timeout} seconds in logic review")
                return {"logic_comments": []}
            except Exception as e:
                logger.error(f"LLM call failed in logic review: {str(e)}")
                return {"logic_comments": []}
            
            # Parse JSON response
            comments = []
            try:
                content = response.content.strip()
                # Remove markdown code blocks if present
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                issues = json.loads(content)
                
                for issue in issues:
                    # Use file_path from issue if provided, otherwise try to match
                    issue_file_path = issue.get('file_path', 'unknown')
                    comments.append(ReviewComment(
                        file_path=issue_file_path,
                        line_number=issue.get('line_number'),
                        severity=ReviewSeverity(issue.get('severity', 'warning')),
                        category=ReviewCategory.LOGIC,
                        message=issue.get('message', ''),
                        suggestion=issue.get('suggestion'),
                        source_agent="logic_reviewer"
                    ))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response: {e}. Response: {response.content[:200]}")
            
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
