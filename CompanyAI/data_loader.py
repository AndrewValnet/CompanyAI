#!/usr/bin/env python3
"""
Data Loader for Company Management System

Loads sample company data and generates embeddings for semantic search.
"""

import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import openai

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PG_DSN = os.getenv("PG_DSN", "postgresql://postgres:postgres@localhost:5432/similarweb")

# Sample company data (you can replace this with your actual 248k companies)
SAMPLE_COMPANIES = [
    {
        "domain": "shopify.com",
        "name": "Shopify",
        "website_url": "https://shopify.com",
        "country": "CA",
        "industry": "E-commerce",
        "employee_range": "10,000+",
        "tech_tags": ["shopify", "react", "ruby", "postgresql"]
    },
    {
        "domain": "stripe.com",
        "name": "Stripe",
        "website_url": "https://stripe.com",
        "country": "US",
        "industry": "Fintech",
        "employee_range": "5,000-10,000",
        "tech_tags": ["stripe", "react", "nodejs", "mongodb"]
    },
    {
        "domain": "notion.so",
        "name": "Notion",
        "website_url": "https://notion.so",
        "country": "US",
        "industry": "Productivity",
        "employee_range": "1,000-5,000",
        "tech_tags": ["notion", "react", "typescript", "postgresql"]
    },
    {
        "domain": "figma.com",
        "name": "Figma",
        "website_url": "https://figma.com",
        "country": "US",
        "industry": "Design",
        "employee_range": "1,000-5,000",
        "tech_tags": ["figma", "webgl", "typescript", "postgresql"]
    },
    {
        "domain": "slack.com",
        "name": "Slack",
        "website_url": "https://slack.com",
        "country": "US",
        "industry": "Communication",
        "employee_range": "5,000-10,000",
        "tech_tags": ["slack", "react", "nodejs", "postgresql"]
    },
    {
        "domain": "zoom.us",
        "name": "Zoom",
        "website_url": "https://zoom.us",
        "country": "US",
        "industry": "Communication",
        "employee_range": "5,000-10,000",
        "tech_tags": ["zoom", "webrtc", "python", "mysql"]
    },
    {
        "domain": "airtable.com",
        "name": "Airtable",
        "website_url": "https://airtable.com",
        "country": "US",
        "industry": "Productivity",
        "employee_range": "1,000-5,000",
        "tech_tags": ["airtable", "react", "nodejs", "postgresql"]
    },
    {
        "domain": "canva.com",
        "name": "Canva",
        "website_url": "https://canva.com",
        "country": "AU",
        "industry": "Design",
        "employee_range": "5,000-10,000",
        "tech_tags": ["canva", "react", "typescript", "mongodb"]
    },
    {
        "domain": "trello.com",
        "name": "Trello",
        "website_url": "https://trello.com",
        "country": "US",
        "industry": "Productivity",
        "employee_range": "1,000-5,000",
        "tech_tags": ["trello", "react", "nodejs", "mongodb"]
    },
    {
        "domain": "asana.com",
        "name": "Asana",
        "website_url": "https://asana.com",
        "country": "US",
        "industry": "Productivity",
        "employee_range": "1,000-5,000",
        "tech_tags": ["asana", "react", "python", "postgresql"]
    }
]

def get_openai_client():
    """Get OpenAI client"""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    return openai.OpenAI(api_key=OPENAI_API_KEY)

def build_company_source_text(company_data: dict) -> str:
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

def get_embedding(text: str, client: openai.OpenAI) -> list:
    """Get embedding for text using OpenAI"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Failed to get embedding for '{text}': {e}")
        return None

def load_companies():
    """Load companies into the database"""
    conn = psycopg2.connect(PG_DSN)
    
    try:
        with conn.cursor() as cur:
            # Insert companies
            company_data = []
            for company in SAMPLE_COMPANIES:
                company_data.append((
                    company['domain'],
                    company['name'],
                    company['website_url'],
                    company['country'],
                    company['industry'],
                    company['employee_range'],
                    company['tech_tags']
                ))
            
            execute_values(
                cur,
                """
                INSERT INTO companies (domain, name, website_url, country, industry, employee_range, tech_tags)
                VALUES %s
                ON CONFLICT (domain) DO UPDATE SET
                    name = EXCLUDED.name,
                    website_url = EXCLUDED.website_url,
                    country = EXCLUDED.country,
                    industry = EXCLUDED.industry,
                    employee_range = EXCLUDED.employee_range,
                    tech_tags = EXCLUDED.tech_tags,
                    updated_at = NOW()
                """,
                company_data
            )
            
            print(f"Loaded {len(company_data)} companies")
            conn.commit()
            
    except Exception as e:
        print(f"Error loading companies: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def generate_embeddings():
    """Generate embeddings for all companies"""
    if not OPENAI_API_KEY:
        print("Skipping embeddings generation - no OpenAI API key")
        return
    
    client = get_openai_client()
    conn = psycopg2.connect(PG_DSN)
    
    try:
        with conn.cursor() as cur:
            # Get all companies
            cur.execute("SELECT company_id, domain, name, industry, country, employee_range, tech_tags FROM companies")
            companies = cur.fetchall()
            
            embedding_data = []
            for company in companies:
                company_id, domain, name, industry, country, employee_range, tech_tags = company
                
                # Build source text
                company_dict = {
                    'name': name,
                    'industry': industry,
                    'country': country,
                    'employee_range': employee_range,
                    'tech_tags': tech_tags
                }
                source_text = build_company_source_text(company_dict)
                
                # Get embedding
                embedding = get_embedding(source_text, client)
                if embedding:
                    embedding_data.append((company_id, embedding, source_text))
                
                # Small delay to avoid rate limiting
                import time
                time.sleep(0.1)
            
            if embedding_data:
                # Insert embeddings
                execute_values(
                    cur,
                    """
                    INSERT INTO company_embeddings (company_id, embedding, source_text)
                    VALUES %s
                    ON CONFLICT (company_id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        source_text = EXCLUDED.source_text
                    """,
                    embedding_data
                )
                
                print(f"Generated embeddings for {len(embedding_data)} companies")
                conn.commit()
            
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def load_sample_metrics():
    """Load sample metrics data"""
    conn = psycopg2.connect(PG_DSN)
    
    try:
        with conn.cursor() as cur:
            # Get company IDs
            cur.execute("SELECT company_id FROM companies")
            company_ids = [row[0] for row in cur.fetchall()]
            
            # Generate sample metrics for the last 3 months
            from datetime import datetime, timedelta
            import random
            
            metrics_data = []
            base_date = datetime.now().replace(day=1)
            
            for company_id in company_ids:
                for i in range(3):
                    month = base_date - timedelta(days=30*i)
                    
                    # Sample metrics
                    visits = random.randint(10000, 1000000)
                    pages_per_visit = round(random.uniform(1.5, 8.0), 2)
                    avg_visit_secs = random.randint(30, 300)
                    bounce_rate = round(random.uniform(0.2, 0.7), 3)
                    page_views = int(visits * pages_per_visit)
                    
                    metrics_data.append((
                        company_id,
                        month.date(),
                        'WW',  # Worldwide
                        visits,
                        pages_per_visit,
                        avg_visit_secs,
                        bounce_rate,
                        page_views
                    ))
            
            if metrics_data:
                execute_values(
                    cur,
                    """
                    INSERT INTO company_metrics_monthly 
                    (company_id, month, country, visits, pages_per_visit, avg_visit_secs, bounce_rate, page_views)
                    VALUES %s
                    ON CONFLICT (company_id, month, country) DO UPDATE SET
                        visits = EXCLUDED.visits,
                        pages_per_visit = EXCLUDED.pages_per_visit,
                        avg_visit_secs = EXCLUDED.avg_visit_secs,
                        bounce_rate = EXCLUDED.bounce_rate,
                        page_views = EXCLUDED.page_views,
                        load_ts = NOW()
                    """,
                    metrics_data
                )
                
                print(f"Loaded metrics for {len(company_ids)} companies across 3 months")
                conn.commit()
            
    except Exception as e:
        print(f"Error loading metrics: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """Main function to load all data"""
    print("Starting data load...")
    
    try:
        # Load companies
        print("Loading companies...")
        load_companies()
        
        # Generate embeddings
        print("Generating embeddings...")
        generate_embeddings()
        
        # Load sample metrics
        print("Loading sample metrics...")
        load_sample_metrics()
        
        print("Data load completed successfully!")
        
    except Exception as e:
        print(f"Data load failed: {e}")
        raise

if __name__ == "__main__":
    main()
