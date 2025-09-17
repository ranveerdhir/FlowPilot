# In app/main.py

from fastapi import FastAPI, APIRouter
# This import path correctly finds the file inside app/services/
from app.services.calender_services import GoogleCalendarService, authenticate_google_calendar

app = FastAPI()
router = APIRouter()

@router.get("/events")
def read_events():
    """
    Authenticates with Google Calendar and fetches upcoming events.
    """
    print("--- /events endpoint was hit! ---")
    creds = authenticate_google_calendar()
    print("--- Authentication finished, have credentials. ---")
    
    calendar_service = GoogleCalendarService(creds)
    events = calendar_service.get_upcoming_events(max_results=5)

    if not events:
        return {'message': 'No upcoming events found.'}
    else:
        # Returning a cleaner list of events
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list.append({'summary': event['summary'], 'start': start})
        return {"events": event_list}

# Include the router in the main app
app.include_router(router)