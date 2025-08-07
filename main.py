from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.auth import auth_router
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:3001",  # Alternative port
        # Add production domains here
    ],
    allow_credentials=True,  # Required for session cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use JWT_SECRET from .env for session encryption
SESSION_SECRET = os.getenv("JWT_SECRET", "super-secret-session-key")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

app.include_router(auth_router)
