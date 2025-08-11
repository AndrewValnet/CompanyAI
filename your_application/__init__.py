#!/usr/bin/env python3
"""
Package initialization for your_application
This creates the package structure that Render is looking for
"""

import sys
import os

# Add the CompanyAI directory to the Python path
companyai_path = os.path.join(os.path.dirname(__file__), '..', 'CompanyAI')
sys.path.insert(0, companyai_path)

try:
    # Import the FastAPI app
    from gpt_api_endpoints import app
    
    # For ASGI compatibility, expose the FastAPI app directly
    # Uvicorn will handle this natively
    application = app
    
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Available files in CompanyAI: {os.listdir(companyai_path) if os.path.exists(companyai_path) else 'Directory not found'}")
    raise
except Exception as e:
    print(f"Unexpected error: {e}")
    raise
