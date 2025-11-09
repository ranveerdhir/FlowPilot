# app/main.py

import os
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

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
    secret_key=os.getenv("GOOGLE_CLIENT_SECRET")
)

# Include your new authentication router
app.include_router(router_auth.router)

# Include your existing calendar router
app.include_router(router_calendar.router)