#!/usr/bin/env python3
"""
WSGI entry point for Render deployment
This is what Render is looking for: your_application.wsgi
"""

# Import from the local package
from . import application

# This is what Gunicorn expects
# The application variable should be available for Gunicorn to find
