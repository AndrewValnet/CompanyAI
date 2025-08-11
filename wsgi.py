#!/usr/bin/env python3
"""
WSGI entry point for Render deployment
This is what Render is looking for: your_application.wsgi
"""

# Import the application from your_application.py
from your_application import application

# This is what Gunicorn expects
# The application variable should be available for Gunicorn to find
