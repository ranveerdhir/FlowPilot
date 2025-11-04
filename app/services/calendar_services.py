
# calender_services.py

import os.path
import datetime
import sqlite3
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastapi import Request, HTTPException

# If modifying these scopes, delete the token.json file.
SCOPES = ['https://www.googleapis.com/auth/calendar']
DATABASE_FILE = "flowpilot.db"

def authenticate_google_calendar(request: Request):
    """
    Retrieves Google OAuth credentials for the currently logged-in user from the session and database.
    Raises HTTPException if not authenticated or credentials missing.
    """
    user_email = request.session.get("user_email")
    if not user_email:
        raise HTTPException(status_code=401, detail="User not authenticated")
    con = sqlite3.connect(DATABASE_FILE)
    cur = con.cursor()
    cur.execute("SELECT token_json FROM user_credentials WHERE user_email = ?", (user_email,))
    row = cur.fetchone()
    con.close()
    if not row:
        raise HTTPException(status_code=403, detail="No credentials found for user")
    token_json = row[0]
    creds = Credentials.from_authorized_user_info(json.loads(token_json))
    return creds

class GoogleCalendarService:
    def __init__(self, credentials):
        """Initialize the service object."""
        self.service = build('calendar', 'v3', credentials=credentials)

    def get_upcoming_events(self, max_results=10):
        """Fetches upcoming events from the user's primary calendar.

        Returns a list of event dicts. On error returns an empty list.
        """
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
        except HttpError as e:
            # API-specific error (e.g., auth, quota). Log and return empty list.
            print(f"Google API error in get_upcoming_events: {e}")
            return []
        except Exception as e:
            # Network/other unexpected error
            print(f"Unexpected error in get_upcoming_events: {e}")
            return []

        return events_result.get('items', [])

    def create_event(self, summary, start_time, end_time, description=None, location=None):
        """Creates a new event on the user's primary calendar."""
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': f"{start_time}",
                'timeZone': 'America/Vancouver',
            },
            'end': {
                'dateTime': f"{end_time}",
                'timeZone': 'America/Vancouver',
            },
        }

        try:
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
        except HttpError as e:
            # API-specific error (e.g., auth, quota). Log and return None.
            print(f"Google API error in create_event: {e}")
            return None
        except Exception as e:
            # Network/other unexpected error
            print(f"Unexpected error in create_event: {e}")
            return None

        print(f"Event created: {created_event.get('htmlLink')}")
        return created_event