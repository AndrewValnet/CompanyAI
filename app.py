#!/usr/bin/env python3
"""
CompanyAI GPT API - Integrated FastAPI application for Render deployment
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import psycopg
from psycopg.rows import dict_row
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Create the FastAPI app
app = FastAPI(
    title="CompanyAI GPT API", 
    description="API endpoints for GPT to query company database",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    host = os.getenv("DB_HOST", "localhost")
    dbname = os.getenv("DB_NAME", "CompanyAI")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "password")
    port = int(os.getenv("DB_PORT", "5432"))
    
    print(f"Attempting to connect to database: {host}:{port}/{dbname} as {user}")
    
    try:
        conn = psycopg.connect(
            host=host,
            dbname=dbname,
            user=user,
            password=password,
            port=port,
            connect_timeout=10,  # 10 second timeout
            sslmode="require",   # Require SSL for Render database
            sslcert=None,        # No client certificate
            sslkey=None,         # No client key
            sslrootcert=None     # No root certificate
        )
        print("Database connection successful!")
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API documentation"""
    return """
    <html>
        <head>
            <title>CompanyAI GPT API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .status { color: green; font-weight: bold; }
                .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
                .method { color: #007bff; font-weight: bold; }
                .url { font-family: monospace; background: #e9ecef; padding: 2px 6px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 CompanyAI GPT API</h1>
                <p class="status">✅ API is live and ready for GPT integration!</p>
                
                <h2>📊 Available Endpoints</h2>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/gpt/companies/search</span>
                    <p>Search companies with filters (query, limit, min_visits, vertical, location)</p>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/gpt/companies/reached-out</span>
                    <p>Get companies that have been reached out to</p>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/gpt/companies/stats</span>
                    <p>Get database statistics and company counts</p>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/gpt/health</span>
                    <p>Health check endpoint</p>
                </div>
                
                <h3>🔗 Test the API</h3>
                <p>Try: <a href="/gpt/health" target="_blank">/gpt/health</a></p>
                <p>Try: <a href="/gpt/companies/stats" target="_blank">/gpt/companies/stats</a></p>
            </div>
        </body>
    </html>
    """

@app.get("/gpt/companies/search")
async def search_companies_gpt(
    query: str = Query(..., description="Search query for companies"),
    limit: int = Query(10, description="Number of results to return"),
    min_visits: Optional[int] = Query(None, description="Minimum monthly visits"),
    vertical: Optional[str] = Query(None, description="Filter by vertical"),
    location: Optional[str] = Query(None, description="Filter by location")
):
    """Search companies for GPT integration"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(row_factory=dict_row)
        
        # Build the query dynamically
        sql = """
            SELECT 
                name, website, vertical, subvertical, description, location,
                monthly_visits, unique_visitors, pages_per_visit, adsense_enabled
            FROM all_companies 
            WHERE 1=1
        """
        params = []
        
        # Add text search
        if query:
            sql += """ AND (
                LOWER(name) LIKE LOWER(%s) OR 
                LOWER(website) LIKE LOWER(%s) OR 
                LOWER(description) LIKE LOWER(%s) OR
                LOWER(vertical) LIKE LOWER(%s) OR
                LOWER(subvertical) LIKE LOWER(%s)
            )"""
            search_term = f"%{query}%"
            params.extend([search_term, search_term, search_term, search_term, search_term])
        
        # Add filters
        if min_visits:
            sql += " AND monthly_visits >= %s"
            params.append(min_visits)
        
        if vertical:
            sql += " AND LOWER(vertical) = LOWER(%s)"
            params.append(vertical)
        
        if location:
            sql += " AND LOWER(location) LIKE LOWER(%s)"
            params.append(f"%{location}%")
        
        # Order by monthly visits (most popular first)
        sql += " ORDER BY monthly_visits DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "count": len(results),
            "companies": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to search companies"
        }

@app.get("/gpt/companies/reached-out")
async def get_reached_out_companies_gpt(
    limit: int = Query(20, description="Number of results to return"),
    vertical: Optional[str] = Query(None, description="Filter by vertical")
):
    """Get companies that have been reached out to"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(row_factory=dict_row)
        
        sql = """
            SELECT 
                name, website, vertical, subvertical, description, location,
                monthly_visits, unique_visitors, pages_per_visit, adsense_enabled,
                reached_out_date, response_status
            FROM all_companies 
            WHERE reached_out = true
        """
        params = []
        
        if vertical:
            sql += " AND LOWER(vertical) = LOWER(%s)"
            params.append(vertical)
        
        sql += " ORDER BY reached_out_date DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "count": len(results),
            "companies": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get reached out companies"
        }

@app.get("/gpt/companies/stats")
async def get_database_stats_gpt():
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(row_factory=dict_row)
        
        # Total companies
        cursor.execute("SELECT COUNT(*) as total FROM all_companies")
        total_companies = cursor.fetchone()["total"]
        
        # Companies by vertical
        cursor.execute("""
            SELECT vertical, COUNT(*) as count 
            FROM all_companies 
            WHERE vertical IS NOT NULL 
            GROUP BY vertical 
            ORDER BY count DESC
        """)
        vertical_stats = cursor.fetchall()
        
        # Companies reached out to
        cursor.execute("SELECT COUNT(*) as count FROM all_companies WHERE reached_out = true")
        reached_out_count = cursor.fetchone()["count"]
        
        # Average monthly visits
        cursor.execute("SELECT AVG(monthly_visits) as avg_visits FROM all_companies WHERE monthly_visits > 0")
        avg_visits = cursor.fetchone()["avg_visits"]
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "stats": {
                "total_companies": total_companies,
                "reached_out_count": reached_out_count,
                "average_monthly_visits": round(avg_visits, 2) if avg_visits else 0,
                "vertical_distribution": vertical_stats
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get database stats"
        }

@app.get("/companies")
async def get_all_companies(
    limit: int = Query(50, description="Number of companies to return"),
    offset: int = Query(0, description="Number of companies to skip")
):
    """Get all companies with pagination"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(row_factory=dict_row)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM all_companies")
        total_count = cursor.fetchone()["total"]
        
        # Get companies with pagination
        sql = """
            SELECT 
                name, website, vertical, subvertical, description, location,
                monthly_visits, unique_visitors, pages_per_visit, adsense_enabled
            FROM all_companies 
            ORDER BY monthly_visits DESC NULLS LAST, name ASC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(sql, (limit, offset))
        companies = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "total_companies": total_count,
            "returned_companies": len(companies),
            "limit": limit,
            "offset": offset,
            "companies": companies
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get companies"
        }

@app.get("/gpt/health")
async def gpt_health():
    """GPT health check endpoint"""
    return {
        "status": "healthy", 
        "message": "GPT API service is running",
        "endpoint": "/gpt/health",
        "available_endpoints": [
            "/gpt/companies/search",
            "/gpt/companies/reached-out", 
            "/gpt/companies/stats",
            "/gpt/health"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
