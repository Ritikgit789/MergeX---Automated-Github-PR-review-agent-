"""Logic reviewer agent - identifies logical errors and edge cases."""
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.config.settings import settings
from app.models.schemas import AgentState, ReviewComment, ReviewSeverity, ReviewCategory
import logging
import json

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
            ("human", """Review these code changes:

File: {file_path}

Changes:
{changes}

Language: {language}
Context: {context}""")
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
    
    def review_logic(self, state: AgentState) -> dict:
        """
        Review code for logical issues.
        
        Args:
            state: Current agent state with parsed_changes
            
        Returns:
            dict: Update for logic_comments
        """
        if not state.parsed_changes:
            logger.warning("No parsed changes available for logic review")
            return {"logic_comments": []}
        
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
                
                changes_str = "\n".join(changes_text[:50])  # Limit to avoid token limits
                
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
                    # Remove markdown code blocks if present
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
                            category=ReviewCategory.LOGIC,
                            message=issue.get('message', ''),
                            suggestion=issue.get('suggestion'),
                            source_agent="logic_reviewer"
                        ))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM response for {file_path}: {e}")
            
            logger.info(f"Logic review found {len(comments)} issues")
            return {"logic_comments": comments}
            
        except Exception as e:
            logger.error(f"Error in logic review: {str(e)}")
            return {"logic_comments": []}


# Create singleton instance
logic_reviewer = LogicReviewerAgent()


def review_logic(state: AgentState) -> dict:
    """LangGraph node function for logic review."""
    return logic_reviewer.review_logic(state)
