from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

import os

# Get the base URL from environment variable or use localhost for development
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8001")

app = FastAPI(
    title="Company Database GPT API", 
    description="API endpoints for GPT to query company database",
    servers=[
        {"url": BASE_URL, "description": "Production server"},
        {"url": "http://localhost:8001", "description": "Local development server"}
    ]
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
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "CompanyAI"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        port=int(os.getenv("DB_PORT", "5432"))
    )

@app.get("/gpt/companies/search")
async def search_companies_gpt(
    query: str = Query(..., description="Search query for companies"),
    limit: int = Query(10, description="Number of results to return"),
    min_visits: Optional[int] = Query(None, description="Minimum monthly visits"),
    vertical: Optional[str] = Query(None, description="Filter by vertical"),
    location: Optional[str] = Query(None, description="Filter by location")
):
    """
    Search companies for GPT integration
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
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
        
        # Convert to list of dicts
        companies = []
        for row in results:
            companies.append(dict(row))
        
        return {
            "success": True,
            "count": len(companies),
            "companies": companies,
            "query": query,
            "filters_applied": {
                "min_visits": min_visits,
                "vertical": vertical,
                "location": location
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.get("/gpt/companies/reached-out")
async def get_reached_out_companies_gpt(
    limit: int = Query(20, description="Number of results to return"),
    vertical: Optional[str] = Query(None, description="Filter by vertical")
):
    """
    Get companies that have been reached out to
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT 
                name, website, vertical, subvertical, description, location,
                monthly_visits, us_percentage
            FROM reached_out_companies 
            WHERE 1=1
        """
        params = []
        
        if vertical:
            sql += " AND LOWER(vertical) = LOWER(%s)"
            params.append(vertical)
        
        sql += " ORDER BY monthly_visits DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        companies = [dict(row) for row in results]
        
        return {
            "success": True,
            "count": len(companies),
            "companies": companies
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.get("/gpt/companies/stats")
async def get_database_stats_gpt():
    """
    Get database statistics for GPT context
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM all_companies")
        total_companies = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reached_out_companies")
        reached_out_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM interested_companies")
        interested_count = cursor.fetchone()[0]
        
        # Get top verticals
        cursor.execute("""
            SELECT vertical, COUNT(*) as count 
            FROM all_companies 
            WHERE vertical IS NOT NULL 
            GROUP BY vertical 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_verticals = cursor.fetchall()
        
        # Get top locations
        cursor.execute("""
            SELECT location, COUNT(*) as count 
            FROM all_companies 
            WHERE location IS NOT NULL 
            GROUP BY location 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_locations = cursor.fetchall()
        
        return {
            "success": True,
            "database_stats": {
                "total_companies": total_companies,
                "reached_out_companies": reached_out_count,
                "interested_companies": interested_count,
                "top_verticals": [{"vertical": v[0], "count": v[1]} for v in top_verticals],
                "top_locations": [{"location": l[0], "count": l[1]} for l in top_locations]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.get("/gpt/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Company Database GPT API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
