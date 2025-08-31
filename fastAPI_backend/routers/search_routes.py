from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func
from models import Company, SustainabilityMetric
from database import get_db
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import time
from urllib.parse import unquote

logger = logging.getLogger(__name__)

# Add email service import
import sys
import os
try:
    # Add backend path for email service import - direct import approach
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up from fastAPI_backend/routers to project root
    project_root = os.path.dirname(os.path.dirname(current_dir))
    email_module_path = os.path.join(project_root, "backend", "src", "EmailService")
    
    # Also try relative path from current working directory  
    alt_email_path = os.path.join(os.getcwd(), "..", "backend", "src", "EmailService")
    
    # Add the EmailService directory directly to path
    for path in [email_module_path, alt_email_path]:
        if path not in sys.path and os.path.exists(path):
            sys.path.insert(0, path)
            logger.debug(f"Added EmailService path: {path}")
    
    # Import directly from the email_notification module
    from email_notification import send_completion_email
    EMAIL_SERVICE_AVAILABLE = True
    logger.info("Email service loaded successfully in search routes")
except ImportError as e:
    EMAIL_SERVICE_AVAILABLE = False
    logger.warning(f"Email service not available: {e}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    logger.debug(f"Current file directory: {os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else 'Unknown'}")
    
    # Debug: check what paths exist
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    email_path = os.path.join(project_root, "backend", "src", "EmailService", "email_notification.py")
    logger.debug(f"Looking for email module at: {email_path}")
    logger.debug(f"Email module exists: {os.path.exists(email_path)}")

class CompanySearchResult(BaseModel):
    company_id: int
    company_name: str
    company_summary: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None
    cng_adopt_score: Optional[int] = None

class SearchResponse(BaseModel):
    success: bool
    query: str
    total_results: int
    companies: List[CompanySearchResult]

router = APIRouter(
    prefix="/api/search",
    tags=["Search"]
)

# NEW: Check if company exists in database
@router.get("/company/exists/{company_name}", summary="Check if company exists in database")
async def check_company_exists(
    company_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if a company exists in the database using intelligent matching.
    Returns basic company info if found, 404 if not found.
    """
    if not company_name or not company_name.strip():
        raise HTTPException(status_code=400, detail="Company name cannot be empty")
    
    try:
        # Use the existing intelligent matching function
        existing_data = await find_existing_company(db, company_name.strip())
        
        if existing_data:
            company, metric = existing_data
            return {
                "exists": True,
                "company": {
                    "company_id": company.company_id,
                    "company_name": company.company_name,
                    "company_summary": company.company_summary,
                    "website_url": company.website_url,
                    "industry": company.industry
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Company not found in database")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking company existence: {str(e)}")

# NEW: Smart company search endpoint that runs scraper if company not found
@router.get("/companies", summary="Search companies - runs scraper if not in database")
async def search_companies(
    q: str = QueryParam(..., description="Company name to search for"),
    db: AsyncSession = Depends(get_db)
):
    """
    Smart company search that:
    1. First checks if company exists in database 
    2. If found, returns company data from database 
    3. If not found, runs the scraper to analyze the company
    4. Returns scraper results (WITHOUT saving to database until user clicks save)
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    # URL decode the company name to handle spaces and special characters
    company_name = unquote(q.strip())
    
    try:
        # Step 1: Check if company exists in database with improved matching
        logger.info(f"API: Searching for company: '{company_name}' in database")
        
        # Try multiple matching strategies
        existing_data = await find_existing_company(db, company_name)
        
        if existing_data:
            # Company found in database - convert to scraper format for consistency
            company, metric = existing_data
            logger.info(f"API: Found existing company in database: '{company.company_name}'")
            
            # Convert database data to original scraper JSON format
            db_to_scraper_results = await convert_db_data_to_scraper_format(company, metric, db)
            
            return db_to_scraper_results
        
        # Step 2: Company not found - run the scraper (but don't save yet)
        logger.info(f"API: Company '{company_name}' not found in database. Starting scraper analysis...")
        # Use the new scraper service for clean, structured results
        import sys
        import os
        
        # Add paths for proper import
        current_router_dir = os.path.dirname(__file__)
        actual_project_root = os.path.dirname(os.path.dirname(current_router_dir))
        actual_backend_path = os.path.join(actual_project_root, "backend")
        
        if actual_project_root not in sys.path:
            sys.path.insert(0, actual_project_root)
        if actual_backend_path not in sys.path:
            sys.path.insert(0, actual_backend_path)
        
        # Enable debug logging for scraper diagnostics
        import logging
        scraper_logger = logging.getLogger('backend.src.scraper.scraper_service')
        scraper_logger.setLevel(logging.DEBUG)
        
        logger.debug(f"API: Current working directory: {os.getcwd()}")
        logger.debug(f"API: Project root path: {actual_project_root}")
        logger.debug(f"API: Backend path: {actual_backend_path}")
        logger.debug(f"API: .env file path: {os.path.join(actual_project_root, '.env')}")
        logger.debug(f"API: .env file exists: {os.path.exists(os.path.join(actual_project_root, '.env'))}")
            
        from backend.src.scraper.scraper_service import analyze_company_structured
        
        structured_results = await run_async_wrapper(
            analyze_company_structured,
            company_name=company_name,
            verbose=False  # Keep verbose=False for API context
        )
        
        logger.info(f"API: Scraper analysis completed for {company_name}")
        
        # Send email notification after scraper completes
        if EMAIL_SERVICE_AVAILABLE:
            try:
                # Send email notification that analysis is ready
                email_success = send_completion_email(company_name, structured_results)
                
                if email_success:
                    logger.info(f"Email notification sent for {company_name} - analysis ready to view")
                else:
                    logger.warning(f"Email notification failed for {company_name}")
                    
            except Exception as email_error:
                # Don't fail the entire request if email fails
                logger.warning(f"Email notification error for {company_name}: {email_error}")
        else:
            logger.warning("Email service not available")
        
        return structured_results
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error in company search: {str(e)}")

async def find_existing_company(db: AsyncSession, search_name: str):
    """
    Intelligent company matching with multiple strategies.
    
    Args:
        db: Database session
        search_name: Company name to search for
        
    Returns:
        Tuple of (Company, SustainabilityMetric) if found, None otherwise
    """
    search_name_clean = search_name.strip()
    
    # Strategy 1: Exact match (case-insensitive)
    logger.debug(f"Trying exact match for: '{search_name_clean}'")
    exact_query = select(Company, SustainabilityMetric).outerjoin(
        SustainabilityMetric, Company.company_id == SustainabilityMetric.company_id
    ).filter(func.lower(Company.company_name) == func.lower(search_name_clean))
    
    result = await db.execute(exact_query)
    exact_match = result.first()
    if exact_match:
        logger.debug(f"Exact match found: '{exact_match[0].company_name}'")
        return exact_match
    
    # Strategy 2: Partial match (search name contained in database name)
    logger.debug(f"Trying partial match for: '{search_name_clean}'")
    partial_query = select(Company, SustainabilityMetric).outerjoin(
        SustainabilityMetric, Company.company_id == SustainabilityMetric.company_id
    ).filter(func.lower(Company.company_name).contains(func.lower(search_name_clean)))
    
    result = await db.execute(partial_query)
    partial_matches = result.all()
    
    if partial_matches:
        # If multiple matches, prefer the shortest one (most likely to be correct)
        best_match = min(partial_matches, key=lambda x: len(x[0].company_name))
        logger.debug(f"Partial match found: '{best_match[0].company_name}' (from {len(partial_matches)} matches)")
        return best_match
    
    # Strategy 3: Reverse partial match (database name contained in search name)
    logger.debug(f"Trying reverse partial match for: '{search_name_clean}'")
    reverse_query = select(Company, SustainabilityMetric).outerjoin(
        SustainabilityMetric, Company.company_id == SustainabilityMetric.company_id
    ).filter(func.lower(search_name_clean).contains(func.lower(Company.company_name)))
    
    result = await db.execute(reverse_query)
    reverse_matches = result.all()
    
    if reverse_matches:
        # If multiple matches, prefer the longest database name (most specific)
        best_match = max(reverse_matches, key=lambda x: len(x[0].company_name))
        logger.debug(f"Reverse partial match found: '{best_match[0].company_name}' (from {len(reverse_matches)} matches)")
        return best_match
    
    # Strategy 4: Common abbreviations and aliases
    logger.debug(f"Trying abbreviation/alias match for: '{search_name_clean}'")
    alias_match = await find_company_by_alias(db, search_name_clean)
    if alias_match:
        logger.debug(f"Alias match found: '{alias_match[0].company_name}'")
        return alias_match
    
    logger.debug(f"No matches found for: '{search_name_clean}'")
    return None

async def find_company_by_alias(db: AsyncSession, search_name: str):
    """
    Check for common company name abbreviations and aliases.
    
    Args:
        db: Database session
        search_name: Company name to search for
        
    Returns:
        Tuple of (Company, SustainabilityMetric) if found, None otherwise
    """
    search_lower = search_name.lower().strip()
    
    # Common company aliases and abbreviations
    company_aliases = {
        # Transportation & Logistics
        'fedex': ['fedex corporation', 'federal express', 'fedex corp'],
        'ups': ['united parcel service', 'ups inc', 'united parcel service inc'],
        'amazon': ['amazon.com inc', 'amazon inc', 'amazon.com', 'amazon corporation'],
        'walmart': ['walmart inc', 'wal-mart', 'wal-mart stores inc'],
        'target': ['target corporation', 'target corp'],
        'dhl': ['dhl international', 'dhl express', 'deutsche post dhl'],
        
        # Tech companies (in case they have fleets)
        'google': ['alphabet inc', 'google llc', 'alphabet'],
        'apple': ['apple inc'],
        'microsoft': ['microsoft corporation', 'microsoft corp'],
        'meta': ['meta platforms inc', 'facebook inc', 'facebook'],
        
        # Others
        'ford': ['ford motor company', 'ford motor co'],
        'gm': ['general motors', 'general motors company'],
        'tesla': ['tesla inc', 'tesla motors']
    }
    
    # Check if search name is a known alias
    potential_names = []
    
    # Direct alias lookup
    if search_lower in company_aliases:
        potential_names.extend(company_aliases[search_lower])
    
    # Reverse lookup - if search contains a known alias
    for alias, full_names in company_aliases.items():
        if alias in search_lower:
            potential_names.extend(full_names)
    
    # Search for each potential name
    for potential_name in potential_names:
        alias_query = select(Company, SustainabilityMetric).outerjoin(
            SustainabilityMetric, Company.company_id == SustainabilityMetric.company_id
        ).filter(func.lower(Company.company_name) == func.lower(potential_name))
        
        result = await db.execute(alias_query)
        match = result.first()
        if match:
            return match
    
    return None

async def convert_db_data_to_scraper_format(company: Company, metric: SustainabilityMetric, db: AsyncSession) -> dict:
    """
    Convert database data back to the original scraper JSON format for consistent frontend display.
    """
    from models import MetricSource, FleetSummary, EmissionsSummary, AltFuelsSummary, CleanEnergyPartnersSummary, RegulatoryPressureSummary
    
    # 1. Company data
    company_data = {
        "company_name": company.company_name,
        "company_summary": company.company_summary,
        "website_url": company.website_url or "",
        "industry": company.industry or "",
        "cso_linkedin_url": company.cso_linkedin_url or ""
    }
    
    # 2. Sustainability metrics (convert back to original format)
    sustainability_metrics = {
        "owns_cng_fleet": metric.owns_cng_fleet if metric else None,
        "cng_fleet_size_range": metric.cng_fleet_size_range if metric and metric.cng_fleet_size_range > 0 else None,
        "cng_fleet_size_actual": metric.cng_fleet_size_actual if metric and metric.cng_fleet_size_actual > 0 else None,
        "total_fleet_size": metric.total_fleet_size if metric and metric.total_fleet_size > 0 else None,
        "emission_report": metric.emission_report if metric else None,
        "emission_goals": metric.emission_goals if metric and metric.emission_goals > 0 else None,
        "alt_fuels": metric.alt_fuels if metric else None,
        "clean_energy_partners": metric.clean_energy_partners if metric else None,
        "regulatory_pressure": metric.regulatory_pressure if metric else None
    }
    
    # 3. Metric sources (group by URL and reverse map metric names)
    metric_sources = []
    if metric:
        sources_query = select(MetricSource).filter(MetricSource.metric_id == metric.metric_id)
        sources_result = await db.execute(sources_query)
        db_sources = sources_result.scalars().all()
        
        # Group sources by URL and contribution text
        sources_grouped = {}
        for source in db_sources:
            key = (source.source_url, source.contribution_text)
            if key not in sources_grouped:
                sources_grouped[key] = []
            
            # Reverse map database metric names back to JSON format
            json_metric_name = map_db_metric_name_to_json(source.metric_name)
            sources_grouped[key].append(json_metric_name)
        
        # Convert to expected format
        for (source_url, contribution_text), metric_names in sources_grouped.items():
            metric_sources.append({
                "metric_name": metric_names,
                "source_url": source_url,
                "contribution_text": contribution_text
            })
    
    # 4. Summaries
    summaries = {}
    if metric:
        # Fleet Summary
        fleet_query = select(FleetSummary).filter(FleetSummary.metric_id == metric.metric_id)
        fleet_result = await db.execute(fleet_query)
        fleet_summary = fleet_result.scalars().first()
        if fleet_summary:
            summaries["fleet_summary"] = {
                "metric_name": "owns_cng_fleet",
                "summary_text": fleet_summary.summary_text
            }
        
        # Emissions Summary
        emissions_query = select(EmissionsSummary).filter(EmissionsSummary.metric_id == metric.metric_id)
        emissions_result = await db.execute(emissions_query)
        emissions_summary = emissions_result.scalars().first()
        if emissions_summary:
            summaries["emissions_summary"] = {
                "metric_name": "emission_report",
                "emissions_summary": emissions_summary.emissions_summary,
                "emissions_goals_summary": emissions_summary.emissions_goals_summary,
                "current_emissions": emissions_summary.current_emissions,
                "target_year": emissions_summary.target_year,
                "target_emissions": emissions_summary.target_emissions
            }
        
        # Alt Fuels Summary
        alt_fuels_query = select(AltFuelsSummary).filter(AltFuelsSummary.metric_id == metric.metric_id)
        alt_fuels_result = await db.execute(alt_fuels_query)
        alt_fuels_summary = alt_fuels_result.scalars().first()
        if alt_fuels_summary:
            summaries["alt_fuels_summary"] = {
                "metric_name": "alt_fuels",
                "summary_text": alt_fuels_summary.summary_text
            }
        
        # Clean Energy Partners Summary
        clean_energy_query = select(CleanEnergyPartnersSummary).filter(CleanEnergyPartnersSummary.metric_id == metric.metric_id)
        clean_energy_result = await db.execute(clean_energy_query)
        clean_energy_summary = clean_energy_result.scalars().first()
        if clean_energy_summary:
            summaries["clean_energy_partners_summary"] = {
                "metric_name": "clean_energy_partners",
                "summary_text": clean_energy_summary.summary_text
            }
        
        # Regulatory Pressure Summary
        regulatory_query = select(RegulatoryPressureSummary).filter(RegulatoryPressureSummary.metric_id == metric.metric_id)
        regulatory_result = await db.execute(regulatory_query)
        regulatory_summary = regulatory_result.scalars().first()
        if regulatory_summary:
            summaries["regulatory_pressure_summary"] = {
                "metric_name": "regulatory_pressure",
                "summary_text": regulatory_summary.summary_text
            }
    
    # 5. Overall score (from cng_adopt_score)
    overall_score = {
        "overall_score_percentage": float(metric.cng_adopt_score) if metric and metric.cng_adopt_score else 0.0
    }
    
    # Return in exact original format
    return {
        "company": company_data,
        "sustainability_metrics": sustainability_metrics,
        "metric_sources": metric_sources,
        "summaries": summaries,
        "overall_score": overall_score
    }

def map_db_metric_name_to_json(db_metric_name: str) -> str:
    """Reverse map database metric names back to JSON format"""
    reverse_mapping = {
        "emission_report": "emission_reporting",
        "owns_cng_fleet": "cng_fleet",
        "cng_fleet_size_range": "cng_fleet_size",
        "total_fleet_size": "total_truck_fleet_size",
        "clean_energy_partners": "clean_energy_partner",
        "regulatory_pressure": "regulatory"
    }
    return reverse_mapping.get(db_metric_name, db_metric_name)

async def run_async_wrapper(func, **kwargs):
    """
    Async wrapper to run synchronous functions in async context.
    Properly handles exceptions and prevents orphaned tasks.
    """
    import asyncio
    
    # Create a proper wrapper function that handles exceptions
    def safe_wrapper():
        try:
            # Add progress logging
            logger.info(f"Starting comprehensive analysis for {kwargs.get('company_name', 'unknown')}")
            start_time = time.time()
            
            result = func(**kwargs)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Analysis completed in {elapsed_time:.1f} seconds")
            return result
            
        except Exception as e:
            # Log the exception in the thread
            logger.error(f"Scraper function failed: {str(e)}")
            logger.exception("Full scraper traceback:")
            # Re-raise so it can be caught by the executor
            raise
    
    try:
        # Run the synchronous function in a thread pool with timeout (25 minutes max for comprehensive analysis)
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, safe_wrapper),
            timeout=1500.0  # 25 minutes for comprehensive analysis (user expects up to 30 mins)
        )
        return result
        
    except asyncio.TimeoutError:
        logger.error("Scraper analysis timed out after 25 minutes")
        raise HTTPException(
            status_code=408,
            detail="Analysis timed out after 25 minutes. Please try again later."
        )
        
    except Exception as e:
        # This will catch exceptions from the thread pool
        logger.error(f"Async wrapper failed: {str(e)}")
        
        # Handle specific error types with appropriate HTTP status codes
        if isinstance(e, EnvironmentError):
            # Environment/API key related errors
            logger.error(f"Environment configuration error: {str(e)}")
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail=f"Service configuration error: Missing required API keys. Please contact administrator."
            )
        elif "OPENAI_API_KEY" in str(e) or "GOOGLE_CSE" in str(e):
            # Environment variable related errors
            logger.error(f"API key configuration error: {str(e)}")
            raise HTTPException(
                status_code=503,  # Service Unavailable  
                detail="Service configuration error: Required API credentials not found. Please contact administrator."
            )
        else:
            # Generic analysis errors
            raise HTTPException(
                status_code=500, 
                detail=f"Analysis failed: {str(e)[:200]}..."
            )

# Test endpoint to check scraper integration
@router.get("/test-scraper/{company_name}", summary="Test scraper integration")
async def test_scraper(company_name: str):
    """
    Test endpoint to check if the scraper can be imported and basic setup works.
    """
    try:
        import sys
        import os
        
        # Add the project root directory to Python path to access backend module
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(os.path.dirname(current_dir))  # Go up from fastAPI_backend/routers to project root
        backend_path = os.path.join(project_root, "backend")
        
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # Check .env file
        env_file_path = os.path.join(project_root, '.env')
        env_exists = os.path.exists(env_file_path)
        
        # Try to import the scraper function
        from backend.src.scraper.main_ai_scraper import analyze_company_sustainability
        
        # Try to import the scraper service 
        from backend.src.scraper.scraper_service import ScraperService
        
        # Test environment validation
        try:
            service = ScraperService()
            environment_valid = True
            environment_error = None
        except EnvironmentError as e:
            environment_valid = False
            environment_error = str(e)
        
        # Check individual environment variables
        env_vars = {
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "GOOGLE_CSE_API_KEY": bool(os.getenv("GOOGLE_CSE_API_KEY")),
            "GOOGLE_CSE_ID": bool(os.getenv("GOOGLE_CSE_ID"))
        }
        
        return {
            "success": True,
            "message": f"Scraper successfully imported for {company_name}",
            "environment_check": {
                "project_root": project_root,
                "backend_path": backend_path,
                "env_file_path": env_file_path,
                "env_file_exists": env_exists,
                "environment_valid": environment_valid,
                "environment_error": environment_error,
                "api_keys_found": env_vars,
                "missing_keys": [k for k, v in env_vars.items() if not v]
            },
            "scraper_function": str(analyze_company_sustainability),
            "working_directory": os.getcwd()
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Could not import scraper: {str(e)}",
            "backend_path": backend_path if 'backend_path' in locals() else "Not set",
            "project_root": project_root if 'project_root' in locals() else "Not set",
            "working_directory": os.getcwd()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"General error: {str(e)}",
            "working_directory": os.getcwd()
        }

def map_fleet_size_to_range(cng_fleet_evidence: dict) -> int:
    """Map CNG fleet size evidence to database range values (0-3)"""
    if not cng_fleet_evidence.get('found', False):
        return 0
    
    evidence_text = cng_fleet_evidence.get('evidence', '').lower()
    
    # Extract numbers from evidence
    import re
    numbers = re.findall(r'\d+', evidence_text)
    if numbers:
        try:
            fleet_size = int(numbers[0])
            if fleet_size == 0:
                return 0
            elif 1 <= fleet_size <= 10:
                return 1
            elif 11 <= fleet_size <= 50:
                return 2
            else:
                return 3
        except ValueError:
            pass
    
    return 0

def extract_fleet_size_actual(cng_fleet_evidence: dict) -> int:
    """Extract actual CNG fleet size number"""
    if not cng_fleet_evidence.get('found', False):
        return 0
    
    evidence_text = cng_fleet_evidence.get('evidence', '')
    
    import re
    numbers = re.findall(r'\d+', evidence_text)
    if numbers:
        try:
            return int(numbers[0])
        except ValueError:
            pass
    
    return 0

def extract_total_fleet_size(total_fleet_evidence: dict) -> int:
    """Extract total fleet size number"""
    if not total_fleet_evidence.get('found', False):
        return 0
    
    evidence_text = total_fleet_evidence.get('evidence', '')
    
    import re
    numbers = re.findall(r'\d+', evidence_text)
    if numbers:
        try:
            return int(numbers[0])
        except ValueError:
            pass
    
    return 0

def map_emission_goals(emission_goals_evidence: dict) -> int:
    """Map emission goals evidence to database values (0-2)"""
    if not emission_goals_evidence.get('found', False):
        return 0
    
    evidence_text = emission_goals_evidence.get('evidence', '').lower()
    justification = emission_goals_evidence.get('justification', '').lower()
    
    # Check for timeline indicators
    timeline_indicators = ['by 2030', 'by 2040', 'by 2050', 'target', 'deadline', 'timeline']
    if any(indicator in evidence_text or indicator in justification for indicator in timeline_indicators):
        return 2  # Goal with timeline
    else:
        return 1  # Goal mentioned

def map_criterion_to_db_name(criterion: str) -> str:
    """Map scraper criterion names to database metric names"""
    mapping = {
        'cng_fleet': 'owns_cng_fleet',
        'cng_fleet_size': 'cng_fleet_size_range',
        'total_truck_fleet_size': 'total_fleet_size',
        'emission_reporting': 'emission_report',
        'emission_goals': 'emission_goals',
        'alt_fuels': 'alt_fuels',
        'clean_energy_partner': 'clean_energy_partners',
        'regulatory': 'regulatory_pressure'
    }
    return mapping.get(criterion, criterion)

class CompanyData(BaseModel):
    company_name: str
    company_summary: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None
    cso_linkedin_url: Optional[str] = None

class SustainabilityMetricsData(BaseModel):
    owns_cng_fleet: Optional[bool] = None
    cng_fleet_size_range: Optional[int] = None
    cng_fleet_size_actual: Optional[int] = None
    total_fleet_size: Optional[int] = None
    emission_report: Optional[bool] = None
    emission_goals: Optional[int] = None
    alt_fuels: Optional[bool] = None
    clean_energy_partners: Optional[bool] = None
    regulatory_pressure: Optional[bool] = None

class MetricSourceData(BaseModel):
    metric_name: List[str]  # JSON has arrays
    source_url: str
    contribution_text: str

class SummaryData(BaseModel):
    metric_name: str
    summary_text: str

class EmissionsSummaryData(BaseModel):
    metric_name: str
    emissions_summary: str
    emissions_goals_summary: str
    current_emissions: Optional[int] = None
    target_year: Optional[int] = None
    target_emissions: Optional[int] = None

class SummariesData(BaseModel):
    fleet_summary: Optional[SummaryData] = None
    emissions_summary: Optional[EmissionsSummaryData] = None
    alt_fuels_summary: Optional[SummaryData] = None
    clean_energy_partners_summary: Optional[SummaryData] = None
    regulatory_pressure_summary: Optional[SummaryData] = None

class OverallScoreData(BaseModel):
    overall_score_percentage: float
    # Optional fields - not stored in database, only used for display
    total_weighted_score: Optional[float] = None
    total_possible_score: Optional[float] = None
    criteria_breakdown: Optional[Dict[str, Any]] = None
    score_calculation: Optional[Dict[str, Any]] = None

class ScraperDataComplete(BaseModel):
    company: CompanyData
    sustainability_metrics: SustainabilityMetricsData
    metric_sources: List[MetricSourceData]
    summaries: SummariesData
    overall_score: OverallScoreData

# NEW: Save scraper results to database (called when user clicks save)
@router.post("/save-company", summary="Save scraper results to database")
async def save_company_to_database(
    scraper_data: ScraperDataComplete,
    db: AsyncSession = Depends(get_db)
):
    """
    Save scraper results to database when user clicks save button.
    Properly handles the structured JSON format from the scraper.
    """
    try:
        company_name = scraper_data.company.company_name
        if not company_name:
            raise HTTPException(status_code=400, detail="Company name is required")
        
        # Import database dependencies
        from sqlalchemy.future import select
        from sqlalchemy import func
        from models import Company, SustainabilityMetric, MetricSource
        from models import FleetSummary, EmissionsSummary, AltFuelsSummary, CleanEnergyPartnersSummary, RegulatoryPressureSummary
        
        # Check if company already exists
        existing_company_query = select(Company).filter(
            func.lower(Company.company_name) == func.lower(company_name)
        )
        result = await db.execute(existing_company_query)
        if result.first():
            raise HTTPException(status_code=409, detail="Company already exists in database")
        
        # 1. Create Company
        db_company = Company(
            company_name=scraper_data.company.company_name,
            company_summary=scraper_data.company.company_summary,
            website_url=scraper_data.company.website_url,
            industry=scraper_data.company.industry,
            cso_linkedin_url=scraper_data.company.cso_linkedin_url
        )
        db.add(db_company)
        await db.flush()  # Get company_id
        
        # 2. Create SustainabilityMetric 
        metrics = scraper_data.sustainability_metrics
        # Map JSON overall_score.overall_score_percentage to database cng_adopt_score field
        cng_adopt_score = int(scraper_data.overall_score.overall_score_percentage)
        
        # Ensure all required fields have proper defaults per schema constraints
        db_metrics = SustainabilityMetric(
            company_id=db_company.company_id,
            owns_cng_fleet=bool(metrics.owns_cng_fleet) if metrics.owns_cng_fleet is not None else False,
            cng_fleet_size_range=metrics.cng_fleet_size_range if metrics.cng_fleet_size_range is not None else 0,
            cng_fleet_size_actual=metrics.cng_fleet_size_actual if metrics.cng_fleet_size_actual is not None else 0,
            total_fleet_size=metrics.total_fleet_size if metrics.total_fleet_size is not None else 0,
            emission_report=bool(metrics.emission_report) if metrics.emission_report is not None else False,
            emission_goals=metrics.emission_goals if metrics.emission_goals is not None else 0,
            alt_fuels=bool(metrics.alt_fuels) if metrics.alt_fuels is not None else False,
            clean_energy_partners=bool(metrics.clean_energy_partners) if metrics.clean_energy_partners is not None else False,
            regulatory_pressure=bool(metrics.regulatory_pressure) if metrics.regulatory_pressure is not None else False,
            cng_adopt_score=cng_adopt_score
        )
        db.add(db_metrics)
        await db.flush()  # Get metric_id
        
        # 3. Create MetricSources with proper name mapping
        def map_json_metric_name_to_db(json_metric_name: str) -> str:
            """Map JSON metric names to database-allowed metric names"""
            mapping = {
                "emission_reporting": "emission_report",
                "cng_fleet": "owns_cng_fleet",
                "cng_fleet_size": "cng_fleet_size_range",
                "total_truck_fleet_size": "total_fleet_size",
                "clean_energy_partner": "clean_energy_partners",
                "regulatory": "regulatory_pressure"
            }
            return mapping.get(json_metric_name, json_metric_name)
        
        for source_data in scraper_data.metric_sources:
            # Handle array of metric names by creating separate entries
            for json_metric_name in source_data.metric_name:
                # Map to database-allowed metric name
                db_metric_name = map_json_metric_name_to_db(json_metric_name)
                
                # Only create if it's a valid database metric name
                valid_metric_names = {
                    'owns_cng_fleet', 'cng_fleet_size_range', 'cng_fleet_size_actual', 
                    'total_fleet_size', 'emission_report', 'emission_goals', 
                    'alt_fuels', 'clean_energy_partners', 'regulatory_pressure'
                }
                
                if db_metric_name in valid_metric_names:
                    db_source = MetricSource(
                        metric_id=db_metrics.metric_id,
                        metric_name=db_metric_name,
                        source_url=source_data.source_url,
                        contribution_text=source_data.contribution_text
                    )
                    db.add(db_source)
                else:
                    logger.warning(f"Skipping invalid metric name: {json_metric_name} -> {db_metric_name}")
        
        # 4. Create Summary tables
        summaries = scraper_data.summaries
        
        # Fleet Summary
        if summaries.fleet_summary:
            db.add(FleetSummary(
                metric_id=db_metrics.metric_id,
                summary_text=summaries.fleet_summary.summary_text
            ))
        
        # Emissions Summary
        if summaries.emissions_summary:
            db.add(EmissionsSummary(
                metric_id=db_metrics.metric_id,
                emissions_summary=summaries.emissions_summary.emissions_summary,
                emissions_goals_summary=summaries.emissions_summary.emissions_goals_summary,
                current_emissions=summaries.emissions_summary.current_emissions,
                target_year=summaries.emissions_summary.target_year,
                target_emissions=summaries.emissions_summary.target_emissions
            ))
        
        # Alt Fuels Summary
        if summaries.alt_fuels_summary:
            db.add(AltFuelsSummary(
                metric_id=db_metrics.metric_id,
                summary_text=summaries.alt_fuels_summary.summary_text
            ))
        
        # Clean Energy Partners Summary
        if summaries.clean_energy_partners_summary:
            db.add(CleanEnergyPartnersSummary(
                metric_id=db_metrics.metric_id,
                summary_text=summaries.clean_energy_partners_summary.summary_text
            ))
        
        # Regulatory Pressure Summary
        if summaries.regulatory_pressure_summary:
            db.add(RegulatoryPressureSummary(
                metric_id=db_metrics.metric_id,
                summary_text=summaries.regulatory_pressure_summary.summary_text
            ))
        
        # Commit all changes
        await db.commit()
        
        return {
            "success": True, 
            "message": f"Company '{company_name}' successfully saved to database",
            "company_id": db_company.company_id,
            "cng_adoption_score": cng_adopt_score
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving company: {str(e)}")

# Debug endpoint to check saved companies
@router.get("/debug/companies", summary="List all companies in database")
async def debug_list_companies(db: AsyncSession = Depends(get_db)):
    """
    Debug endpoint to check what companies are saved in database.
    """
    try:
        # Get all companies with their metrics
        companies_query = select(Company, SustainabilityMetric).outerjoin(
            SustainabilityMetric, Company.company_id == SustainabilityMetric.company_id
        ).order_by(Company.created_at.desc())
        
        result = await db.execute(companies_query)
        companies_data = result.all()
        
        companies_list = []
        for company, metric in companies_data:
            companies_list.append({
                "company_id": company.company_id,
                "company_name": company.company_name,
                "industry": company.industry,
                "cng_adopt_score": metric.cng_adopt_score if metric else None,
                "created_at": company.created_at.isoformat() if company.created_at else None,
                "has_metrics": metric is not None
            })
        
        return {
            "success": True,
            "total_companies": len(companies_list),
            "companies": companies_list
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")

@router.get("/debug/company/{company_id}", summary="Get detailed company data")
async def debug_get_company_details(company_id: int, db: AsyncSession = Depends(get_db)):
    """
    Debug endpoint to get full company details including all related data.
    """
    try:
        from models import MetricSource, FleetSummary, EmissionsSummary, AltFuelsSummary, CleanEnergyPartnersSummary, RegulatoryPressureSummary
        
        # Get company and metrics
        company_query = select(Company, SustainabilityMetric).outerjoin(
            SustainabilityMetric, Company.company_id == SustainabilityMetric.company_id
        ).filter(Company.company_id == company_id)
        
        result = await db.execute(company_query)
        company_data = result.first()
        
        if not company_data:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company, metric = company_data
        
        # Get metric sources
        sources = []
        if metric:
            sources_query = select(MetricSource).filter(MetricSource.metric_id == metric.metric_id)
            sources_result = await db.execute(sources_query)
            sources = [
                {
                    "metric_name": source.metric_name,
                    "source_url": source.source_url,
                    "contribution_text": source.contribution_text
                }
                for source in sources_result.scalars().all()
            ]
        
        # Get summaries
        summaries = {}
        if metric:
            # Fleet summary
            fleet_query = select(FleetSummary).filter(FleetSummary.metric_id == metric.metric_id)
            fleet_result = await db.execute(fleet_query)
            fleet_summary = fleet_result.scalars().first()
            if fleet_summary:
                summaries["fleet"] = fleet_summary.summary_text
            
            # Emissions summary
            emissions_query = select(EmissionsSummary).filter(EmissionsSummary.metric_id == metric.metric_id)
            emissions_result = await db.execute(emissions_query)
            emissions_summary = emissions_result.scalars().first()
            if emissions_summary:
                summaries["emissions"] = {
                    "emissions_summary": emissions_summary.emissions_summary,
                    "emissions_goals_summary": emissions_summary.emissions_goals_summary,
                    "current_emissions": emissions_summary.current_emissions,
                    "target_year": emissions_summary.target_year,
                    "target_emissions": emissions_summary.target_emissions
                }
        
        return {
            "success": True,
            "company": {
                "company_id": company.company_id,
                "company_name": company.company_name,
                "company_summary": company.company_summary,
                "website_url": company.website_url,
                "industry": company.industry,
                "cso_linkedin_url": company.cso_linkedin_url,
                "created_at": company.created_at.isoformat() if company.created_at else None
            },
            "sustainability_metrics": {
                "metric_id": metric.metric_id if metric else None,
                "owns_cng_fleet": metric.owns_cng_fleet if metric else None,
                "cng_fleet_size_range": metric.cng_fleet_size_range if metric else None,
                "cng_fleet_size_actual": metric.cng_fleet_size_actual if metric else None,
                "total_fleet_size": metric.total_fleet_size if metric else None,
                "emission_report": metric.emission_report if metric else None,
                "emission_goals": metric.emission_goals if metric else None,
                "alt_fuels": metric.alt_fuels if metric else None,
                "clean_energy_partners": metric.clean_energy_partners if metric else None,
                "regulatory_pressure": metric.regulatory_pressure if metric else None,
                "cng_adopt_score": metric.cng_adopt_score if metric else None
            } if metric else None,
            "metric_sources": sources,
            "summaries": summaries
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error fetching company details: {str(e)}")

@router.delete("/company/{company_id}", summary="Delete company and all related data")
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a company and all its related data from the database.
    This will cascade delete:
    - SustainabilityMetric
    - All MetricSource entries
    - All Summary tables (Fleet, Emissions, AltFuels, CleanEnergyPartners, RegulatoryPressure)
    """
    try:
        # First, check if company exists
        company_query = select(Company).filter(Company.company_id == company_id)
        result = await db.execute(company_query)
        company = result.scalars().first()
        
        if not company:
            raise HTTPException(status_code=404, detail=f"Company with ID {company_id} not found")
        
        company_name = company.company_name
        
        # Delete the company (this will cascade delete all related records)
        await db.delete(company)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Company '{company_name}' (ID: {company_id}) and all related data successfully deleted",
            "deleted_company_id": company_id,
            "deleted_company_name": company_name
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")

@router.delete("/company/by-name/{company_name}", summary="Delete company by name")
async def delete_company_by_name(company_name: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a company by name and all its related data from the database.
    """
    try:
        # Find company by name (case-insensitive)
        company_query = select(Company).filter(func.lower(Company.company_name) == func.lower(company_name))
        result = await db.execute(company_query)
        company = result.scalars().first()
        
        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")
        
        company_id = company.company_id
        actual_name = company.company_name
        
        # Delete the company (this will cascade delete all related records)
        await db.delete(company)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Company '{actual_name}' (ID: {company_id}) and all related data successfully deleted",
            "deleted_company_id": company_id,
            "deleted_company_name": actual_name
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")

@router.post("/test-email/{company_id}", summary="Test email notification for saved company")
async def test_email_notification(company_id: int, db: AsyncSession = Depends(get_db)):
    """
    Test email notification functionality with a company already saved in the database.
    This endpoint is for testing email integration.
    """
    try:
        if not EMAIL_SERVICE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Email service not available")
        
        # Get company and metrics from database
        company_query = select(Company, SustainabilityMetric).outerjoin(
            SustainabilityMetric, Company.company_id == SustainabilityMetric.company_id
        ).filter(Company.company_id == company_id)
        
        result = await db.execute(company_query)
        company_data = result.first()
        
        if not company_data:
            raise HTTPException(status_code=404, detail=f"Company with ID {company_id} not found")
        
        company, metric = company_data
        
        # Convert database data to email format
        email_data = {
            "company": {
                "company_name": company.company_name,
                "company_summary": company.company_summary or "",
                "website_url": company.website_url or "",
                "industry": company.industry or ""
            },
            "sustainability_metrics": {
                "owns_cng_fleet": metric.owns_cng_fleet if metric else False,
                "cng_fleet_size_range": metric.cng_fleet_size_range if metric else 0,
                "cng_fleet_size_actual": metric.cng_fleet_size_actual if metric else 0,
                "total_fleet_size": metric.total_fleet_size if metric else 0,
                "emission_report": metric.emission_report if metric else False,
                "emission_goals": metric.emission_goals if metric else 0,
                "alt_fuels": metric.alt_fuels if metric else False,
                "clean_energy_partners": metric.clean_energy_partners if metric else False,
                "regulatory_pressure": metric.regulatory_pressure if metric else False
            },
            "overall_score": {
                "overall_score_percentage": float(metric.cng_adopt_score) if metric and metric.cng_adopt_score else 0.0
            },
            "total_pages_crawled": 8,  # Default for test
            "sources_found": 5,  # Default for test
            "test_email": True  # Flag to indicate this is a test email
        }
        
        # Send test email
        email_success = send_completion_email(company.company_name, email_data)
        
        if email_success:
            return {
                "success": True,
                "message": f"Test email sent successfully for {company.company_name}",
                "company_name": company.company_name,
                "company_id": company_id,
                "cng_adoption_score": metric.cng_adopt_score if metric else 0
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending test email: {str(e)}")