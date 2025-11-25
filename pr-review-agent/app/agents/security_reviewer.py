"""Security reviewer agent - identifies security vulnerabilities."""
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.config import settings
from app.models import AgentState, ReviewComment, ReviewSeverity, ReviewCategory
import logging
import json

logger = logging.getLogger(__name__)


class SecurityReviewerAgent:
    """Agent responsible for reviewing security vulnerabilities."""
    
    def __init__(self):
        """Initialize Gemini LLM."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=settings.gemini_temperature,
            max_output_tokens=settings.gemini_max_tokens,
            google_api_key=settings.google_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert security code reviewer.
Review the provided code changes and identify security vulnerabilities:
- SQL injection risks
- Cross-site scripting (XSS)
- Cross-site request forgery (CSRF)
- Hardcoded secrets, passwords, or API keys
- Insecure authentication/authorization
- Insecure cryptography
- Path traversal vulnerabilities
- Command injection
- Insecure dependencies
- Sensitive data exposure

Return your findings as a JSON array of objects with this structure:
[
  {{
    "file_path": "path/to/file",
    "line_number": 42,
    "severity": "critical|error|warning",
    "message": "Clear description of the security issue",
    "suggestion": "How to fix it securely"
  }}
]

If no issues found, return an empty array: []
Be specific about the vulnerability type and impact."""),
            ("human", """Review these code changes for security issues:

File: {file_path}

Changes:
{changes}

Language: {language}
Context: {context}""")
        ])
    
    def review_security(self, state: AgentState) -> AgentState:
        """
        Review code for security vulnerabilities.
        
        Args:
            state: Current agent state with parsed_changes
            
        Returns:
            Updated state with security_comments
        """
        if not state.parsed_changes:
            logger.warning("No parsed changes available for security review")
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
                            category=ReviewCategory.SECURITY,
                            message=issue.get('message', ''),
                            suggestion=issue.get('suggestion')
                        ))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM response for {file_path}: {e}")
            
            state.security_comments = comments
            logger.info(f"Security review found {len(comments)} issues")
            
        except Exception as e:
            logger.error(f"Error in security review: {str(e)}")
        
        return state


# Create singleton instance
security_reviewer = SecurityReviewerAgent()


def review_security(state: AgentState) -> AgentState:
    """LangGraph node function for security review."""
    return security_reviewer.review_security(state)
