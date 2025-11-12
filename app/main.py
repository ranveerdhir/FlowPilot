# app/main.py

import os
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.config.config import settings
from dotenv import load_dotenv
from app import logging_config  # Initialize logging early

# Load environment variables from .env file
load_dotenv()

# Initialize the database tables
from app.database import init_db
init_db()

# Import your routers
from app.router import router_calendar
from app.router import router_auth

app = FastAPI(title="Flowpilot")

# Add SessionMiddleware to handle user sessions
# This requires a secret key, which you should load from your environment
app.add_middleware(
    SessionMiddleware,
    secret_key=(settings.session_secret or settings.google_client_secret)
)

# Include your new authentication router
app.include_router(router_auth.router)

# Include your existing calendar router
app.include_router(router_calendar.router)