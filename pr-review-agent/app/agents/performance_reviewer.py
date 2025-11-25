"""Performance reviewer agent - identifies performance issues."""
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.config import settings
from app.models import AgentState, ReviewComment, ReviewSeverity, ReviewCategory
import logging
import json

logger = logging.getLogger(__name__)


class PerformanceReviewerAgent:
    """Agent responsible for reviewing performance issues."""
    
    def __init__(self):
        """Initialize Gemini LLM."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=settings.gemini_temperature,
            max_output_tokens=settings.gemini_max_tokens,
            google_api_key=settings.google_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert performance code reviewer.
Review the provided code changes and identify performance issues:
- N+1 query problems
- Inefficient loops or nested iterations
- Unnecessary database calls
- Memory leaks or excessive memory usage
- Inefficient algorithms (wrong time complexity)
- Blocking operations in async code
- Missing caching opportunities
- Redundant computations
- Large object copies
- Inefficient data structures

Return your findings as a JSON array of objects with this structure:
[
  {{
    "file_path": "path/to/file",
    "line_number": 42,
    "severity": "error|warning|info",
    "message": "Clear description of the performance issue",
    "suggestion": "How to optimize it"
  }}
]

If no issues found, return an empty array: []
Focus on significant performance impacts."""),
            ("human", """Review these code changes for performance issues:

File: {file_path}

Changes:
{changes}

Language: {language}
Context: {context}""")
        ])
    
    def review_performance(self, state: AgentState) -> AgentState:
        """
        Review code for performance issues.
        
        Args:
            state: Current agent state with parsed_changes
            
        Returns:
            Updated state with performance_comments
        """
        if not state.parsed_changes:
            logger.warning("No parsed changes available for performance review")
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
                            severity=ReviewSeverity(issue.get('severity', 'warning')),
                            category=ReviewCategory.PERFORMANCE,
                            message=issue.get('message', ''),
                            suggestion=issue.get('suggestion')
                        ))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM response for {file_path}: {e}")
            
            state.performance_comments = comments
            logger.info(f"Performance review found {len(comments)} issues")
            
        except Exception as e:
            logger.error(f"Error in performance review: {str(e)}")
        
        return state


# Create singleton instance
performance_reviewer = PerformanceReviewerAgent()


def review_performance(state: AgentState) -> AgentState:
    """LangGraph node function for performance review."""
    return performance_reviewer.review_performance(state)
