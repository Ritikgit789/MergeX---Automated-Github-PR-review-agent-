"""Configuration settings for the PR Review Agent."""
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    environment: str = "development"
    
    # API Keys
    google_api_key: Optional[str] = None
    github_token: Optional[str] = None
    
    # Application
    app_name: str = "PR Review Agent"
    app_version: str = "1.0.0"
    log_level: str = "INFO"  # Use DEBUG, INFO, WARNING, or ERROR (uppercase)
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Gemini Model Configuration (legacy, optional fallback)
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.3
    gemini_max_tokens: int = 2048
    
    # Groq Model Configuration (primary)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.1-8b-instant"
    groq_temperature: float = 0.3
    groq_max_tokens: int = 1800
    groq_timeout: int = 5  # Quality-focused timeout
    groq_retry_timeout: int = 2  # Faster retry on failure
    
    # Timeout Configuration (in seconds)
    github_api_timeout: int = 30
    llm_api_timeout: int = 60  # Kept for backward compatibility

    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
