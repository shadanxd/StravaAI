from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.auth_routes import auth_router
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="StravaAI API",
    description="AI-powered Strava analytics and insights",
    version="1.0.0"
)

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

# Include authentication routes
app.include_router(auth_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StravaAI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
