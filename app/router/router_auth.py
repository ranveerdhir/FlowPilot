# app/router/router_auth.py
import os
import json
import sqlite3
from fastapi import APIRouter, Request, HTTPException
import logging
from starlette.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from app.config.config import settings
from app.services.google_oauth import get_google_flow, OAuthConfigError

# --- Configuration ---
# You would typically load this from a config file or environment variables
# For simplicity here, we read them directly. Ensure they are in your .env file.
from dotenv import load_dotenv
load_dotenv()
REDIRECT_URI = "http://127.0.0.1:8000/api/auth/callback" # Must match Google Cloud Console
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]
DATABASE_FILE = "flowpilot.db"

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.get("/init")
def auth_init(request: Request):
    """Generates a Google OAuth URL and redirects the user."""
    try:
        flow = get_google_flow()
    except OAuthConfigError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    
    request.session["state"] = state
    return RedirectResponse(authorization_url)


@router.get("/callback")
def auth_callback(request: Request, code: str, state: str):
    """Handles the OAuth callback from Google."""
    logger = logging.getLogger("router_auth")
    logger.debug(f"Callback called with code={code}, state={state}")
    session_state = request.session.pop("state", None)
    logger.debug(f"Session state: {session_state}")
    if not session_state or session_state != state:
        logger.warning("State mismatch error")
        raise HTTPException(status_code=400, detail="State mismatch")

    try:
        flow = get_google_flow()
    except OAuthConfigError as e:
        raise HTTPException(status_code=500, detail=str(e))

    flow.fetch_token(code=code)
    creds = flow.credentials
    logger.debug(f"Fetched credentials: scopes={creds.scopes}")

    # Get user info from Google
    from googleapiclient.discovery import build
    user_info_service = build('oauth2', 'v2', credentials=creds)
    try:
        user_info = user_info_service.userinfo().get().execute()
        logger.info(f"User info fetched for {user_info.get('email')}")
    except Exception as e:
        logger.exception(f"Error fetching user info: {e}")
        raise HTTPException(status_code=500, detail=f"Google userinfo error: {e}")

    user_email = user_info['email']
    user_name = user_info.get('name', '')

    # Save credentials to DB
    con = sqlite3.connect(DATABASE_FILE)
    cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO users (email, full_name) VALUES (?, ?)", (user_email, user_name))
    cur.execute("INSERT OR REPLACE INTO user_credentials (user_email, token_json) VALUES (?, ?)", (user_email, creds.to_json()))
    con.commit()
    con.close()
    
    # Store user email in session to "log them in"
    request.session["user_email"] = user_email
    logger.info(f"User {user_email} logged in and credentials saved.")

    return RedirectResponse(url="/docs") # Redirect to docs page on success