#!/usr/bin/env python3
"""
Gunicorn configuration file
This file is automatically read by Gunicorn and cannot be ignored
"""

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "company-database-gpt-api"

# Timeout
timeout = 30
keepalive = 2

# Preload app for better performance
preload_app = True

# Application module
app_name = "wsgi:application"
