#!/usr/bin/env python3
"""
Package initialization for your_application
This creates the package structure that Render is looking for
"""

# Import the FastAPI app from the root app.py
from app import app

# For WSGI compatibility, expose the app
# This is what Gunicorn will look for
application = app
