"""
VeriSight Configuration
Environment-based configuration for production deployment
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))

# API Configuration
API_PREFIX = os.getenv("API_PREFIX", "/api")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
# In production, restrict to specific origins (extension IDs, domain names)
# Example: "chrome-extension://abc123...,https://yourdomain.com"

# Database Configuration
DB_PATH = os.getenv("DB_PATH", "brands.db.json")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", None)  # None = stdout, or path to log file

# Security Configuration
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "").split(",")
# Comma-separated list of allowed extension IDs for production

# Rate Limiting (future feature)
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

# Google Safe Browsing API Configuration
GOOGLE_SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", None)
# Get your API key from: https://console.cloud.google.com/apis/credentials
# Enable "Safe Browsing API" in Google Cloud Console

def get_cors_origins() -> List[str]:
    """Get CORS origins based on environment"""
    if ENVIRONMENT == "production" and CORS_ORIGINS == ["*"]:
        # In production, warn if CORS is wide open
        import warnings
        warnings.warn(
            "CORS_ORIGINS is set to '*' in production. "
            "Consider restricting to specific origins for security.",
            UserWarning
        )
    return CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"]
