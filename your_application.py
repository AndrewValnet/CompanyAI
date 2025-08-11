#!/usr/bin/env python3
"""
This is the file Render is looking for: your_application.py
Render is hardcoded to run 'gunicorn your_application.wsgi'
So we'll give it exactly what it wants.
"""

import sys
import os

# Add the CompanyAI directory to the Python path
companyai_path = os.path.join(os.path.dirname(__file__), 'CompanyAI')
sys.path.insert(0, companyai_path)

try:
    # Import the FastAPI app
    from gpt_api_endpoints import app
    
    # For WSGI compatibility, we need to expose the app
    # This is what Gunicorn will look for
    application = app
    
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
