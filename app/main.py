# In app/main.py

from fastapi import FastAPI, APIRouter
# This import path correctly finds the file inside app/services/
from .router import router_calendar

app = FastAPI(title = "Flowpilot")

app.include_router(router_calendar.router)