"""Readability reviewer agent - checks code readability and style."""
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.config import settings
from app.models import AgentState, ReviewComment, ReviewSeverity, ReviewCategory
import logging
import json

logger = logging.getLogger(__name__)


class ReadabilityReviewerAgent:
    """Agent responsible for reviewing code readability and style."""
    
    def __init__(self):
        """Initialize Gemini LLM."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=settings.gemini_temperature,
            max_output_tokens=settings.gemini_max_tokens,
            google_api_key=settings.google_api_key
        )
        
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
            ("human", """Review these code changes for readability and style:

File: {file_path}

Changes:
{changes}

Language: {language}
Context: {context}""")
        ])
    
    def review_readability(self, state: AgentState) -> AgentState:
        """
        Review code for readability issues.
        
        Args:
            state: Current agent state with parsed_changes
            
        Returns:
            Updated state with readability_comments
        """
        if not state.parsed_changes:
            logger.warning("No parsed changes available for readability review")
            return state
        
        try:
            comments = []
            
            for file_change in state.parsed_changes:
                file_path = file_change.get('file_path', 'unknown')
                
                # Build changes text
                changes_text = []
                for hunk in file_change.get('hunks', []):
                    for change in hunk.get('changes', []):
                        if change['type'] == 'addition':
                            changes_text.append(f"+ {change['content']} (line {change.get('line_number', '?')})")
                        elif change['type'] == 'deletion':
                            changes_text.append(f"- {change['content']}")
                
                if not changes_text:
                    continue
                
                changes_str = "\n".join(changes_text[:50])
                
                # Call LLM
                chain = self.prompt | self.llm
                response = chain.invoke({
                    "file_path": file_path,
                    "changes": changes_str,
                    "language": state.language or "unknown",
                    "context": state.context or "No additional context"
                })
                
                # Parse JSON response
                try:
                    content = response.content.strip()
                    if content.startswith('```'):
                        content = content.split('```')[1]
                        if content.startswith('json'):
                            content = content[4:]
                    content = content.strip()
                    
                    issues = json.loads(content)
                    
                    for issue in issues:
                        comments.append(ReviewComment(
                            file_path=issue.get('file_path', file_path),
                            line_number=issue.get('line_number'),
                            severity=ReviewSeverity(issue.get('severity', 'info')),
                            category=ReviewCategory.READABILITY,
                            message=issue.get('message', ''),
                            suggestion=issue.get('suggestion')
                        ))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM response for {file_path}: {e}")
            
            state.readability_comments = comments
            logger.info(f"Readability review found {len(comments)} issues")
            
        except Exception as e:
            logger.error(f"Error in readability review: {str(e)}")
        
        return state


# Create singleton instance
readability_reviewer = ReadabilityReviewerAgent()


def review_readability(state: AgentState) -> AgentState:
    """LangGraph node function for readability review."""
    return readability_reviewer.review_readability(state)
