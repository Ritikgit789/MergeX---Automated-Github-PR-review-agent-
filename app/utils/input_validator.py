"""Input validator for detecting greetings and irrelevant queries."""
import re
from typing import Dict, Optional
from enum import Enum


class InputType(str, Enum):
    """Types of user input."""
    GREETING = "greeting"
    IRRELEVANT = "irrelevant"
    INVALID_URL = "invalid_url"
    VALID_PR_URL = "valid_pr_url"


class InputValidator:
    """Validates user input and provides appropriate responses."""
    
    # Greeting patterns
    GREETING_PATTERNS = [
        r'^hi+$',
        r'^hi\s+mergeX$',
        r'^hello+$',
        r'^hello\s+mergeX$',
        r'^hey+$',
        r'^hi\s+there$',
        r'^hello\s+there$',
        r'^hey\s+there$',
        r'^greetings?$',
        r'^good\s+(morning|afternoon|evening|day)$',
        r'^howdy$',
        r'^sup$',
        r'^what\'?s\s+up$',
    ]
    
    # GitHub PR URL pattern
    GITHUB_PR_PATTERN = r'https?://github\.com/[\w\-\.]+/[\w\-\.]+/pull/\d+'
    
    # Keywords that indicate irrelevant queries
    IRRELEVANT_KEYWORDS = [
        'what is', 'how to', 'tell me', 'explain', 'tutorial',
        'teach me', 'help me learn', 'joke', 'story', 'weather',
        'time', 'date', 'calculate', 'translate', 'define',
        'meaning of', 'who is', 'where is', 'when is', 'why is',
    ]
    
    def __init__(self):
        """Initialize validator with compiled patterns."""
        self.greeting_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.GREETING_PATTERNS]
        self.github_pr_regex = re.compile(self.GITHUB_PR_PATTERN, re.IGNORECASE)
    
    def validate(self, user_input: str) -> Dict[str, any]:
        """
        Validate user input and determine its type.
        
        Args:
            user_input: Raw user input string
            
        Returns:
            Dict with 'type', 'is_valid', 'message', and optional 'url'
        """
        if not user_input or not user_input.strip():
            return {
                "type": InputType.INVALID_URL,
                "is_valid": False,
                "message": "Please provide a GitHub PR URL to review."
            }
        
        user_input = user_input.strip()
        
        # Check for greetings
        if self._is_greeting(user_input):
            return {
                "type": InputType.GREETING,
                "is_valid": False,
                "message": "Hi! How can I help you? Please provide your GitHub PR link, let's check and solve any issues together! 🚀"
            }
        
        # Check for valid GitHub PR URL
        if self._is_valid_github_pr_url(user_input):
            return {
                "type": InputType.VALID_PR_URL,
                "is_valid": True,
                "url": user_input,
                "message": "Valid GitHub PR URL"
            }
        
        # Check for irrelevant queries
        if self._is_irrelevant_query(user_input):
            return {
                "type": InputType.IRRELEVANT,
                "is_valid": False,
                "message": "Sorry, I am a GitHub PR review agent. I don't handle general questions or unrelated topics. Please provide a GitHub Pull Request URL for me to review. Example: https://github.com/owner/repo/pull/123"
            }
        
        # If it's not a greeting, not irrelevant, but also not a valid URL
        return {
            "type": InputType.INVALID_URL,
            "is_valid": False,
            "message": "Invalid GitHub PR URL format. Please provide a valid URL like: https://github.com/owner/repo/pull/123"
        }
    
    def _is_greeting(self, text: str) -> bool:
        """Check if input is a greeting."""
        text_lower = text.lower().strip()
        
        # Check against greeting patterns
        for pattern in self.greeting_regex:
            if pattern.match(text_lower):
                return True
        
        return False
    
    def _is_valid_github_pr_url(self, text: str) -> bool:
        """Check if input is a valid GitHub PR URL."""
        return bool(self.github_pr_regex.match(text))
    
    def _is_irrelevant_query(self, text: str) -> bool:
        """Check if input is an irrelevant query."""
        text_lower = text.lower()
        
        # Check for irrelevant keywords
        for keyword in self.IRRELEVANT_KEYWORDS:
            if keyword in text_lower:
                return True
        
        # Check if it's a question but not about GitHub/PR
        if '?' in text and 'github' not in text_lower and 'pull request' not in text_lower and 'pr' not in text_lower:
            return True
        
        return False


# Singleton instance
input_validator = InputValidator()
