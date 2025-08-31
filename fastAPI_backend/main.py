from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS, API_CONFIG
from routers import (
  company_router,
  company_card_routes,
  sustainability_router,
  cng_router,
  dashboard_router,
  search_routes,
  summary_routes,
  saved_reports,
)

# Create FastAPI app instance with centralized config
app = FastAPI(
    title=API_CONFIG["title"],
    description=API_CONFIG["description"],
    version=API_CONFIG["version"]
)

# CORS middleware with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Configurable origins from config.py
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include the routes from the router
app.include_router(company_router)
app.include_router(company_card_routes.router)
app.include_router(sustainability_router)
app.include_router(cng_router)
app.include_router(dashboard_router)
app.include_router(search_routes.router)
app.include_router(summary_routes.router)
app.include_router(saved_reports.router)
