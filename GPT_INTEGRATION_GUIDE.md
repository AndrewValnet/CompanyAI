# ChatGPT GPT Database Integration Guide

## Overview
This guide shows you how to connect your PostgreSQL database containing 248K+ companies to a ChatGPT GPT for AI-powered company research and outreach management.

## Option 1: Custom GPT with Database Actions (Recommended)

### Step 1: Create a Custom GPT
1. Go to [ChatGPT Plus](https://chat.openai.com/) and click "Explore GPTs"
2. Click "Create" to build a new GPT
3. Give it a name like "Company Research Assistant"

### Step 2: Configure GPT Instructions
Add these instructions to your GPT:

```
You are a Company Research Assistant with access to a database of 248,000+ companies. You can help users find companies based on specific criteria, analyze company data, and provide insights for outreach campaigns.

Your database contains:
- all_companies: 248K+ companies with traffic data
- reached_out_companies: 1K+ companies already contacted
- interested_companies: Companies of interest

You can search companies by:
- Name, website, or description
- Vertical/industry
- Location
- Traffic metrics (monthly visits, unique visitors)
- Engagement metrics (pages per visit, visit duration)

When users ask for company recommendations, use the search API to find relevant matches and provide detailed insights.
```

### Step 3: Add Database Actions
In your GPT configuration, add these actions:

#### Action 1: Search Companies
- **Name**: `search_companies`
- **Description**: Search for companies matching specific criteria
- **API Endpoint**: `http://localhost:8001/gpt/companies/search`
- **Method**: GET
- **Parameters**:
  - `query` (string): Search term
  - `limit` (integer): Number of results (default: 10)
  - `min_visits` (integer): Minimum monthly visits
  - `vertical` (string): Industry vertical
  - `location` (string): Company location

#### Action 2: Get Reached Out Companies
- **Name**: `get_reached_out_companies`
- **Description**: Get list of companies already contacted
- **API Endpoint**: `http://localhost:8001/gpt/companies/reached-out`
- **Method**: GET
- **Parameters**:
  - `limit` (integer): Number of results (default: 20)
  - `vertical` (string): Filter by vertical

#### Action 3: Get Database Stats
- **Name**: `get_database_stats`
- **Description**: Get database statistics and overview
- **API Endpoint**: `http://localhost:8001/gpt/companies/stats`
- **Method**: GET

## Option 2: Use Existing FastAPI Backend

### Step 1: Start the API Server
```bash
python gpt_api_endpoints.py
```

This will start a server on port 8001 with GPT-specific endpoints.

### Step 2: Test the API
```bash
# Test search endpoint
curl "http://localhost:8001/gpt/companies/search?query=gaming&limit=5"

# Test stats endpoint
curl "http://localhost:8001/gpt/companies/stats"
```

## Example GPT Prompts

### Company Discovery
```
"Find me 10 gaming companies with over 1 million monthly visits that are based in the US"
```

### Industry Analysis
```
"What are the top 5 verticals in my database and how many companies are in each?"
```

### Outreach Planning
```
"Show me companies in the fintech space with high traffic that I haven't reached out to yet"
```

### Competitive Research
```
"Find companies similar to Netflix in terms of traffic and engagement metrics"
```

## Security Considerations

### API Key Protection
- Your API key is sensitive - never share it publicly
- Consider implementing API key authentication for production use
- Use environment variables for sensitive configuration

### Database Access
- The current setup uses local database access
- For production, consider:
  - Database connection pooling
  - Rate limiting
  - IP whitelisting
  - SSL connections

## Troubleshooting

### Common Issues

1. **Connection Refused**: Make sure the FastAPI server is running on port 8001
2. **Database Connection Error**: Verify PostgreSQL is running and credentials are correct
3. **CORS Issues**: The API includes CORS middleware, but you may need to adjust for your specific setup

### Testing Your Setup

1. Start the API server: `python gpt_api_endpoints.py`
2. Test endpoints in your browser or with curl
3. Create your custom GPT and add the actions
4. Test with simple queries first

## Advanced Features

### Custom Filters
You can extend the search API to include:
- Date ranges
- Revenue estimates
- Technology stack information
- Social media presence

### Analytics Integration
Consider adding:
- Company growth trends
- Traffic pattern analysis
- Industry benchmarking
- Outreach success metrics

## Next Steps

1. **Start the API server** using the provided script
2. **Create your custom GPT** with the database actions
3. **Test the integration** with sample queries
4. **Customize the search logic** based on your specific needs
5. **Add more endpoints** for additional functionality

## Support

If you encounter issues:
1. Check the API server logs for error messages
2. Verify database connectivity
3. Test individual endpoints
4. Review the FastAPI documentation for advanced configuration
