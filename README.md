# Company Management System

An AI-powered system for managing and discovering companies using semantic search and list management. Built with FastAPI, PostgreSQL, and OpenAI embeddings.

## Features

- **AI-Powered Search**: Use natural language prompts to find companies that match your criteria
- **Semantic Search**: Leverages OpenAI embeddings for intelligent company matching
- **List Management**: Organize companies into "interested" and "reached out" lists
- **Company Promotion**: Move companies from interested to reached out status
- **Similarweb Integration**: Ready for Similarweb API data integration
- **Scalable Architecture**: Designed to handle 248k+ companies efficiently

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   FastAPI API   │    │   PostgreSQL    │
│                 │◄──►│                 │◄──►│                 │
│  (HTML/JS)     │    │  (Python)       │    │  + pgvector     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │  (Embeddings)   │
                       └─────────────────┘
```

## Database Schema

- **companies**: Master company data (domain, name, industry, tech stack, etc.)
- **company_metrics_monthly**: Similarweb traffic metrics by month
- **company_embeddings**: Vector embeddings for semantic search
- **lists**: Named lists (interested, reached_out)
- **list_memberships**: Company-list relationships with history
- **company_status_history**: Audit trail of status changes

## Quick Start

### 1. Prerequisites

- Python 3.8+
- PostgreSQL 12+ with pgvector extension
- OpenAI API key

### 2. Setup Database

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Run the schema.sql file
\i schema.sql
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file:

```env
# Database
PG_DSN=postgresql://username:password@localhost:5432/database_name

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Similarweb (optional)
SIMILARWEB_BATCH_API_KEY=your_similarweb_api_key
```

### 5. Load Sample Data

```bash
python data_loader.py
```

### 6. Start the API

```bash
python company_management_api.py
```

The API will be available at `http://localhost:8000`

### 7. Open Web Interface

Open `web_interface.html` in your browser to use the system.

## API Endpoints

### Search Companies
```http
POST /search
{
  "prompt": "E-commerce companies using React with high traffic",
  "min_visits": 100000,
  "limit": 20,
  "exclude_reached_out": true
}
```

### Add to List
```http
POST /lists/{list_slug}/add
{
  "domain": "example.com",
  "user": "username"
}
```

### Remove from List
```http
POST /lists/{list_slug}/remove
{
  "domain": "example.com",
  "user": "username"
}
```

### Promote Company
```http
POST /promote/{domain}
{
  "domain": "example.com",
  "user": "username"
}
```

### Get List Companies
```http
GET /lists/{list_slug}?page=1&per_page=100
```

## Usage Examples

### Finding E-commerce Companies
```
Prompt: "E-commerce companies using Shopify or WooCommerce with over 100k monthly visits"
```

### Finding Tech Companies
```
Prompt: "SaaS companies in the productivity space using React and TypeScript"
```

### Finding Companies by Location
```
Prompt: "US-based fintech companies with mobile apps"
```

## Scaling to 248k Companies

### 1. Bulk Company Import
Replace the sample data in `data_loader.py` with your actual company list:

```python
# Load from CSV file
import csv
with open('companies.csv', 'r') as f:
    reader = csv.DictReader(f)
    companies = [row for row in reader]
```

### 2. Batch Embedding Generation
For large datasets, process embeddings in batches:

```python
def generate_embeddings_batch(companies, batch_size=100):
    for i in range(0, len(companies), batch_size):
        batch = companies[i:i+batch_size]
        # Process batch
        time.sleep(1)  # Rate limiting
```

### 3. Similarweb Integration
Use the existing `similarweb_api.py` to fetch metrics:

```bash
python similarweb_api.py
```

## Performance Optimization

### Database Indexes
- Vector similarity search with HNSW index
- Domain lookups with lowercase index
- List membership queries with composite indexes

### Caching
- Consider Redis for frequently accessed data
- Cache search results for common queries

### Async Processing
- Use background tasks for embedding generation
- Queue-based processing for Similarweb data

## Monitoring and Maintenance

### Health Checks
```http
GET /health
```

### Database Maintenance
```sql
-- Analyze table statistics
ANALYZE companies;
ANALYZE company_embeddings;

-- Vacuum tables
VACUUM ANALYZE;
```

### Embedding Updates
- Re-generate embeddings when company data changes
- Monitor embedding quality and similarity scores

## Troubleshooting

### Common Issues

1. **pgvector extension not found**
   ```bash
   # Install pgvector
   sudo apt-get install postgresql-14-pgvector
   ```

2. **OpenAI API rate limits**
   - Implement exponential backoff
   - Use batch processing with delays

3. **Memory issues with large datasets**
   - Process embeddings in smaller batches
   - Monitor PostgreSQL memory usage

### Debug Mode
Set environment variable for detailed logging:
```bash
export LOG_LEVEL=DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs` when running
3. Open an issue on GitHub
