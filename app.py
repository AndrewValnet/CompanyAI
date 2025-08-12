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
import csv
from dotenv import load_dotenv
from urllib.parse import quote_plus

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
    # Try using the exact External Database URL first
    external_url = os.getenv("EXTERNAL_DATABASE_URL")
    if external_url:
        print(f"Trying External Database URL: {external_url.replace(external_url.split('@')[0].split(':')[2], '***')}")
        try:
            conn = psycopg.connect(external_url, connect_timeout=10)
            print("Database connection successful with External Database URL!")
            return conn
        except Exception as url_error:
            print(f"External Database URL failed: {url_error}")
    
    # Fallback to individual environment variables
    host = os.getenv("DB_HOST", "localhost")
    dbname = os.getenv("DB_NAME", "CompanyAI")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "password")
    port = int(os.getenv("DB_PORT", "5432"))
    
    print(f"Attempting to connect to database: {host}:{port}/{dbname} as {user}")
    
    try:
        # URL encode the password to handle special characters
        encoded_password = quote_plus(password)
        connection_string = f"postgresql://{user}:{encoded_password}@{host}:{port}/{dbname}?sslmode=require"
        print(f"Trying connection string: postgresql://{user}:***@{host}:{port}/{dbname}?sslmode=require")
        print(f"Password encoded: {encoded_password}")
        
        try:
            conn = psycopg.connect(connection_string, connect_timeout=10)
            print("Database connection successful!")
            return conn
        except Exception as conn_string_error:
            print(f"Connection string failed: {conn_string_error}")
            print("Trying individual parameters...")
            
            # Fallback to individual parameters
            conn = psycopg.connect(
                host=host,
                dbname=dbname,
                user=user,
                password=password,
                port=port,
                connect_timeout=10,
                sslmode="require"
            )
            print("Database connection successful with individual parameters!")
            return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        print(f"Connection details: {host}:{port}/{dbname} as {user}")
        print(f"SSL mode: require")
        print(f"Password length: {len(password)}")
        print(f"Password starts with: {password[:10]}...")
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
            "/gpt/health",
            "/setup-database",
            "/populate-sample-data",
            "/import-csv-data",
            "/debug-csv-files"
        ]
    }

@app.get("/setup-database")
async def setup_database():
    """Create the all_companies table if it doesn't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create the all_companies table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS all_companies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            website VARCHAR(255),
            vertical VARCHAR(255),
            subvertical VARCHAR(255),
            description TEXT,
            location VARCHAR(255),
            monthly_visits BIGINT,
            unique_visitors BIGINT,
            visit_duration VARCHAR(50),
            pages_per_visit NUMERIC(10,2),
            adsense_enabled BOOLEAN DEFAULT FALSE,
            us_percentage NUMERIC(5,2),
            reached_out BOOLEAN DEFAULT FALSE,
            reached_out_date TIMESTAMP,
            response_status VARCHAR(50)
        );
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        # Check if table was created
        cursor.execute("SELECT COUNT(*) as count FROM all_companies")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "Database table created successfully!",
            "table_name": "all_companies",
            "current_records": count
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to setup database table"
        }

@app.get("/populate-sample-data")
async def populate_sample_data():
    """Add sample company data to the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Sample company data
        sample_companies = [
            {
                "name": "TechCorp Solutions",
                "website": "techcorp-solutions.com",
                "vertical": "Technology",
                "subvertical": "Software Development",
                "description": "Leading software development company specializing in enterprise solutions",
                "location": "San Francisco, CA",
                "monthly_visits": 50000,
                "unique_visitors": 35000,
                "visit_duration": "00:03:45",
                "pages_per_visit": 3.2,
                "adsense_enabled": True,
                "us_percentage": 85.5,
                "reached_out": False
            },
            {
                "name": "GreenEnergy Innovations",
                "website": "greenenergy-innovations.com",
                "vertical": "Energy",
                "subvertical": "Renewable Energy",
                "description": "Pioneering renewable energy solutions for a sustainable future",
                "location": "Austin, TX",
                "monthly_visits": 25000,
                "unique_visitors": 18000,
                "visit_duration": "00:02:30",
                "pages_per_visit": 2.8,
                "adsense_enabled": False,
                "us_percentage": 92.3,
                "reached_out": True,
                "reached_out_date": "2024-01-15",
                "response_status": "Interested"
            },
            {
                "name": "HealthTech Pro",
                "website": "healthtech-pro.com",
                "vertical": "Healthcare",
                "subvertical": "Digital Health",
                "description": "Digital health platform connecting patients with healthcare providers",
                "location": "Boston, MA",
                "monthly_visits": 75000,
                "unique_visitors": 52000,
                "visit_duration": "00:04:15",
                "pages_per_visit": 4.1,
                "adsense_enabled": True,
                "us_percentage": 78.9,
                "reached_out": False
            },
            {
                "name": "EduLearn Academy",
                "website": "edulearn-academy.com",
                "vertical": "Education",
                "subvertical": "Online Learning",
                "description": "Comprehensive online learning platform for professional development",
                "location": "Seattle, WA",
                "monthly_visits": 120000,
                "unique_visitors": 85000,
                "visit_duration": "00:06:20",
                "pages_per_visit": 5.3,
                "adsense_enabled": True,
                "us_percentage": 88.7,
                "reached_out": True,
                "reached_out_date": "2024-02-01",
                "response_status": "No Response"
            },
            {
                "name": "FinTech Solutions",
                "website": "fintech-solutions.com",
                "vertical": "Finance",
                "subvertical": "Financial Technology",
                "description": "Innovative financial technology solutions for modern banking",
                "location": "New York, NY",
                "monthly_visits": 95000,
                "unique_visitors": 68000,
                "visit_duration": "00:03:55",
                "pages_per_visit": 3.9,
                "adsense_enabled": False,
                "us_percentage": 91.2,
                "reached_out": False
            }
        ]
        
        # Insert sample data
        insert_sql = """
        INSERT INTO all_companies 
        (name, website, vertical, subvertical, description, location, 
         monthly_visits, unique_visitors, visit_duration, pages_per_visit, 
         adsense_enabled, us_percentage, reached_out, reached_out_date, response_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        inserted_count = 0
        for company in sample_companies:
            try:
                cursor.execute(insert_sql, (
                    company["name"],
                    company["website"],
                    company["vertical"],
                    company["subvertical"],
                    company["description"],
                    company["location"],
                    company["monthly_visits"],
                    company["unique_visitors"],
                    company["visit_duration"],
                    company["pages_per_visit"],
                    company["adsense_enabled"],
                    company["us_percentage"],
                    company["reached_out"],
                    company.get("reached_out_date"),
                    company.get("response_status")
                ))
                inserted_count += 1
            except Exception as insert_error:
                print(f"Error inserting {company['name']}: {insert_error}")
                continue
        
        conn.commit()
        
        # Get final count
        cursor.execute("SELECT COUNT(*) as count FROM all_companies")
        total_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Sample data populated successfully!",
            "inserted_companies": inserted_count,
            "total_companies": total_count
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to populate sample data"
        }

@app.get("/import-csv-data")
async def import_csv_data():
    """Import company data from CSV files"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        imported_count = 0
        csv_files = [
            "CompanyAI/AI_Andrew_Outreach_List.csv",
            "CompanyAI/SW_List_Andrew.csv"
        ]
        
        for csv_file in csv_files:
            if not os.path.exists(csv_file):
                print(f"CSV file not found: {csv_file}")
                continue
                
            print(f"Processing CSV file: {csv_file}")
            
            with open(csv_file, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    try:
                        # Map CSV columns to database columns based on actual CSV structure
                        company_data = {
                            "name": row.get("Company Name", row.get("name", "")),
                            "website": row.get("Website", row.get("Domain", row.get("website", ""))),
                            "vertical": row.get("Vertical", row.get("vertical", "")),
                            "subvertical": row.get("Subvertical", row.get("subvertical", "")),
                            "description": row.get("Description", row.get("description", "")),
                            "location": row.get("Location", row.get("location", "")),
                            "monthly_visits": int(str(row.get("Monthly Visits", "0")).replace(",", "").replace(".", "").split(".")[0] or 0),
                            "unique_visitors": int(str(row.get("Unique Visitors", "0")).replace(",", "").replace(".", "").split(".")[0] or 0),
                            "visit_duration": row.get("Visit Duration", row.get("visit_duration", "")),
                            "pages_per_visit": float(row.get("Pages / Visit", row.get("pages_per_visit", "0")) or 0),
                            "adsense_enabled": row.get("AdSense", row.get("adsense_enabled", "")).lower() in ["true", "yes", "1"],
                            "us_percentage": float(str(row.get("US %", "0")).replace("%", "") or 0),
                            "reached_out": False,  # Default to False since not in CSV
                            "reached_out_date": None,  # Default to None since not in CSV
                            "response_status": ""  # Default to empty since not in CSV
                        }
                        
                        # Skip if no name or website
                        if not company_data["name"] or not company_data["website"]:
                            continue
                        
                        # Insert into database
                        insert_sql = """
                        INSERT INTO all_companies 
                        (name, website, vertical, subvertical, description, location, 
                         monthly_visits, unique_visitors, visit_duration, pages_per_visit, 
                         adsense_enabled, us_percentage, reached_out, reached_out_date, response_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (website) DO NOTHING
                        """
                        
                        cursor.execute(insert_sql, (
                            company_data["name"],
                            company_data["website"],
                            company_data["vertical"],
                            company_data["subvertical"],
                            company_data["description"],
                            company_data["location"],
                            company_data["monthly_visits"],
                            company_data["unique_visitors"],
                            company_data["visit_duration"],
                            company_data["pages_per_visit"],
                            company_data["adsense_enabled"],
                            company_data["us_percentage"],
                            company_data["reached_out"],
                            company_data["reached_out_date"],
                            company_data["response_status"]
                        ))
                        
                        imported_count += 1
                        
                        # Commit every 100 records
                        if imported_count % 100 == 0:
                            conn.commit()
                            print(f"Imported {imported_count} companies so far...")
                            
                    except Exception as row_error:
                        print(f"Error processing row: {row_error}")
                        continue
        
        conn.commit()
        
        # Get final count
        cursor.execute("SELECT COUNT(*) as count FROM all_companies")
        total_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"CSV data imported successfully!",
            "imported_companies": imported_count,
            "total_companies": total_count,
            "processed_files": [f for f in csv_files if os.path.exists(f)]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to import CSV data"
        }

@app.get("/debug-csv-files")
async def debug_csv_files():
    """Debug endpoint to check CSV files and their structure"""
    try:
        csv_files = [
            "CompanyAI/AI_Andrew_Outreach_List.csv",
            "CompanyAI/SW_List_Andrew.csv"
        ]
        
        debug_info = {
            "current_working_directory": os.getcwd(),
            "files_exist": {},
            "file_sizes": {},
            "sample_rows": {},
            "column_headers": {}
        }
        
        for csv_file in csv_files:
            file_exists = os.path.exists(csv_file)
            debug_info["files_exist"][csv_file] = file_exists
            
            if file_exists:
                # Get file size
                file_size = os.path.getsize(csv_file)
                debug_info["file_sizes"][csv_file] = f"{file_size:,} bytes"
                
                # Read first few rows to get headers and sample data
                try:
                    with open(csv_file, 'r', encoding='utf-8') as file:
                        csv_reader = csv.DictReader(file)
                        
                        # Get column headers
                        debug_info["column_headers"][csv_file] = csv_reader.fieldnames
                        
                        # Get first 3 rows as sample
                        sample_rows = []
                        for i, row in enumerate(csv_reader):
                            if i < 3:  # Only first 3 rows
                                sample_rows.append(row)
                            else:
                                break
                        
                        debug_info["sample_rows"][csv_file] = sample_rows
                        
                except Exception as read_error:
                    debug_info["sample_rows"][csv_file] = f"Error reading file: {read_error}"
                    debug_info["column_headers"][csv_file] = f"Error reading headers: {read_error}"
        
        return {
            "success": True,
            "debug_info": debug_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to debug CSV files"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
