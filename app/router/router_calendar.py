from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.calendar_services import GoogleCalendarService, authenticate_google_calendar

router =  APIRouter(tags = ["Calendar"]) # calender is the tag for this router instance helps me navigate

#pydantic model to define the request body structure

class EventCreate(BaseModel):
    summary: str
    start_time: str #Expected format: '2025-09-20T10:00:00'
    end_time: str   # Expected format: '2025-09-20T11:00:000'
    description: Optional[str] = None
    location: Optional[str] = None

@router.get("/events")
# In app/router/router_calendar.py

@router.get("/events")
def read_events():
    """
    Authenticates with Google Calendar and fetches upcoming events.
    """
    print("--- /events GET endpoint was hit! ---")
    creds = authenticate_google_calendar()
    print("--- Authentication finished, have credentials. ---")

    calendar_service = GoogleCalendarService(creds)
    
    # 1. Get the LIST of events, so the variable is PLURAL: 'events'
    events = calendar_service.get_upcoming_events(max_results=5)

    # 2. Check the PLURAL 'events' list
    if not events:
        return {'message': 'No upcoming events found.'}
    else:
        event_list = []
        # 3. Loop through the PLURAL 'events' list, getting one SINGULAR 'event' at a time
        for event in events:
            # 4. Inside the loop, use the SINGULAR 'event'
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list.append({'summary': event['summary'], 'start': start})
        return {"events": event_list}
# -- new endpoint for creating events --
@router.post("/events", status_code = 201)
def create_new_event(event_data: EventCreate):
    """
    Create a new event in google calender
    """
    print( "--/ events POST Endpoint was hit! --")
    creds = authenticate_google_calendar()
    print("--Athentication finished, have credentials. --")

    calendar_service = GoogleCalendarService(creds)

    created_event = calendar_service.create_event(
        summary=event_data.summary,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        description=event_data.description,
        location=event_data.location

    )
    return {"message": "Event created successfully!", "event_link": created_event.get('htmlLink')}