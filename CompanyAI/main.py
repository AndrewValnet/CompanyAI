from fastapi import FastAPI
from company_management_api import app as core_app   # :8000 endpoints
from gpt_api_endpoints import app as gpt_app        # :8001 endpoints

app = FastAPI(title="CompanyAI")
app.mount("/", core_app)        # keeps your /search, /lists, /promote, /health
app.mount("/gpt", gpt_app)      # exposes /gpt/companies/* & /gpt/health
