#!/usr/bin/env python3
"""
WSGI entry point for Render deployment
This file is what Render is looking for when it runs 'gunicorn your_application.wsgi'
"""

import sys
import os

# Add the CompanyAI directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CompanyAI'))

# Import the FastAPI app
from gpt_api_endpoints import app

# For WSGI compatibility, we need to expose the app
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
