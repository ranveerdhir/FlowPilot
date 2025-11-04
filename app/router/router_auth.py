# app/router/router_auth.py
import os
import json
import sqlite3
from fastapi import APIRouter, Request, HTTPException
from starlette.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# --- Configuration ---
# You would typically load this from a config file or environment variables
# For simplicity here, we read them directly. Ensure they are in your .env file.
from dotenv import load_dotenv
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8000/api/auth/callback" # Must match Google Cloud Console
SCOPES = ['https://www.googleapis.com/auth/calendar']
DATABASE_FILE = "flowpilot.db"

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.get("/init")
def auth_init(request: Request):
    """Generates a Google OAuth URL and redirects the user."""
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    
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
    session_state = request.session.pop("state", None)
    if not session_state or session_state != state:
        raise HTTPException(status_code=400, detail="State mismatch")

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    flow.fetch_token(code=code)
    creds = flow.credentials

    # Get user info from Google
    from googleapiclient.discovery import build
    user_info_service = build('oauth2', 'v2', credentials=creds)
    user_info = user_info_service.userinfo().get().execute()
    
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
    
    return RedirectResponse(url="/docs") # Redirect to docs page on success