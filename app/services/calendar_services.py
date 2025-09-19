# calender_services.py

import os.path
import datetime
from google.auth.transport.requests import Request  # <-- IMPORT THIS
from google.oauth2.credentials import Credentials  # <-- CAPITAL 'C'
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the token.json file.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    """Handles the OAuth2 authentication flow and returns the credentials object."""
    creds = None 

    # 1. Get the directory of the current script (e.g., .../app/services)
    script_dir = os.path.dirname(__file__)

    # 2. Go up two levels to get the project root directory (e.g., .../FLOWPILOT)
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    # 3. Define the full paths for your credential and token files
    creds_path = os.path.join(project_root, 'credentials.json')
    token_path = os.path.join(project_root, 'token.json')

    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'): # <-- FIX: .json
        creds = Credentials.from_authorized_user_file('token.json', SCOPES) # <-- FIX: .json and Credentials

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: # <-- FIX: expired
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds # <-- IMPORTANT: Return the credentials

class GoogleCalendarService:
    def __init__(self, credentials):
        """Initialize the service object."""
        self.service = build('calendar', 'v3', credentials=credentials) 

    def get_upcoming_events(self, max_results=10):
        """Fetches upcoming events from the user's primary calendar."""
        import datetime
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return events_result.get('items', []) 
    
    # --- create events
    def create_event( sef, summary, start_time, end_time, description = None, location = None):
    # Cereate a new even on user's Pimary calendar
        event  = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': f"{start_time}-07:00", # manually adding PDT time zone
                'timeZone': 'America/Vancouver',
            },
            'end': {
                'dateTime': f"{end_time}-07:00",
                'timeZone': 'America/Vancouver',
            },
        }

        created_event = self.service.events().insert(
            calenderId = 'primary',
            body = event
        ).execute()

        print(f"Event created: {created_event.get('htmlLink')}")
        return created_event