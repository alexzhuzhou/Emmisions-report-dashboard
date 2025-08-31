"""Web crawling and content fetching utilities."""

import time
import logging
from typing import Set
from urllib.parse import urlparse
from ...search.google_search import get_company_domain

logger = logging.getLogger(__name__)

# Asset extensions to ignore (keep minimal for basic filtering)
ASSET_EXT = {
    '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', 
    '.woff', '.woff2', '.ttf', '.ico', '.svg', '.map',
    '.webp', '.mp4', '.webm', '.mp3', '.wav'
}


def should_crawl(url: str, needed: Set[str], company: str) -> bool:
    """Determine if a URL is worth crawling based on content relevance and filtering rules"""
    url_low = url.lower()
    
    # Special handling for PDFs with domain + content filtering
    if url_low.endswith('.pdf'):
        return should_crawl_pdf(url, company)
        
    # Skip non-http(s) URLs
    if not url_low.startswith(('http://', 'https://')):
        return False

    # Skip asset files
    if any(url_low.endswith(ext) for ext in ASSET_EXT if ext != '.pdf'):
        return False

    # Allow news/industry sites if we still need REGULATORY
    REG_NEWS = (
        "fleetowner.com", "freightwaves.com", "ttnews.com", "truckinginfo.com",
        "reuters.com", "bloomberg.com", "wsj.com", "ft.com"
    )
    if needed <= {"regulatory"} and any(dom in url_low for dom in REG_NEWS):
        return True

    # Allow high-value paths
    high_value_paths = [
        '/sustainability', '/news/sustainability', '/investor', '/ir/', '/filings',
        '/annual-report', '/esg', '/corporate-responsibility', '/about-us',
        '/fleet', '/transportation', '/newsroom', '/media', '/item1/', '/item-1/', '/ixviewer/'
    ]
    
    if any(path in url_low for path in high_value_paths):
        return True

    # Fallback to AI-friendly domain trust logic
    if not is_trusted_domain_ai(url, company):
        return False

    return True


def should_crawl_pdf(url: str, company: str) -> bool:
    """Domain-based filtering for PDFs to prevent wrong-company reports."""
    # Get allowed domains for this company
    allowed_domains = get_company_domain(company)
    if isinstance(allowed_domains, str):
        allowed_domains = [allowed_domains]
    
    # Add trusted sustainability/reporting domains
    trusted_domains = [
        'sec.gov', 'edgar.sec.gov',           # SEC filings
        'cdp.net',                            # CDP reports  
        'globalreporting.org',                # GRI reports
        'sustainabledevelopment.report'       # UN SDG reports
    ]
    
    # Check if PDF is from allowed domain
    try:
        host = urlparse(url).netloc.lower()
        
        # Check company domains
        for domain in allowed_domains:
            clean_domain = domain.replace('www.', '').replace('sustainability.', '').replace('about.', '')
            if clean_domain in host:
                logger.debug(f"[PDF ALLOW] {url} - company domain match: {clean_domain}")
                return True
        
        # Check trusted domains
        for trusted in trusted_domains:
            if trusted in host:
                logger.debug(f"[PDF ALLOW] {url} - trusted domain: {trusted}")
                return True
                
        logger.debug(f"[PDF REJECT] {url} - not from allowed domain (host: {host})")
        return False
        
    except Exception as e:
        logger.warning(f"Failed to parse PDF URL {url}: {e}")
        return False


def safe_get_page_content(browser, url: str, timeout: int = 20000, max_retries: int = 3, verbose: bool = False):
    """
    OPTIMIZED: Safely retrieve webpage content reusing existing browser context.
    Fixed to avoid expensive context creation on every call.
    """
    try:
        domain = urlparse(url).netloc
    except:
        domain = url
        
    for attempt in range(max_retries):
        try:
            # OPTIMIZED: Reuse existing browser context instead of creating new ones
            if hasattr(browser, 'contexts') and browser.contexts:
                context = browser.contexts[0]  # Reuse existing context
            else:
                context = browser.new_context()
            
            if hasattr(context, 'pages') and context.pages:
                page = context.pages[0]  # Reuse existing page
            else:
                page = context.new_page()
            
            # Navigate to URL with timeout
            response = page.goto(url, timeout=timeout, wait_until='domcontentloaded')
            
            if response and response.status < 400:
                content = page.content()
                if len(content.strip()) > 100:  # Ensure we got meaningful content
                    return content
                    
        except Exception as e:
            if verbose:
                logger.warning(f"Attempt {attempt + 1} failed for {domain}: {e}")
            if attempt == max_retries - 1:
                if verbose:
                    logger.error(f"All attempts failed for {domain}")
                return None
            time.sleep(1 * (attempt + 1))  # Progressive backoff
    
    return None


def is_trusted_domain_ai(url: str, company: str) -> bool:
    """Simple AI-friendly domain trust check"""
    try:
        domain = urlparse(url).netloc.lower()
        
        # Company domain check
        company_domains = get_company_domain(company)
        if isinstance(company_domains, list):
            for comp_domain in company_domains:
                if comp_domain.replace('www.', '') in domain:
                    return True
        
        # High-value domains
        trusted_patterns = [
            'sustainability', 'esg', 'investor', 'annual-report',
            'sec.gov', 'cdp.net', 'globalreporting.org'
        ]
        
        return any(pattern in domain for pattern in trusted_patterns)
    except Exception as e:
        logger.warning(f"Error occurred: {e}")
        return False 