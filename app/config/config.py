from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import secrets

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
    """Application settings loaded from environment variables.

    Provides centralized access to configuration instead of calling os.getenv
    throughout the codebase. Each attribute below maps to an environment
    variable automatically. If an env var is missing and a default is provided
    here, that default is used.
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    # External service keys
    llm_api_key: str = Field(..., validation_alias='LLM_API_KEY')

    # Google OAuth client configuration (now required)
    google_client_id: str = Field(..., validation_alias='GOOGLE_CLIENT_ID')
    google_client_secret: str = Field(..., validation_alias='GOOGLE_CLIENT_SECRET')

    # OAuth redirect URI and scopes (overridable via env)
    redirect_uri: str = Field(
        default='http://127.0.0.1:8000/api/auth/callback',
        validation_alias='REDIRECT_URI',
    )
    scopes: list[str] = Field(
        default=[
            'https://www.googleapis.com/auth/calendar',
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
        ],
        validation_alias='GOOGLE_SCOPES',  # if provided, should be JSON array or comma-separated
    )

    # Session secret for signing cookies (Starlette SessionMiddleware).
    # If not set via env, a random one is generated. For production you should
    # set SESSION_SECRET explicitly so sessions survive restarts.
    session_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48), validation_alias='SESSION_SECRET')
    # Logging level (e.g., DEBUG, INFO, WARNING, ERROR) configurable via LOG_LEVEL
    log_level: str = Field(default='INFO', validation_alias='LOG_LEVEL')

settings = Settings()