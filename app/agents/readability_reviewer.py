"""Readability reviewer agent - checks code readability and style."""
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.config.settings import settings
from app.models.schemas import AgentState, ReviewComment, ReviewSeverity, ReviewCategory
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


class ReadabilityReviewerAgent:
    """Agent responsible for reviewing code readability and style."""
    
    def __init__(self):
        """Initialize Gemini LLM."""
        self._llm = None
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert code reviewer specializing in code readability and maintainability.
Review the provided code changes and identify:
- Poor naming conventions (unclear variable/function names)
- Missing or inadequate documentation/comments
- Overly complex functions (too long, too many responsibilities)
- Code duplication
- Inconsistent formatting or style
- Magic numbers or hardcoded values
- Unclear control flow
- Missing type hints (for typed languages)
- Poor error messages

Return your findings as a JSON array of objects with this structure:
[
  {{
    "file_path": "path/to/file",
    "line_number": 42,
    "severity": "warning|info",
    "message": "Clear description of the readability issue",
    "suggestion": "How to improve it"
  }}
]

If no issues found, return an empty array: []
Focus on maintainability and developer experience."""),
            ("human", """Review these code changes for readability and style (may include multiple files):

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
    
    async def review_readability(self, state: AgentState) -> dict:
        """
        Review code for readability issues - batches all files in a single LLM call.
        
        Args:
            state: Current agent state with parsed_changes
            
        Returns:
            dict: Update for readability_comments
        """
        if not state.parsed_changes:
            logger.warning("No parsed changes available for readability review")
            return {"readability_comments": []}
        
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
                    # Limit each file to 100 lines to avoid token limits
                    file_changes_str = "\n".join(changes_text[:100])
                    file_section = f"\n\n=== File {idx + 1}: {file_path} (Language: {file_language}) ===\n{file_changes_str}"
                    all_files_text.append(file_section)
            
            if not all_files_text:
                return {"readability_comments": []}
            
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
                logger.error(f"LLM call timed out after {settings.llm_api_timeout} seconds in readability review")
                return {"readability_comments": []}
            except Exception as e:
                logger.error(f"LLM call failed in readability review: {str(e)}")
                return {"readability_comments": []}
            
            # Parse JSON response
            comments = []
            try:
                content = response.content.strip()
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                issues = json.loads(content)
                
                for issue in issues:
                    issue_file_path = issue.get('file_path', 'unknown')
                    comments.append(ReviewComment(
                        file_path=issue_file_path,
                        line_number=issue.get('line_number'),
                        severity=ReviewSeverity(issue.get('severity', 'info')),
                        category=ReviewCategory.READABILITY,
                        message=issue.get('message', ''),
                        suggestion=issue.get('suggestion'),
                        source_agent="readability_reviewer"
                    ))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response: {e}. Response: {response.content[:200]}")
            
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
