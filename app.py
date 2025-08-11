#!/usr/bin/env python3
"""
Simple FastAPI application for Render deployment
This is the most basic setup possible - just one file!
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse

# Create the FastAPI app
app = FastAPI(title="CompanyAI API", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint"""
    return """
    <html>
        <head>
            <title>CompanyAI API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .status { color: green; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 CompanyAI API is Running!</h1>
                <p class="status">✅ Deployment Successful!</p>
                <p>Your API is now live and responding to requests.</p>
                <h2>Available Endpoints:</h2>
                <ul>
                    <li><code>/</code> - This page</li>
                    <li><code>/health</code> - Health check</li>
                    <li><code>/gpt/health</code> - GPT health check</li>
                </ul>
            </div>
        </body>
    </html>
    """

@app.get("/health")
async def health():
    """Basic health check"""
    return {"status": "healthy", "message": "Service is running"}

@app.get("/gpt/health")
async def gpt_health():
    """GPT health check endpoint"""
    return {"status": "healthy", "message": "GPT service is running", "endpoint": "/gpt/health"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
