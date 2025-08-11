#!/usr/bin/env python3
"""
WSGI entry point for Render deployment
This creates a WSGI-compatible application for Gunicorn
"""

def application(environ, start_response):
    """Simple WSGI application that works with Gunicorn"""
    
    # Get the path from the request
    path = environ.get('PATH_INFO', '/')
    
    # Handle health check endpoint
    if path == '/gpt/health':
        status = '200 OK'
        response_headers = [('Content-Type', 'application/json')]
        start_response(status, response_headers)
        return [b'{"status": "healthy", "message": "Service is running"}']
    
    # Handle root endpoint
    elif path == '/':
        status = '200 OK'
        response_headers = [('Content-Type', 'text/html')]
        start_response(status, response_headers)
        return [b'<h1>CompanyAI API is running!</h1>']
    
    # Handle 404 for unknown paths
    else:
        status = '404 Not Found'
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        return [b'Endpoint not found']

# This is what Gunicorn expects
# The application variable should be available for Gunicorn to find
