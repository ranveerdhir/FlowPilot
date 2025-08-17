from pydantic_settings import BaseSettings, SettingsConfigDict

"""
Centralized configuration management for the application.

Uses Pydantic Settings to:
1. Load environment variables from .env file
2. Validate required settings (e.g., API keys)
3. Provide type-safe access to configuration
4. Protect sensitive data (like API keys) from accidental exposure

Example usage:
    from config.settings import settings
    api_key = settings.llm_api_key
"""
class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    
    llm_api_key: str

settings = Settings()