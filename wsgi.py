#!/usr/bin/env python3
"""
WSGI entry point for Render deployment
This is what Render is looking for: your_application.wsgi
"""

import sys
import os

# Debug: Print current working directory and Python path
print(f"WSGI: Current working directory: {os.getcwd()}")
print(f"WSGI: Python path: {sys.path}")
print(f"WSGI: Available files: {os.listdir('.')}")

try:
    # Import the application from your_application.py
    print("WSGI: Attempting to import application from your_application...")
    from your_application import application
    print("WSGI: Successfully imported application")
    
except ImportError as e:
    print(f"WSGI: Import error: {e}")
    raise
except Exception as e:
    print(f"WSGI: Unexpected error: {e}")
    raise

# This is what Gunicorn expects
# The application variable should be available for Gunicorn to find
print("WSGI: Application object available:", application)
