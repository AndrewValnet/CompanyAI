#!/usr/bin/env python3
"""
Company Management API

FastAPI application for managing companies with AI-powered search and list management.
Supports moving companies between 'interested' and 'reached_out' lists.
"""

import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Company Management API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PG_DSN = os.getenv("PG_DSN", "postgresql://postgres:postgres@localhost:5432/similarweb")

# Pydantic models
class SearchRequest(BaseModel):
    prompt: str
    min_visits: Optional[int] = None
    limit: Optional[int] = 100
    exclude_reached_out: bool = True

class CompanyResponse(BaseModel):
    company_id: int
    domain: str
    name: Optional[str]
    country: Optional[str]
    industry: Optional[str]
    employee_range: Optional[str]
    tech_tags: Optional[List[str]]
    visits: Optional[float]
    pages_per_visit: Optional[float]
    avg_visit_secs: Optional[float]
    bounce_rate: Optional[float]
    similarity_score: Optional[float]

class ListOperationRequest(BaseModel):
    domain: str
    user: str = "system"

class ListResponse(BaseModel):
    companies: List[CompanyResponse]
    total: int
    page: int
    per_page: int

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(PG_DSN)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# OpenAI client
def get_openai_client():
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    return openai.OpenAI(api_key=OPENAI_API_KEY)

# Utility functions
def get_embedding(text: str, client: openai.OpenAI) -> List[float]:
    """Get embedding for text using OpenAI"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

def build_company_source_text(company_data: Dict[str, Any]) -> str:
    """Build source text for company embedding"""
    parts = []
    
    if company_data.get('name'):
        parts.append(company_data['name'])
    
    if company_data.get('industry'):
        parts.append(f"Industry: {company_data['industry']}")
    
    if company_data.get('country'):
        parts.append(f"Country: {company_data['country']}")
    
    if company_data.get('employee_range'):
        parts.append(f"Employees: {company_data['employee_range']}")
    
    if company_data.get('tech_tags'):
        parts.append(f"Tech: {', '.join(company_data['tech_tags'])}")
    
    return " | ".join(parts)

# API endpoints
@app.post("/search", response_model=List[CompanyResponse])
async def search_companies(
    request: SearchRequest,
    db: psycopg2.extensions.connection = Depends(get_db_connection),
    openai_client: openai.OpenAI = Depends(get_openai_client)
):
    """Search companies using AI prompt and optional filters"""
    
    # Generate embedding for the prompt
    prompt_embedding = get_embedding(request.prompt, openai_client)
    
    # Build the search query
    query = """
    SELECT 
        c.company_id,
        c.domain,
        c.name,
        c.country,
        c.industry,
        c.employee_range,
        c.tech_tags,
        ce.embedding <-> %s AS distance,
        m.visits,
        m.pages_per_visit,
        m.avg_visit_secs,
        m.bounce_rate
    FROM companies c
    LEFT JOIN company_embeddings ce ON c.company_id = ce.company_id
    LEFT JOIN LATERAL (
        SELECT * FROM company_metrics_monthly 
        WHERE company_id = c.company_id 
        AND country = 'WW'
        ORDER BY month DESC 
        LIMIT 1
    ) m ON true
    WHERE 1=1
    """
    
    params = [prompt_embedding]
    param_count = 1
    
    # Add filters
    if request.exclude_reached_out:
        query += f"""
        AND NOT EXISTS (
            SELECT 1 FROM list_members_current lmc
            JOIN lists l ON l.list_id = lmc.list_id
            WHERE lmc.company_id = c.company_id AND l.slug = 'reached_out'
        )
        """
    
    if request.min_visits:
        param_count += 1
        query += f" AND m.visits >= %s"
        params.append(request.min_visits)
    
    query += f"""
    ORDER BY distance ASC
    LIMIT %s
    """
    params.append(request.limit)
    
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            results = cur.fetchall()
            
            companies = []
            for row in results:
                company = CompanyResponse(
                    company_id=row['company_id'],
                    domain=row['domain'],
                    name=row['name'],
                    country=row['country'],
                    industry=row['industry'],
                    employee_range=row['employee_range'],
                    tech_tags=row['tech_tags'],
                    visits=row['visits'],
                    pages_per_visit=row['pages_per_visit'],
                    avg_visit_secs=row['avg_visit_secs'],
                    bounce_rate=row['bounce_rate'],
                    similarity_score=1.0 - (row['distance'] or 0)  # Convert distance to similarity
                )
                companies.append(company)
            
            return companies
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/lists/{list_slug}/add")
async def add_company_to_list(
    list_slug: str,
    request: ListOperationRequest,
    db: psycopg2.extensions.connection = Depends(get_db_connection)
):
    """Add a company to a specific list"""
    
    try:
        with db.cursor() as cur:
            # Get list ID
            cur.execute("SELECT list_id FROM lists WHERE slug = %s", (list_slug,))
            list_result = cur.fetchone()
            if not list_result:
                raise HTTPException(status_code=404, detail=f"List '{list_slug}' not found")
            
            list_id = list_result[0]
            
            # Get company ID
            cur.execute("SELECT company_id FROM companies WHERE lower(domain) = lower(%s)", (request.domain,))
            company_result = cur.fetchone()
            if not company_result:
                raise HTTPException(status_code=404, detail=f"Company with domain '{request.domain}' not found")
            
            company_id = company_result[0]
            
            # Check if already in list
            cur.execute("""
                SELECT 1 FROM list_memberships 
                WHERE list_id = %s AND company_id = %s AND removed_at IS NULL
            """, (list_id, company_id))
            
            if cur.fetchone():
                return {"message": f"Company already in list '{list_slug}'"}
            
            # Add to list
            cur.execute("""
                INSERT INTO list_memberships (list_id, company_id, added_by)
                VALUES (%s, %s, %s)
            """, (list_id, company_id, request.user))
            
            # Log status change
            cur.execute("""
                INSERT INTO company_status_history (company_id, from_status, to_status, changed_by)
                VALUES (%s, %s, %s, %s)
            """, (company_id, 'none', list_slug, request.user))
            
            db.commit()
            return {"message": f"Company added to list '{list_slug}'"}
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add company: {str(e)}")

@app.post("/lists/{list_slug}/remove")
async def remove_company_from_list(
    list_slug: str,
    request: ListOperationRequest,
    db: psycopg2.extensions.connection = Depends(get_db_connection)
):
    """Remove a company from a specific list"""
    
    try:
        with db.cursor() as cur:
            # Get list ID
            cur.execute("SELECT list_id FROM lists WHERE slug = %s", (list_slug,))
            list_result = cur.fetchone()
            if not list_result:
                raise HTTPException(status_code=404, detail=f"List '{list_slug}' not found")
            
            list_id = list_result[0]
            
            # Get company ID
            cur.execute("SELECT company_id FROM companies WHERE lower(domain) = lower(%s)", (request.domain,))
            company_result = cur.fetchone()
            if not company_result:
                raise HTTPException(status_code=404, detail=f"Company with domain '{request.domain}' not found")
            
            company_id = company_result[0]
            
            # Mark as removed
            cur.execute("""
                UPDATE list_memberships 
                SET removed_at = NOW(), removed_by = %s
                WHERE list_id = %s AND company_id = %s AND removed_at IS NULL
            """, (request.user, list_id, company_id))
            
            if cur.rowcount == 0:
                return {"message": f"Company not found in list '{list_slug}'"}
            
            # Log status change
            cur.execute("""
                INSERT INTO company_status_history (company_id, from_status, to_status, changed_by)
                VALUES (%s, %s, %s, %s)
            """, (company_id, list_slug, 'none', request.user))
            
            db.commit()
            return {"message": f"Company removed from list '{list_slug}'"}
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove company: {str(e)}")

@app.post("/promote/{domain}")
async def promote_company(
    domain: str,
    request: ListOperationRequest,
    db: psycopg2.extensions.connection = Depends(get_db_connection)
):
    """Promote company from 'interested' to 'reached_out' list"""
    
    try:
        with db.cursor() as cur:
            # Get company ID
            cur.execute("SELECT company_id FROM companies WHERE lower(domain) = lower(%s)", (domain,))
            company_result = cur.fetchone()
            if not company_result:
                raise HTTPException(status_code=404, detail=f"Company with domain '{domain}' not found")
            
            company_id = company_result[0]
            
            # Get list IDs
            cur.execute("SELECT list_id, slug FROM lists WHERE slug IN ('interested', 'reached_out')")
            lists = {row[1]: row[0] for row in cur.fetchall()}
            
            if 'interested' not in lists or 'reached_out' not in lists:
                raise HTTPException(status_code=500, detail="Required lists not found")
            
            # Remove from interested
            cur.execute("""
                UPDATE list_memberships 
                SET removed_at = NOW(), removed_by = %s
                WHERE list_id = %s AND company_id = %s AND removed_at IS NULL
            """, (request.user, lists['interested'], company_id))
            
            # Add to reached_out
            cur.execute("""
                INSERT INTO list_memberships (list_id, company_id, added_by)
                VALUES (%s, %s, %s)
            """, (lists['reached_out'], company_id, request.user))
            
            # Log status change
            cur.execute("""
                INSERT INTO company_status_history (company_id, from_status, to_status, changed_by)
                VALUES (%s, %s, %s, %s)
            """, (company_id, 'interested', 'reached_out', request.user))
            
            db.commit()
            return {"message": f"Company promoted from 'interested' to 'reached_out'"}
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to promote company: {str(e)}")

@app.get("/lists/{list_slug}", response_model=ListResponse)
async def get_list_companies(
    list_slug: str,
    page: int = 1,
    per_page: int = 100,
    db: psycopg2.extensions.connection = Depends(get_db_connection)
):
    """Get companies in a specific list with pagination"""
    
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cur:
            # Get list ID
            cur.execute("SELECT list_id FROM lists WHERE slug = %s", (list_slug,))
            list_result = cur.fetchone()
            if not list_result:
                raise HTTPException(status_code=404, detail=f"List '{list_slug}' not found")
            
            list_id = list_result[0]
            
            # Get total count
            cur.execute("""
                SELECT COUNT(*) FROM list_members_current lmc
                WHERE lmc.list_id = %s
            """, (list_id,))
            total = cur.fetchone()[0]
            
            # Get companies with pagination
            offset = (page - 1) * per_page
            cur.execute("""
                SELECT 
                    c.company_id,
                    c.domain,
                    c.name,
                    c.country,
                    c.industry,
                    c.employee_range,
                    c.tech_tags,
                    lmc.added_at,
                    m.visits,
                    m.pages_per_visit,
                    m.avg_visit_secs,
                    m.bounce_rate
                FROM list_members_current lmc
                JOIN companies c ON lmc.company_id = c.company_id
                LEFT JOIN LATERAL (
                    SELECT * FROM company_metrics_monthly 
                    WHERE company_id = c.company_id 
                    AND country = 'WW'
                    ORDER BY month DESC 
                    LIMIT 1
                ) m ON true
                WHERE lmc.list_id = %s
                ORDER BY lmc.added_at DESC
                LIMIT %s OFFSET %s
            """, (list_id, per_page, offset))
            
            results = cur.fetchall()
            
            companies = []
            for row in results:
                company = CompanyResponse(
                    company_id=row['company_id'],
                    domain=row['domain'],
                    name=row['name'],
                    country=row['country'],
                    industry=row['industry'],
                    employee_range=row['employee_range'],
                    tech_tags=row['tech_tags'],
                    visits=row['visits'],
                    pages_per_visit=row['pages_per_visit'],
                    avg_visit_secs=row['avg_visit_secs'],
                    bounce_rate=row['bounce_rate']
                )
                companies.append(company)
            
            return ListResponse(
                companies=companies,
                total=total,
                page=page,
                per_page=per_page
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get list: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
