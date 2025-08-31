"""
FastAPI Backend Configuration
Centralized configuration for URLs and CORS settings
"""
import os
from typing import List

# Default values matching globals.ts
DEFAULT_FRONTEND_URL = "http://localhost:3000"
DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"

# Environment-based configuration
def get_environment() -> str:
    """Get current environment (development, staging, production)"""
    return os.getenv("ENVIRONMENT", "development")

def is_development() -> bool:
    """Check if running in development mode"""
    return get_environment() == "development"

# Base URLs - can be overridden via environment variables
FRONTEND_URL = os.getenv("FRONTEND_URL", DEFAULT_FRONTEND_URL)
BACKEND_URL = os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL)

# Dashboard URL (used in emails and redirects)
DASHBOARD_URL = os.getenv("DASHBOARD_URL", FRONTEND_URL)

# CORS Origins - supports multiple origins separated by commas
def get_cors_origins() -> List[str]:
    """Get CORS origins from environment or defaults"""
    cors_env = os.getenv("CORS_ORIGINS")
    if cors_env:
        return [origin.strip() for origin in cors_env.split(",")]
    
    # Default CORS origins for development
    return [
        FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # For alternative dev ports
    ]

CORS_ORIGINS = get_cors_origins()

# Email configuration
EMAIL_DASHBOARD_URL = DASHBOARD_URL

# API Configuration
API_CONFIG = {
    "title": "Chevron SQ FastAPI",
    "description": "Chevron FastAPI project with RESTful capabilities.",
    "version": "0.1.0",
    "frontend_url": FRONTEND_URL,
    "backend_url": BACKEND_URL,
}

# Development/Debug settings
DEBUG = is_development()
SQL_ECHO = os.getenv("SQL_DEBUG", "false").lower() == "true" if not is_development() else True

# Export commonly used values
__all__ = [
    "FRONTEND_URL",
    "BACKEND_URL", 
    "DASHBOARD_URL",
    "CORS_ORIGINS",
    "EMAIL_DASHBOARD_URL",
    "API_CONFIG",
    "DEBUG",
    "SQL_ECHO",
] 