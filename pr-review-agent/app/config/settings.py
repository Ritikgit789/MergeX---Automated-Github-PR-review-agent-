"""Configuration settings for the PR Review Agent."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    environment: str = "development"
    
    # API Keys
    google_api_key: str
    github_token: Optional[str] = None
    
    # Application
    app_name: str = "PR Review Agent"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Gemini Model Configuration
    gemini_model: str = "gemini-1.5-flash"
    gemini_temperature: float = 0.3
    gemini_max_tokens: int = 2048
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
