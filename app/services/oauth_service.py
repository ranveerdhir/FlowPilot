# app/services/oauth_service.py
"""OAuth helper utilities centralizing Flow construction.

Provides a single function `get_google_flow` that uses centralized settings
instead of duplicating config blocks in routers.
"""
from google_auth_oauthlib.flow import Flow
from app.config.config import settings
import json
from typing import Sequence

class OAuthConfigError(RuntimeError):
    """Raised when required OAuth configuration is missing."""


def get_google_flow(scopes: Sequence[str] | None = None, redirect_uri: str | None = None) -> Flow:
    """Create and return a configured Google OAuth Flow.

    Args:
        scopes: Optional sequence of scope strings. Defaults to settings.scopes.
        redirect_uri: Optional override for redirect URI. Defaults to settings.redirect_uri.

    Raises:
        OAuthConfigError: If required client id/secret are missing.
    """
    client_id = settings.google_client_id
    client_secret = settings.google_client_secret
    if not client_id or not client_secret:
        raise OAuthConfigError("Google OAuth client id/secret missing. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")

    used_scopes = list(scopes) if scopes else settings.scopes
    used_redirect = redirect_uri or settings.redirect_uri

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [used_redirect],
            }
        },
        scopes=used_scopes,
        redirect_uri=used_redirect,
    )
    return flow
