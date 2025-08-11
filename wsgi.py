#!/usr/bin/env python3
"""
WSGI entry point for Render deployment
This file is what Render is looking for when it runs 'gunicorn your_application.wsgi'
"""

import sys
import os

# Debug: Print current working directory and Python path
print(f"Current working directory: {os.getcwd()}")
print(f"Python path before: {sys.path}")

# Add the CompanyAI directory to the Python path
companyai_path = os.path.join(os.path.dirname(__file__), 'CompanyAI')
print(f"Adding CompanyAI path: {companyai_path}")
sys.path.insert(0, companyai_path)

print(f"Python path after: {sys.path}")

try:
    # Import the FastAPI app
    print("Attempting to import gpt_api_endpoints...")
    from gpt_api_endpoints import app
    print("Successfully imported gpt_api_endpoints.app")
    
    # For WSGI compatibility, we need to expose the app
    application = app
    print("WSGI application object created successfully")
    
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Available files in CompanyAI: {os.listdir(companyai_path) if os.path.exists(companyai_path) else 'Directory not found'}")
    raise
except Exception as e:
    print(f"Unexpected error: {e}")
    raise

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting uvicorn on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
