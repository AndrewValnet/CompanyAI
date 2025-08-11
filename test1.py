#!/usr/bin/env python3
import requests

# Your REST API key
API_KEY = "3a096c4234044544b8b2e13582e4c93c"

# Domain to test
domain = "google.com"

# Endpoint
url = f"https://api.similarweb.com/v1/website/{domain}/total-traffic-and-engagement/visits"

# All possible parameters (example values)
params = {
    "api_key": API_KEY,
    "start_date": "2024-01",        # YYYY-MM
    "end_date": "2024-03",          # YYYY-MM
    "country": "ww",                # 'ww' or 2-letter ISO
    "granularity": "monthly",       # 'daily', 'weekly', 'monthly'
    "main_domain_only": "false",    # 'true' or 'false'
    "format": "json",               # 'json' or 'xml'
    "show_verified": "true",        # 'true' or 'false'
    "mtd": "false",                  # 'true' or 'false' (mainly for daily granularity)
    "engaged_only": "false"         # 'true' or 'false'
}

response = requests.get(url, params=params)

if response.status_code == 200:
    print("Data fetched successfully!\n")
    print(response.json())
else:
    print(f"Error {response.status_code}: {response.text}")
