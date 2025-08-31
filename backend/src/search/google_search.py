import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union, Set, Any, Tuple
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import logging
import json
import re
from pathlib import Path
import hashlib
import time

# Load environment variables from project root
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))

# Set up logging
logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path(__file__).parent.parent.parent / 'search_cache'
CACHE_DIR.mkdir(exist_ok=True)

# Cache expiry time (24 hours)
CACHE_EXPIRY = 24 * 60 * 60

# RECURSION FIX: Add domain caching to prevent infinite loops
_domain_cache: dict[str, list[str]] = {}

# SCORING CONSTANTS - Centralized magic numbers for easy tuning
OFFICIAL_DOMAIN_BOOST = 200        # Massive bonus for company's own domain
CDN_DOMAIN_BOOST = 150             # Bonus for company domain in year searches  
ESG_INDICATOR_BOOST = 150          # ESG reports are highest priority
CDP_TCFD_BOOST = 140               # CDP/TCFD reports are very high priority
SUSTAINABILITY_BOOST = 120         # Sustainability reports are high priority
ANNUAL_REPORT_BOOST = 100          # Annual reports are good priority
RECENT_YEAR_BOOST = 40             # Bonus for recent years (2024/2023/2022)
COMPANY_MENTION_BOOST = 40         # Company mentioned in snippet
DOMAIN_SCORING_BOOST = 100         # Base company domain scoring
CDN_PATTERN_BOOST = 80             # Company CDN patterns

# SEARCH THRESHOLDS
MIN_SCORE_PRIORITY_DOMAIN = 150    # Lower threshold for company domain
MIN_SCORE_YEAR_SEARCH = 200        # Higher threshold for external sources

# RATE LIMITING
RATE_LIMIT_DELAY = 0.1             # 10 queries/sec (conservative start)

# Generate a cache key for a search query
# def get_cache_key(query: str) -> str:
#     return hashlib.md5(query.encode()).hexdigest()

# Get cached search results if they exist and are not expired
# def get_cached_results(query: str) -> Optional[Dict[str, Dict[str, str]]]:
#     cache_key = get_cache_key(query)
#     cache_file = CACHE_DIR / f"{cache_key}.json"
#     
#     if not cache_file.exists():
#         return None
#     
#     try:
#         with open(cache_file, 'r') as f:
#             data = json.load(f)
#         
#         # Check if cache is expired
#         if time.time() - data['timestamp'] > CACHE_EXPIRY:
#             logger.debug(f"Cache expired for query: {query}")
#             return None
#         
#         logger.debug(f"Using cached results for query: {query}")
#         return data['results']
#     
#     except Exception as e:
#         logger.warning(f"Failed to read cache for query '{query}': {e}")
#         return None

# Cache search results for future use
# def cache_results(query: str, results: Dict[str, Dict[str, str]]) -> None:
#     cache_key = get_cache_key(query)
#     cache_file = CACHE_DIR / f"{cache_key}.json"
#     
#     try:
#         data = {
#             'timestamp': time.time(),
#             'query': query,
#             'results': results
#         }
#         
#         with open(cache_file, 'w') as f:
#             json.dump(data, f)
#         
#         logger.debug(f"Cached {len(results)} results for query: {query}")
#     
#     except Exception as e:
#         logger.warning(f"Failed to cache results for query '{query}': {e}")

# API credentials
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
    logger.warning("Google CSE credentials missing – searches will fail.")

# Simplified query structure - Direct questions from criteria table
CRITERIA_QUESTIONS = {
    'total_truck_fleet_size': [
        '{company} total truck fleet size number of vehicles trailers tractors semi-trucks',
        '{company} how many trucks trailers semi-trucks does {company} operate',
        '{company} approximately over more than truck fleet size vehicles',
        '{company} operates owns maintains fleet trucks vehicles trailers'
    ],
    'cng_fleet': [
        '{company} does {company} currently operate any CNG vehicles',
        '{company} compressed natural gas vehicles fleet operations',
        '{company} CNG trucks natural gas vehicles currently operates',
        '{company} compressed natural gas fleet deployment operations',
        # ENHANCED: More specific current CNG fleet searches
        '{company} "currently operates" CNG trucks natural gas vehicles',
        '{company} "natural gas fleet" current operations deployment',
        '{company} CNG vehicle operations "we operate" "we have"',
        '{company} compressed natural gas truck fleet "in service"'
    ],
    'cng_fleet_size': [
        '{company} number of CNG trucks owned',
        '{company} how many CNG vehicles does {company} have',
        '{company} CNG fleet size vehicles compressed natural gas',
        '{company} number CNG trucks natural gas fleet size',
        # ENHANCED: More specific CNG-only count searches
        '{company} "CNG vehicles" "CNG trucks" "natural gas vehicles" count number',
        '{company} "operates" "owns" CNG trucks compressed natural gas vehicles',
        '{company} CNG fleet "of which" "portion" "specifically" natural gas',
        '{company} "CNG-powered" "CNG tractors" "CNG-fueled" vehicle count',
        # BALANCED: Include some broader searches that might find CNG breakdowns
        '{company} alternative fuel fleet breakdown CNG portion',
        '{company} natural gas vehicles fleet composition sustainability report'
    ],
    'emission_reporting': [
        '{company} does {company} publish an emissions report or sustainability report',
        '{company} sustainability report ESG environmental disclosure'
    ],
    'emission_goals': [
        '{company} has {company} set public GHG reduction or net-zero targets',
        '{company} climate goals carbon neutral net zero commitment'
    ],
    'alt_fuels': [
        '{company} does {company} mention use of biogas biodiesel or RNG in sustainability report',
        '{company} alternative fuels renewable natural gas biofuels'
    ],
    'clean_energy_partner': [
        '{company} partnerships with Clean Energy Fuels or Trillium or RNG providers',
        '{company} renewable energy agreements charging infrastructure partnerships',
        # ENHANCED: Specific RNG/CNG Infrastructure Providers
        '{company} partnership Clean Energy Fuels CNG stations',
        '{company} agreement Trillium CNG infrastructure',
        '{company} Shell CNG BP Natural Gas partnership',
        '{company} Neste World Energy renewable diesel partnership',
        '{company} Brightmark Archaea Energy RNG supplier agreement',
        # ENHANCED: Power Purchase Agreements and clean energy partnerships
        '{company} power purchase agreement PPA renewable energy',
        '{company} signed agreement renewable energy provider',
        '{company} partnership renewable energy solar wind',
        '{company} CNG Fuels partnership agreement supplier',
        '{company} "partnered with" clean energy renewable fuel supplier',
        '{company} renewable natural gas RNG supplier partnership agreement',
        # ENHANCED: OEMs and Technology Partners  
        '{company} partnership Cummins natural gas engines CNG trucks',
        '{company} Cummins X15N CNG engine deployment agreement',
        '{company} collaboration IVECO Westport natural gas vehicles',
        '{company} agreement Volvo Mack CNG truck deployment',
        '{company} Tesla BrightDrop GM electric vehicle partnership',
        '{company} Rivian electric delivery vehicle partnership',
        # ENHANCED: Charging/Energy Infrastructure
        '{company} charging infrastructure Electrify America ChargePoint EVgo',
        '{company} PPA agreement Orsted EDF Renewables NextEra',
        '{company} solar wind power purchase agreement renewable energy',
        # ENHANCED: Alternative Fuel Partnerships
        '{company} partnership renewable diesel biodiesel supplier',
        '{company} collaboration clean energy infrastructure provider',
        '{company} partnership alternative fuel station provider'
    ],
    'regulatory': [
        '{company} 10-K SEC filing regulatory environment compliance',
        '{company} regulatory compliance environmental logistics freight',
        '{company} SEC filing regulatory risks environmental',
        '{company} compliance regulatory oversight freight operations',
        '{company} environmental regulatory compliance annual report',
        '{company} regulatory environment business analysis',
        # ENHANCED: Specific freight regulations
        '{company} EPA SmartWay program participation member',
        '{company} CARB Low-NOx truck rule compliance',
        '{company} California Clean Fleets regulation compliance',
        '{company} EPA emissions standards trucking compliance'
    ]
}

# Priority queries for initial seeds
PRIORITY_QUERIES = [
    '{company} total truck fleet size number of vehicles trailers tractors',
    '{company} approximately over more than truck fleet size vehicles',
    '{company} operates owns maintains fleet trucks vehicles trailers',
    '{company} does {company} currently operate any CNG vehicles',
    '{company} number of CNG trucks owned',
    '{company} does {company} publish an emissions report or sustainability report',
    '{company} has {company} set public GHG reduction or net-zero targets',
    '{company} does {company} mention use of biogas biodiesel or RNG in sustainability report',
    '{company} partnerships with Clean Energy Fuels or Trillium or RNG providers',
    '{company} operating in sectors under high regulatory pressure waste freight transit'
]

# Keep basic sustainability reports for PDFs
QUERY_TEMPLATES = {
    'sustainability_reports': [
        '{company} sustainability report 2024 filetype:pdf',
        '{company} sustainability report 2023 filetype:pdf', 
        '{company} ESG report 2024 filetype:pdf',
        '{company} environmental report filetype:pdf'
    ]
}

def make_query(company: str, phrase: str, year: int = None) -> str:
    """Build a natural-language query for Google CSE"""
    q = f'{company} {phrase}'
    if year:
        q += f' {year}'
    return q

def canonicalize(url: str) -> str:
    """Canonicalize URL by removing UTM parameters and normalizing format"""
    try:
        p = urlparse(url)
        # Remove UTM and other tracking parameters
        qs = {k: v for k, v in parse_qsl(p.query) if not k.startswith(("utm_", "fbclid", "gclid"))}
        path = p.path.rstrip("/")
        return urlunparse((p.scheme, p.netloc.lower(), path, "", urlencode(sorted(qs.items())), ""))
    except Exception:
        return url

def is_official_domain(url: str, base_domains: List[str]) -> bool:
    """Check if URL is from an official company domain or subdomain"""
    try:
        host = urlparse(url).netloc.lower()
        return any(host == d or host.endswith("." + d) for d in base_domains)
    except Exception:
        return False

def search_google(company: str, phrase: str, year: int = 2025, max_pages: int = 3) -> Dict[str, Dict[str, str]]:
    """Core search function with deterministic, repeatable results using caching"""
    q = make_query(company, phrase, year)
    

    
    # If not cached, perform search
    all_results = {}
    logger.info(f"Searching with query: {q}")
    
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
        logger.error("Missing Google CSE API credentials")
        return {}
    
    # ENHANCED: Prioritize recent, official sources by searching recent years first
    recent_years = [2025, 2024, 2023]
    
    # First, try company-specific domain search for sustainability content
    if any(term in phrase.lower() for term in ['sustainability', 'esg', 'report', 'emission']):
        # Try company-specific domain search first
        company_domains = get_company_domain(company)
        if isinstance(company_domains, list) and company_domains:
            # Create a site-restricted query with recent date preference
            main_domain = company_domains[0].replace('www.', '')
            for search_year in recent_years:
                site_query = f'"{company}" {phrase} site:{main_domain}'
                logger.info(f"Trying company-specific search for {search_year}: {site_query}")
                
                company_results = _perform_search(site_query, search_year, 1)  # Just 1 page for company-specific
                if company_results:
                    all_results.update(company_results)
                    logger.info(f"Found {len(company_results)} company-specific results for {search_year}")
                    if len(all_results) >= 5:  # Stop if we have enough good results
                        break
    
    # If we didn't get enough results from company domain, do broader search with recent preference
    if len(all_results) < 5:
        for search_year in recent_years:
            # Use quoted company name for more precise matching with year filter
            enhanced_query = f'"{company}" {phrase}'
            broader_results = _perform_search(enhanced_query, search_year, max_pages)
            
            # Filter to prioritize company-relevant results with snippet analysis
            for url, data in broader_results.items():
                if url not in all_results:
                    # ENHANCED: Check if this result is company-relevant AND from reliable source
                    if _is_reliable_source(url, data):
                        all_results[url] = data
            
            # Stop if we have enough good results
            if len(all_results) >= 8:
                break
    
    logger.info(f"Total unique URLs found: {len(all_results)}")
    

    
    return all_results

def _perform_search(query: str, year: int, max_pages: int) -> Dict[str, Dict[str, str]]:
    """Helper function to perform the actual API search"""
    results = {}
    
    for i in range(max_pages):
        # Add rate limiting delay
        if i > 0:
            time.sleep(RATE_LIMIT_DELAY)
        
        params = {
            "q": query,
            "key": GOOGLE_CSE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "num": 10,
            "start": 1 + 10 * i,
            "gl": "us",
            "lr": "lang_en",
            "safe": "off"
        }
        
        # Add date restriction for recent content (simpler and more reliable)
        current_year = 2025
        if year and year >= current_year - 2:  # Only restrict if searching recent years
            params["dateRestrict"] = "y1"  # Last year of content
        
        try:
            resp = requests.get("https://www.googleapis.com/customsearch/v1", 
                              params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            if "error" in data:
                error_msg = data['error'].get('message', 'Unknown error')
                logger.error(f"Google API error: {error_msg}")
                
                # Stop on quota/auth errors, continue on other errors
                if any(err in error_msg.lower() for err in ['quota', 'limit', 'auth', 'key']):
                    logger.error("Stopping search due to quota/auth error")
                    break
                continue
            
            if "items" not in data:
                logger.warning(f"No results found for query: {query} (page {i+1})")
                continue
            
            items = data.get("items", [])
            for item in items:
                if "link" in item:
                    url = canonicalize(item["link"])
                    snippet = item.get("snippet", "")
                    title = item.get("title", "")
                    
                    # Don't store URL redundantly in the data
                    results[url] = {
                        "snippet": snippet,
                        "title": title
                    }
                    
            logger.info(f"Found {len(items)} results on page {i+1} (total: {len(results)})")
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            break  # Network errors usually mean we should stop
        except ValueError as e:
            logger.error(f"JSON decode error: {e}")
            continue  # Malformed response, try next page
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            break  # Unknown errors, better to stop
    
    return results

# def _is_company_relevant_result(url: str, data: Dict[str, str], company: str) -> bool:
#     """Check if a search result is relevant to the specific company"""
#     url_lower = url.lower()
#     title_lower = data.get('title', '').lower()
#     snippet_lower = data.get('snippet', '').lower()
#     company_lower = company.lower()
    
#     # Prioritize company's own domains
#     company_domains = get_company_domain(company)
#     if isinstance(company_domains, list):
#         for domain in company_domains:
#             if domain.replace('www.', '') in url_lower:
#                 return True
    
#     # Check if company name appears prominently in title or snippet
#     if company_lower in title_lower or company_lower in snippet_lower:
#         # Accept any substantive mention of the company
#         substantive_context = [
#             'sustainability', 'report', 'annual', 'esg', 'environment', 'fleet', 'truck', 'vehicle',
#             'cng', 'compressed natural gas', 'electric', 'emissions', 'carbon', 'partnership',
#             'order', 'purchase', 'announcement', 'news', 'press', 'industry'
#         ]
        
#         # If title or snippet contains substantive context, include it
#         if any(term in title_lower for term in substantive_context):
#             return True
#         if any(term in snippet_lower for term in substantive_context):
#             return True
        
#         # Also include news/industry sources that mention the company
#         industry_indicators = [
#             'news', 'transport', 'truck', 'fleet', 'automotive', 'energy', 'fuel',
#             'logistics', 'freight', 'delivery', 'commercial', 'industry', 'business'
#         ]
#         if any(term in url_lower for term in industry_indicators):
#             return True
    
#     # Reject results that are clearly about other companies
#     other_companies = ['microsoft', 'google', 'apple', 'meta', 'tesla', 'mercedes', 'toyota', 'volkswagen', 'bp', 'shell', 'exxon']
#     for other in other_companies:
#         if other != company_lower and other in title_lower and company_lower not in title_lower:
#             return False
    
#     return False

# Simple domain discovery for company websites
def discover_company_domain(company: str) -> List[str]:
    try:
        # Use direct API call instead of search_google to avoid recursion
        query = f'"{company}" official website'
        logger.debug(f"Discovering domains for {company}")
        
        if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
            return []
        
        # Direct API call to avoid recursion through search_google
        params = {
            "q": query,
            "key": GOOGLE_CSE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "num": 5,
            "start": 1,
            "gl": "us",
            "lr": "lang_en",
            "safe": "off"
        }
        
        resp = requests.get("https://www.googleapis.com/customsearch/v1", 
                          params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if "error" in data:
            logger.debug(f"Domain discovery API error: {data['error'].get('message', 'Unknown error')}")
            return []
        
        discovered_domains = []
        company_variations = [
            company.lower().strip(),
            company.lower().replace(' ', '').strip(),
            company.lower().replace(' ', '-').strip(),
        ]
        
        # Remove common company suffixes for better matching
        for i, variation in enumerate(company_variations):
            for suffix in ['inc', 'corp', 'corporation', 'company', 'co', 'llc', 'ltd']:
                if variation.endswith(f' {suffix}'):
                    company_variations.append(variation[:-len(f' {suffix}')].strip())
                elif variation.endswith(suffix):
                    company_variations.append(variation[:-len(suffix)].strip())
        
        for item in data.get("items", []):
            try:
                url = item.get("link", "")
                title = item.get("title", "").lower()
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Skip obvious non-company domains
                if any(skip in domain for skip in [
                    'wikipedia', 'linkedin', 'facebook', 'twitter', 'youtube',
                    'bloomberg', 'reuters', 'sec.gov', 'crunchbase', 'glassdoor',
                    'indeed', 'yelp', 'bbb.org'
                ]):
                    continue
                
                # Improved domain cleaning - only remove www prefix and extract main domain part
                domain_clean = domain.replace('www.', '')
                domain_main = domain_clean.split('.')[0]  # Get the main part before first dot
                
                # Check if this looks like a company domain
                for variation in company_variations:
                    if len(variation) > 3:
                        # Stricter matching: exact match or starts/ends with company name
                        if (variation == domain_main or 
                            domain_main.startswith(variation) or 
                            domain_main.endswith(variation) or
                            (len(variation) > 5 and variation in domain_main)):
                            
                                                         # Additional validation: check if title contains company name
                             if any(var in title for var in company_variations[:3]):
                                 # Store clean domain without www
                                 clean_domain = domain.replace('www.', '')
                                 discovered_domains.append(clean_domain)
                                 logger.debug(f"Found company domain: {clean_domain} (matched '{variation}')")
                                 break
                
            except Exception as e:
                logger.debug(f"Error processing domain discovery item: {e}")
                continue
        
        # Remove duplicates while preserving order
        unique_domains = []
        for domain in discovered_domains:
            if domain not in unique_domains:
                unique_domains.append(domain)
        
        return unique_domains[:3]
        
    except Exception as e:
        logger.debug(f"Domain discovery failed for {company}: {e}")
        return []

def get_company_domain(company: str) -> Union[str, List[str]]:
    """Get potential company domains"""
    company_clean = company.lower().strip()
    
    # Try to discover actual domains first
    discovered = discover_company_domain(company)
    if discovered:
        # Domains are already cleaned in discover_company_domain
        return discovered[:3]
    
    # Fallback to pattern generation
    company_key = company_clean.replace(' ', '').replace('.', '').replace('-', '')
    base_domains = [f"{company_key}.com"]
    
    # Add variations without common suffixes
    for suffix in ['inc', 'corp', 'corporation', 'company', 'co', 'llc', 'ltd']:
        if company_key.endswith(suffix):
            clean_key = company_key[:-len(suffix)]
            if len(clean_key) > 2:
                base_domains.append(f"{clean_key}.com")
            break
    
    return base_domains[:3]

# Simplified sustainability data collection using criteria questions
def get_company_sustainability_data(company: str, search_query: Optional[str] = None, max_pages: int = 4) -> Dict[str, List[str]]:
    results = {
        "all_unique_links": [],
        "total_truck_fleet_size": [],
        "cng_fleet": [],
        "cng_fleet_size": [],
        "emission_reporting": [],
        "emission_goals": [],
        "alt_fuels": [],
        "clean_energy_partner": [],
        "regulatory": []
    }
    
    all_links_seen = set()
    
    # If specific search query provided, use it
    if search_query:
        search_results = search_google(company, search_query, year=2025, max_pages=max_pages)
        filtered_links = filter_search_results(search_results, company)
        for link in filtered_links:
            if link not in all_links_seen:
                all_links_seen.add(link)
                results["all_unique_links"].append(link)
        return results
    
    # Use criteria questions for each criterion
    for criterion, questions in CRITERIA_QUESTIONS.items():
        criterion_links = []
        criterion_seen = set()
        
        for question_template in questions[:3]:
            query = question_template.format(company=company)
            search_phrase = query.replace(f"{company} ", "")
            
            try:
                search_results = search_google(company, search_phrase, year=2025, max_pages=2)
                filtered_links = filter_search_results(search_results, company)
                
                for link in filtered_links[:5]:
                    if link not in criterion_seen:
                        criterion_seen.add(link)
                        criterion_links.append(link)
                
                if len(criterion_links) >= 4:
                    break
                    
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                continue
        
        results[criterion] = criterion_links
        
        for link in criterion_links:
            if link not in all_links_seen:
                all_links_seen.add(link)
                results["all_unique_links"].append(link)
    
    logger.debug(f"Found {len(results['all_unique_links'])} filtered seeds for missing criteria")
    return results

# Get targeted search results for a specific criterion
def get_criterion_seeds(company: str, criterion: str, max_results: int = 5) -> List[str]:
    if criterion not in CRITERIA_QUESTIONS:
        return []
    
    all_results = []
    
    for question_template in CRITERIA_QUESTIONS[criterion][:3]:
        query = question_template.format(company=company)
        search_phrase = query.replace(f"{company} ", "")
        
        try:
            search_results = search_google(company, search_phrase, max_pages=2)
            filtered_results = filter_search_results(search_results, company)
            all_results.extend(filtered_results[:3])
            
            if len(all_results) >= max_results:
                break
        except Exception as e:
            logger.warning(f"Search failed for query '{query}': {e}")
            continue
    
    return all_results[:max_results]

# Analyze search snippets for evidence before crawling full pages
def analyze_search_snippets(search_results: Dict[str, Dict[str, str]], company: str, needed: Set[str]) -> Dict[str, 'CriteriaEvidence']:
    """AI-based analysis of Google search snippets for evidence before crawling full pages"""
    
    evidence = {}
    
    logger.info(f"Analyzing {len(search_results)} search snippets with AI for {len(needed)} criteria")
    
    # Collect all snippets into a single text for efficient batch analysis
    combined_snippets = []
    url_mapping = {}
    
    for url, result_data in search_results.items():
        snippet = result_data.get("snippet", "")
        title = result_data.get("title", "")
        
        # Skip empty snippets
        if not snippet and not title:
            continue
    
        # Combine title and snippet for analysis
        combined_text = f"Title: {title}\nSnippet: {snippet}"
        
        
        combined_snippets.append(combined_text)
        url_mapping[len(combined_snippets) - 1] = {
            'url': url,
            'title': title,
            'snippet': snippet,
            'combined_text': combined_text
        }
    
    if not combined_snippets:
        logger.info("No relevant search snippets found for analysis")
        return evidence
    
    # Batch analyze all snippets at once for efficiency
    all_snippets_text = "\n\n--- SNIPPET SEPARATOR ---\n\n".join(combined_snippets)
    
    try:
        # FIXED CIRCULAR IMPORT: Direct file import to avoid module loading issues
        import sys
        import os
        import importlib.util
        
        # Get the path to ai_criteria_analyzer.py directly
        analyzer_path = os.path.join(os.path.dirname(__file__), '..', 'scraper', 'ai_criteria_analyzer.py')
        spec = importlib.util.spec_from_file_location("ai_criteria_analyzer", analyzer_path)
        analyzer_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analyzer_module)
        
        call_openai_multi_criteria = analyzer_module.call_openai_multi_criteria
        CriteriaEvidence = analyzer_module.CriteriaEvidence
        
        # Use efficient multi-criteria AI analysis
        multi_result = call_openai_multi_criteria(all_snippets_text, needed, company)
        
        # Process results for each criterion
        for criterion in needed:
            criterion_result = multi_result.get(criterion, {})
            if criterion_result.get("criteria_found", False):
                quote = criterion_result.get("quote", "")
                evidence_score = criterion_result.get("score", 0)
                justification = criterion_result.get("justification", "")
                confidence = criterion_result.get("confidence", 0)
                potential_issues = criterion_result.get("potential_issues", "")
                extracted_number = criterion_result.get("extracted_number")
                extracted_unit = criterion_result.get("extracted_unit")
                numeric_range = criterion_result.get("numeric_range")
                
                # Find which snippet contains this evidence
                best_url = None
                best_snippet_data = None
                
                for idx, snippet_data in url_mapping.items():
                    if quote.lower() in snippet_data['combined_text'].lower():
                        best_url = snippet_data['url']
                        best_snippet_data = snippet_data
                        break
                
                # If we can't find the exact snippet, use the first one
                if not best_url and url_mapping:
                    first_snippet = list(url_mapping.values())[0]
                    best_url = first_snippet['url']
                    best_snippet_data = first_snippet
                
                if best_url and evidence_score > 0:
                    # SIMPLIFIED: Let AI handle content validation - it's much better at context understanding
                    
                    # FIXED: Create CriteriaEvidence object to match analyze_text_with_ai_batched pattern
                    
                    evidence_obj = CriteriaEvidence(
                        criterion=criterion,
                        found=True,
                        score=evidence_score,
                        evidence_text=quote,
                        justification=justification,
                        url=best_url,
                        source_type="search_snippet",
                        verified=True,  # AI verified the evidence
                        full_context=best_snippet_data['combined_text'],  # Store full snippet context
                        confidence=confidence,
                        potential_issues=potential_issues,
                        # NEW: Include extracted numeric data from AI
                        extracted_number=extracted_number,
                        extracted_unit=extracted_unit,
                        numeric_range=tuple(numeric_range) if numeric_range and isinstance(numeric_range, list) else None
                    )
                    
                    evidence[criterion] = evidence_obj
                    logger.info(f"Found {criterion} evidence in search snippet from {best_url} (score: {evidence_score})")
                    logger.info(f"  Title: {best_snippet_data['title']}")
                    logger.info(f"  Snippet: {best_snippet_data['snippet'][:150]}...")
                    
                    # Log extracted numeric data if available
                    if extracted_number is not None:
                        logger.info(f"  Extracted: {extracted_number} {extracted_unit or 'units'}")
    
    except Exception as e:
        logger.error(f"AI search snippet analysis failed: {e}")
        return evidence
    
    logger.info(f"AI snippet analysis found evidence for {len(evidence)} criteria: {list(evidence.keys())}")
    return evidence

# Get search results for missing criteria
def get_missing_criteria_seeds(company: str, needed: Set[str], max_per_criterion: int = 3) -> List[str]:
    all_seeds = []
    
    for criterion in needed:
        if criterion in CRITERIA_QUESTIONS:
            seeds = get_criterion_seeds(company, criterion, max_per_criterion)
            all_seeds.extend(seeds)
    
    # Remove duplicates
    seen = set()
    unique_seeds = []
    for seed in all_seeds:
        if seed not in seen:
            seen.add(seed)
            unique_seeds.append(seed)
    
    logger.debug(f"Found {len(unique_seeds)} filtered seeds for missing criteria")
    return unique_seeds

# Enhanced missing criteria search with more targeted approach
def get_enhanced_missing_criteria_seeds(company: str, missing_criteria: Set[str], max_per_criterion: int = 5) -> List[str]:
    """
    Get high-quality URLs for web scraping missing criteria.
    Uses exactly 2 queries per criterion and collects ALL links from first page.
    PDFs are automatically excluded. Deduplication happens in main scraper.
    """
    all_seeds = []
    
    # For each missing criterion, use enhanced search strategies
    for criterion in missing_criteria:
        criterion_seeds = []
        
        if criterion in CRITERIA_QUESTIONS:
            # Use exactly 2 queries per criterion for consistency
            base_queries = CRITERIA_QUESTIONS[criterion][:2]
            
            # Search with limited scope for efficiency
            for query_template in base_queries:
                try:
                    query = query_template.format(company=company)
                    search_phrase = query.replace(f"{company} ", "")
                    
                    # Single page search to limit API calls
                    search_results = search_google(company, search_phrase, max_pages=1)
                    
                    # Get ALL filtered URLs from first page (PDFs already excluded)
                    filtered_urls = filter_search_results(search_results, company, exclude_pdfs=True)
                    criterion_seeds.extend(filtered_urls)  # Take ALL links, not limited
                    
                except Exception as e:
                    logger.warning(f"Enhanced search failed for {criterion}: {e}")
                    continue
            
            # Add all found URLs for this criterion (no deduplication here - done in main scraper)
            if criterion_seeds:
                all_seeds.extend(criterion_seeds)
    
    # No deduplication here - it's handled in the main scraper with detailed logging
    logger.debug(f"Found {len(all_seeds)} raw seeds for {len(missing_criteria)} criteria (PDFs excluded, duplicates will be handled in main scraper)")
    return all_seeds

# Smart filtering with company relevance detection using snippets
def filter_search_results(search_results: Dict[str, Dict[str, str]], company: str, exclude_pdfs: bool = False) -> List[str]:
    """
    Enhanced filtering that considers both URLs and snippet content for relevance.
    ENHANCED: Can exclude PDFs early to avoid wasting web scraping slots.
    """
    filtered_urls = []
    company_clean = company.lower().strip()
    
    potential_domains = get_company_domain(company)
    if isinstance(potential_domains, str):
        potential_domains = [potential_domains]
    
    company_variations = [
        company_clean,
        company_clean.replace(' ', ''),
        company_clean.replace(' ', '-'),
        company_clean.replace('.', ''),
    ]
    
    # Add variations without common suffixes
    for suffix in [' inc', ' corp', ' corporation', ' company', ' co', ' llc', ' ltd']:
        if company_clean.endswith(suffix):
            clean_no_suffix = company_clean[:-len(suffix)].strip()
            company_variations.append(clean_no_suffix)
            company_variations.append(clean_no_suffix.replace(' ', ''))
            break
    
    # Remove duplicates and short variations
    company_variations = list(set([v for v in company_variations if len(v) > 2]))
    
    for url, result_data in search_results.items():
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            full_url = url.lower()
            
            # ENHANCED: Early PDF filtering for web scraping
            if exclude_pdfs and url.lower().endswith('.pdf'):
                logger.debug(f"Excluding PDF early: {url}")
                continue
            
            # Get snippet and title for content analysis
            snippet = result_data.get('snippet', '').lower()
            title = result_data.get('title', '').lower()
            combined_content = f"{title} {snippet}"
            
            company_relevance_score = 0
            
            # Check for company domain matches
            domain_matches = [d for d in potential_domains if d in domain]
            if domain_matches:
                company_relevance_score += 120
            
            # Check for company name in domain
            strong_domain_matches = [var for var in company_variations if len(var) > 4 and var in domain]
            if strong_domain_matches:
                company_relevance_score += 100
            
            # Enhanced content-based scoring using snippets and titles
            content_company_mentions = sum(1 for var in company_variations if len(var) > 3 and var in combined_content)
            if content_company_mentions > 0:
                company_relevance_score += content_company_mentions * 30
            
            # Check for company name in path
            path_matches = [var for var in company_variations if len(var) > 3 and var in path]
            if path_matches:
                company_relevance_score += 70
            
            # Check for company name anywhere in URL
            url_matches = [var for var in company_variations if len(var) > 4 and var in full_url]
            if url_matches:
                company_relevance_score += 50
            
            # EXCLUDE obviously irrelevant domains early
            irrelevant_domains = [
                'reddit.com', 'quora.com', 'stackoverflow.com', 'forums.',
                'ntassoc.com', 'commercialtruckinsurance.', 'truckinsurance.',
                'greenmatch.co.uk', 'therealtrucker.com', 'truckerspath.com',
                'bigrigchrome.com', 'truckstop.com', 'loadboard.com',
                'facebook.com', 'twitter.com', 'linkedin.com/pulse',
                'blog.', 'blogger.com', 'wordpress.com', 'medium.com',
                'indeed.com', 'glassdoor.com', 'ziprecruiter.com',
                'wikipedia.org', 'investopedia.com', 'definitions.',
                'dictionary.', 'encyclopedia.'
            ]
            
            if any(irrelevant in domain for irrelevant in irrelevant_domains):
                continue
            
            # ORIGINAL PDF filtering (only applies when exclude_pdfs=False)
            if not exclude_pdfs and url.lower().endswith('.pdf'):
                # Get company domains
                company_domains = get_company_domain(company)
                if isinstance(company_domains, str):
                    company_domains = [company_domains]
                
                # Trusted sustainability domains
                trusted_pdf_domains = ['sec.gov', 'cdp.net', 'globalreporting.org']
                
                # Check if PDF is from allowed domain
                is_allowed_pdf = False
                for allowed_domain in company_domains + trusted_pdf_domains:
                    clean_domain = allowed_domain.replace('www.', '').replace('sustainability.', '').replace('about.', '')
                    if clean_domain in domain:
                        is_allowed_pdf = True
                        break
                
                if not is_allowed_pdf:
                    continue  # Skip PDFs from unrelated domains
            
            # Boost for relevant content types
            if any(term in full_url for term in ['sustainability', 'esg', 'environmental', 'climate']):
                company_relevance_score += 15
            if any(term in full_url for term in ['fleet', 'truck', 'vehicle', 'transportation']):
                company_relevance_score += 15
            if any(term in full_url for term in ['cng', 'natural-gas', 'alternative-fuel']):
                company_relevance_score += 20
            
            # Boost for trusted sources
            trusted_sources = ['sec.gov', 'reuters.com', 'bloomberg.com', 'businesswire.com']
            if any(trusted in domain for trusted in trusted_sources):
                if any(var in combined_content for var in company_variations if len(var) > 2):
                    company_relevance_score += 60
            
            # RAISE the minimum threshold to be more selective
            if company_relevance_score < 25:  # Raised from 15 to 25
                continue
            
            # Exclude obvious non-corporate content (expanded list)
            excluded_patterns = [
                '/dp/', '/product/', '/shop/', '/buy/',
                '/gp/', '/ASIN/', '/asin/',  # Amazon product pages
                '/cart/', '/checkout/', '/wishlist/',
                '/review/', '/customer-reviews/'
            ]
            if any(pattern in full_url for pattern in excluded_patterns):
                continue
            
            # Check for ASIN pattern (10 alphanumeric characters)
            asin_pattern = r'/[A-Z0-9]{10}(?:/|$)'
            if re.search(asin_pattern, path.upper()):
                continue
            
            # Boost for PDFs and high-value content (only when not excluding PDFs)
            quality_score = company_relevance_score
            if not exclude_pdfs and url.lower().endswith('.pdf'):
                quality_score += 20
            
            # Apply quality threshold
            if quality_score >= 25:
                filtered_urls.append(url)
                
        except Exception as e:
            logger.warning(f"Error filtering URL {url}: {e}")
            continue
    
    # Sort by estimated quality (longer URLs often have more specific content)
    filtered_urls.sort(key=lambda x: len(x), reverse=True)
    
    return filtered_urls

# Enhanced sustainability report search with scoring
def get_sustainability_reports(company: str, max_results: int = 10) -> List[str]:
    all_candidates = []  # Store (score, url, reason) tuples
    
    # ENHANCED: Get company domains including CDN subdomains
    company_domains = get_company_domain(company)
    main_domains = []
    cdn_patterns = []
    
    # Fix: Handle both string and list returns from get_company_domain
    if isinstance(company_domains, str):
        company_domains = [company_domains]
    
    if isinstance(company_domains, list) and company_domains:
        for domain in company_domains:
            clean_domain = domain.replace('www.', '')
            main_domains.append(clean_domain)
            # Add common CDN patterns for this domain
            cdn_patterns.extend([
                f"cdn.{clean_domain}",
                f"assets.{clean_domain}",
                f"files.{clean_domain}",
                f"docs.{clean_domain}",
                f"investor.{clean_domain}",
                f"annualreport.{clean_domain}",
                f"sustainability.{clean_domain}",
                f"impact.{clean_domain}",
                f"www.{clean_domain}"
            ])
    
    # PRIORITY 1: Company's own domain with comprehensive search patterns
    priority_queries = []
    
    # Use discovered domains for ALL companies (no special cases)
    for domain in main_domains + cdn_patterns:
        priority_queries.extend([
            f'site:{domain} sustainability report filetype:pdf',
            f'site:{domain} ESG report filetype:pdf',
            f'site:{domain} environmental report filetype:pdf',
            f'site:{domain} annual report sustainability filetype:pdf',
            f'site:{domain} corporate responsibility report filetype:pdf',
            f'site:{domain} environmental impact report filetype:pdf',
            f'site:{domain} climate report filetype:pdf'
        ])
    
    # Add path-specific searches for common sustainability page patterns
    if main_domains:
        main_domain = main_domains[0]  # Use the primary domain
        priority_queries.extend([
            f'site:{main_domain}/sustainability filetype:pdf',
            f'site:{main_domain}/impact filetype:pdf',
            f'site:{main_domain}/esg filetype:pdf',
            f'site:{main_domain}/corporate-responsibility filetype:pdf'
        ])
    
    # Search priority company domain queries first
    for i, query in enumerate(priority_queries[:8]):  # Limit to avoid rate limits
        try:
            # Add delay between requests to avoid rate limiting
            if i > 0:
                time.sleep(RATE_LIMIT_DELAY)  # Configurable delay between requests
            
            logger.info(f"Priority search: {query}")
            results = _perform_search(query, 2024, 1)
            
            if not results:
                continue
                
            for url, data in list(results.items())[:3]:  # Top 3 per query
                try:
                    score, reason = score_sustainability_report_relevance(url, data.get('title', ''), data.get('snippet', ''), company)
                    
                    # MASSIVE BONUS for company's own domain
                    if is_official_domain(url, main_domains):
                        score += OFFICIAL_DOMAIN_BOOST  # Huge boost for official domain
                        reason = f"OFFICIAL DOMAIN: {reason}"
                    
                    if score > MIN_SCORE_PRIORITY_DOMAIN:  # Lower threshold for company domain
                        all_candidates.append((score, url, reason))
                        logger.info(f"Priority candidate: {url} (score: {score})")
                except Exception as e:
                    logger.warning(f"Error scoring URL {url}: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Priority search failed for '{query}': {e}")
    
    # PRIORITY 2: Recent years with company name
    for year in [2024, 2023, 2022]:
        for report_type in ["sustainability report", "ESG report", "annual report sustainability", "environmental report"]:
            query = f'"{company}" {report_type} {year} filetype:pdf'
            logger.info(f"Trying recent year search: {query}")
            try:
                # Add delay between requests
                time.sleep(RATE_LIMIT_DELAY)
                
                results = _perform_search(query, year, 1)
                if not results:
                    continue
                    
                for url, data in list(results.items())[:3]:
                    try:
                        score, reason = score_sustainability_report_relevance(url, data.get('title', ''), data.get('snippet', ''), company)
                        
                        # BONUS for company's own domain
                        if is_official_domain(url, main_domains):
                            score += CDN_DOMAIN_BOOST
                            reason = f"OFFICIAL DOMAIN: {reason}"
                        
                        if score > MIN_SCORE_YEAR_SEARCH:
                            all_candidates.append((score, url, reason))
                            logger.info(f"Found {year} candidate: {url} (score: {score})")
                    except Exception as e:
                        logger.warning(f"Error scoring URL {url}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Year search failed for {query}: {e}")
                
    # Remove duplicates and sort by score
    seen_urls = set()
    unique_candidates = []
    for score, url, reason in all_candidates:
        canonical_url = canonicalize(url)
        if canonical_url not in seen_urls:
            seen_urls.add(canonical_url)
            # Store canonical URL for consistency
            unique_candidates.append((score, canonical_url, reason))
    
    # Sort by score (highest first) 
    unique_candidates.sort(key=lambda x: x[0], reverse=True)
    
    logger.info(f"Sustainability report candidates for {company}:")
    for score, url, reason in unique_candidates[:max_results]:
        logger.info(f"  Score {score}: {url[:50]}...")
        logger.info(f"  Score {score}: {url} - {reason}")
    
    # Return top URLs
    return [url for score, url, reason in unique_candidates[:max_results]]

def score_sustainability_report_relevance(url: str, title: str, snippet: str, company: str, analyze_content: bool = True) -> Tuple[int, str]:
    """Score how likely a PDF is to be the actual company's sustainability report."""
    score = 0
    reasons = []
    company_lower = company.lower()
    url_lower = url.lower()
    title_lower = title.lower()
    snippet_lower = snippet.lower()
    
    # ENHANCED: Generate company name variations for better matching
    company_variations = [
        company_lower,
        company_lower.replace(' ', ''),
        company_lower.replace(' ', '-'),
    ]
    
    # Add variations without common suffixes (like "Logistics" from "XPO Logistics")
    for suffix in [' inc', ' corp', ' corporation', ' company', ' co', ' llc', ' ltd', ' logistics']:
        if company_lower.endswith(suffix):
            clean_no_suffix = company_lower[:-len(suffix)].strip()
            if len(clean_no_suffix) > 2:
                company_variations.append(clean_no_suffix)
                company_variations.append(clean_no_suffix.replace(' ', ''))
            break
    
    # Add first word for cases like "XPO" from "XPO Logistics"
    first_word = company_lower.split()[0] if ' ' in company_lower else company_lower
    if len(first_word) > 2:
        company_variations.append(first_word)
    
    # IMMEDIATE REJECTION: Obviously irrelevant content
    immediate_rejections = [
        # Academic/University content
        '.edu/', 'university', 'college', 'academic', 'research.pdf', 'thesis.pdf',
        # Service guides and operational manuals  
        'service-guide', 'user-guide', 'manual.pdf', 'instructions.pdf', 'handbook.pdf',
        # E-commerce and marketing materials  
        'ecommerce-ebook', 'marketing-guide', 'sales-guide', 'product-catalog',
        # Regional service materials
        'service-guide-en-', 'guide-en-', '-service-guide', 'regional-guide',
        # Third-party presentations and reports about the company (not by the company)
        'analyst-report', 'third-party-analysis', 'industry-report',
        # Financial presentations (unless annual reports)
        'earnings-presentation', 'investor-presentation', 'quarterly-presentation'
    ]
    
    for rejection_pattern in immediate_rejections:
        if rejection_pattern in url_lower or rejection_pattern in title_lower:
            return 0, f"rejected - {rejection_pattern} content"
    
    # ENHANCED: Check for company domain OR CDN hosting with company path
    company_domains = get_company_domain(company)
    actual_company_domain = False
    
    if isinstance(company_domains, list):
        for domain in company_domains:
            clean_domain = domain.replace('www.', '').replace('sustainability.', '').replace('about.', '')
            
            # Check main domain OR CDN patterns
            if clean_domain in url_lower:
                actual_company_domain = True
                score += DOMAIN_SCORING_BOOST
                reasons.append(f"hosted on company domain ({clean_domain})")
                break
            
            # Check CDN patterns for this domain
            cdn_patterns = [f"cdn.{clean_domain}", f"{clean_domain}/cdn", f"assets.{clean_domain}"]
            for pattern in cdn_patterns:
                if pattern in url_lower:
                    actual_company_domain = True
                    score += CDN_PATTERN_BOOST  # Slightly lower than main domain but still high
                    reasons.append(f"hosted on company CDN ({pattern})")
                    break
            
            if actual_company_domain:
                break
    
    # ENHANCED: Company name matching in title with variations
    company_in_title = False
    for variation in company_variations:
        if len(variation) > 2 and variation in title_lower:
            company_in_title = True
            break
    
    if company_in_title:
        # Check if it's actually sustainability content
        sustainability_indicators = ['sustainability', 'esg', 'environmental', 'climate', 'annual report', 'cdp', 'tcfd']
        if any(indicator in title_lower for indicator in sustainability_indicators):
            score += 80
            reasons.append("company name in sustainability title")
        else:
            # Company name but not sustainability - still give some score
            score += 40
            reasons.append("company name in title")
    else:
        # RELAXED: If no company name in title but hosted on company domain/CDN, still ok
        if actual_company_domain:
            score += 20
            reasons.append("on company domain but no name in title")
        else:
            # External hosting without company name in title - big penalty
            score -= 30
            reasons.append("external hosting without company name in title")
    
    # BOOST: High-priority sustainability content types
    high_priority_indicators = [
        'esg report', 'esg_report', 'sustainability report', 'sustainability_report',
        'cdp', 'tcfd', 'gri report', 'annual report', 'corporate responsibility'
    ]
    
    for indicator in high_priority_indicators:
        if indicator in title_lower or indicator in url_lower:
            if indicator in ['esg', 'esg report', 'esg_report']:
                score += ESG_INDICATOR_BOOST  # ESG reports are highest priority
                reasons.append("ESG report - highest priority")
            elif indicator in ['cdp', 'tcfd']:
                score += CDP_TCFD_BOOST  # CDP/TCFD reports are very high priority
                reasons.append("CDP/TCFD report - very high priority")
            elif 'sustainability' in indicator:
                score += SUSTAINABILITY_BOOST  # Sustainability reports are high priority
                reasons.append("sustainability report - high priority")
            elif 'annual report' in indicator:
                score += ANNUAL_REPORT_BOOST  # Annual reports are good priority
                reasons.append("annual report - good priority")
            break
    
    # ENHANCED: Validate the content is actually about the company using snippet with variations
    if snippet_lower:
        company_mentioned_in_snippet = False
        for variation in company_variations:
            if len(variation) > 2:
                # Use word boundaries for better matching
                pattern = r'\b' + re.escape(variation) + r'\b'
                if re.search(pattern, snippet_lower, re.IGNORECASE):
                    company_mentioned_in_snippet = True
                    break
        
        if company_mentioned_in_snippet:
            score += COMPANY_MENTION_BOOST
            reasons.append("company mentioned in snippet")
        else:
            # RELAXED: If hosted on company domain but no mention in snippet, smaller penalty
            if actual_company_domain:
                score -= 10  # Small penalty instead of -40
                reasons.append("company domain but no snippet mention")
            else:
                score -= 40
                reasons.append("external hosting without company mention in snippet")
    
    # Recent year gets bonus
    for year in ['2024', '2023', '2022']:
        if year in title_lower or year in url_lower:
            score += RECENT_YEAR_BOOST
            reasons.append(f"recent year ({year})")
            break
    
    # RELAXED: Additional validation for external hosting
    if not actual_company_domain:
        # Check if the title/URL contains strong company indicators
        strong_company_indicators = []
        for variation in company_variations:
            if len(variation) > 3:
                strong_company_indicators.extend([
                    f"{variation} sustainability",
                    f"{variation} annual report", 
                    f"{variation} esg report",
                    f"{variation} environmental report",
                    f"{variation} cdp",
                    f"{variation} tcfd"
                ])
        
        has_strong_indicator = any(indicator in title_lower for indicator in strong_company_indicators)
        if not has_strong_indicator:
            score -= 20  # Reduced penalty from -30 to -20
            reasons.append("external hosting without strong company indicator")
    
    reason_text = "; ".join(reasons) if reasons else "no specific indicators"
    return max(0, score), reason_text

def _is_reliable_source(url: str, data: Dict[str, str]) -> bool:
    """Filter out unreliable sources like Reddit, forums, old articles, and anecdotal content"""
    url_lower = url.lower()
    title_lower = data.get('title', '').lower()
    snippet_lower = data.get('snippet', '').lower()
    
    # REJECT: Social media and forums (anecdotal)
    unreliable_domains = [
        'reddit.com', 'facebook.com', 'twitter.com', 'linkedin.com/pulse',
        'quora.com', 'stackoverflow.com', 'forums.', 'discussion.',
        'medium.com/@', 'blog.', 'blogger.com', 'wordpress.com',
        'youtube.com', 'tiktok.com', 'instagram.com'
    ]
    
    if any(domain in url_lower for domain in unreliable_domains):
        logger.debug(f"Rejected unreliable domain: {url}")
        return False
    
    # FLAG: Very old sources (2021 and earlier) but don't reject - let user decide
    very_old_year_patterns = ['2021', '2020', '2019', '2018']
    if any(year in title_lower or year in snippet_lower for year in very_old_year_patterns):
        # Log for transparency but don't reject
        logger.info(f"Old source flagged (user can evaluate): {url}")
        # Continue processing - don't return False
    
    # REJECT: Generic marketing content without substance
    marketing_indicators = [
        'learn more about', 'discover our', 'explore our', 'join our network',
        'sign up', 'book now', 'get started', 'find out more'
    ]
    
    if any(indicator in snippet_lower for indicator in marketing_indicators):
        # Unless it's from official company domain with specific data
        company_data_indicators = ['report', 'data', 'emissions', 'fleet', 'vehicles', 'partnership']
        if not any(indicator in snippet_lower for indicator in company_data_indicators):
            logger.debug(f"Rejected marketing content: {url}")
            return False
    
    # PRIORITIZE: Official sources
    trusted_domains = [
        '.gov', 'sec.gov', 'epa.gov', 'carb.ca.gov',  # Government
        'bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com',  # Financial news
        'businesswire.com', 'prnewswire.com',  # Press releases
        'fleetowner.com', 'ttnews.com', 'freightwaves.com'  # Industry trade
    ]
    
    is_trusted = any(domain in url_lower for domain in trusted_domains)
    
    # REQUIRE: Substantive content indicators
    substantive_indicators = [
        'operates', 'deployed', 'purchased', 'announced', 'reported', 'disclosed',
        'compliance', 'regulation', 'emissions', 'fleet', 'vehicles', 'partnership',
        'agreement', 'contract', 'investment', 'million', 'billion'
    ]
    
    has_substance = any(indicator in snippet_lower for indicator in substantive_indicators)
    
    # Accept if trusted domain OR has substantive content
    if is_trusted or has_substance:
        return True
    
    logger.debug(f"Rejected low-quality source: {url}")
    return False

