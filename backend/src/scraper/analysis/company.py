"""Company sustainability analysis and validation functions."""

import re
import logging
from typing import List, Union

# Import required modules
from ...search.google_search import get_company_domain

logger = logging.getLogger(__name__)


def get_dynamic_page_limit(missing_criteria_count: int) -> int:
    """Scale crawling effort based on how many criteria we still need"""
    if missing_criteria_count <= 1:
        return 1  # Just 1 page for final criterion
    elif missing_criteria_count <= 2:
        return 2  # 2 pages for a couple missing
    else:
        return 3  # Max 3 pages when many missing


def validate_pdf_ownership(pdf_url: str, pdf_text: str, company: str) -> bool:
    """
    Enhanced validation to ensure PDF is actually published BY the company, not ABOUT the company.
    
    Returns True only if the PDF is very likely to be the company's own publication.
    """
    url_lower = pdf_url.lower()
    company_lower = company.lower()
    
    # IMMEDIATE ACCEPTANCE: Always trust company domains and SEC filings
    company_domains = get_company_domain(company)
    
    # ENHANCED: Check both discovered domains AND URL-based company indicators
    domain_match = False
    if isinstance(company_domains, list):
        for domain in company_domains:
            clean_domain = domain.replace('www.', '').replace('investor.', '').replace('ir.', '')
            if clean_domain in url_lower:
                domain_match = True
                logger.info(f"PDF ownership: Domain match found ({clean_domain})")
                break
    
    # ENHANCED: Check for company-specific URL patterns (like XPO using "xpo.com")
    company_variations = [
        company_lower,
        company_lower.replace(' ', ''),
        company_lower.replace(' ', '-'),
        company_lower.replace('.', ''),
    ]
    
    # Add variations without common suffixes
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
    
    # Check for company indicators in URL (more flexible)
    url_company_match = False
    for variation in company_variations:
        if len(variation) > 2 and variation in url_lower:
            url_company_match = True
            logger.info(f"PDF ownership: URL company match found ({variation})")
            break
    
    # ENHANCED: CDN and file hosting patterns - more permissive
    cdn_hosting_patterns = [
        '/cdn/', '/files/', '/assets/', '/static/', '/docs/', '/content/',
        'cdn.', 'files.', 'assets.', 'docs.', 'static.'
    ]
    
    is_cdn_hosted = any(pattern in url_lower for pattern in cdn_hosting_patterns)
    
    # ENHANCED: Sustainability report file naming patterns
    sustainability_file_patterns = [
        'sustainability_report', 'sustainability-report', 'esg_report', 'esg-report',
        'annual_report', 'annual-report', 'csr_report', 'csr-report',
        'environmental_report', 'environmental-report', 'climate_report',
        'sustainability_update', 'sustainability-update'
    ]
    
    has_sustainability_filename = any(pattern in url_lower for pattern in sustainability_file_patterns)
    
    # IMMEDIATE ACCEPTANCE: Company domain or URL match with sustainability content
    if (domain_match or url_company_match) and (has_sustainability_filename or is_cdn_hosted):
        logger.info("PDF ownership: ACCEPTED - Company domain/URL with sustainability content")
        return True
    
    # IMMEDIATE ACCEPTANCE: SEC filings
    if 'sec.gov' in url_lower:
        logger.info("PDF ownership: ACCEPTED - SEC filing")
        return True
    
    # ENHANCED: Check PDF content for company ownership indicators
    if pdf_text:
        text_lower = pdf_text.lower()
        
        # Look for copyright and ownership statements
        ownership_indicators = [
            f'© {company_lower}',
            f'copyright {company_lower}',
            f'{company_lower}, inc.',
            f'{company_lower} corporation',
            f'{company_lower} limited',
            f'{company_lower} llc'
        ]
        
        # Look for variations in ownership statements
        for variation in company_variations:
            if len(variation) > 2:
                ownership_indicators.extend([
                    f'© {variation}',
                    f'copyright {variation}',
                    f'{variation}, inc.',
                    f'{variation} corporation',
                    f'published by {variation}',
                    f'prepared by {variation}'
                ])
        
        has_ownership = any(indicator in text_lower for indicator in ownership_indicators)
        
        # Check for company mentions in title/header area (first 500 chars)
        header_area = text_lower[:500]
        company_in_header = any(variation in header_area for variation in company_variations if len(variation) > 2)
        
        # ACCEPTANCE: Strong content ownership indicators
        if has_ownership and company_in_header:
            logger.info("PDF ownership: ACCEPTED - Strong ownership indicators in content")
            return True
        
        # ACCEPTANCE: CDN-hosted with company mentions and sustainability keywords
        if is_cdn_hosted and company_in_header:
            sustainability_keywords = ['sustainability', 'esg', 'environmental', 'climate', 'emissions']
            has_sustainability_content = any(keyword in text_lower[:1000] for keyword in sustainability_keywords)
            
            if has_sustainability_content:
                logger.info("PDF ownership: ACCEPTED - CDN-hosted with company mentions and sustainability content")
                return True
        
        # ENHANCED: More flexible validation for official reports
        if has_sustainability_filename or url_company_match:
            # Count company mentions more flexibly
            company_mention_count = 0
            for variation in company_variations:
                if len(variation) > 2:
                    # Use word boundaries for accurate counting
                    pattern = r'\b' + re.escape(variation) + r'\b'
                    matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                    company_mention_count = max(company_mention_count, matches)
            
            # More lenient threshold for CDN-hosted sustainability reports
            required_mentions = 1 if is_cdn_hosted else 2
            
            if company_mention_count >= required_mentions:
                logger.info(f"PDF ownership: ACCEPTED - Sufficient company mentions ({company_mention_count}/{required_mentions})")
                return True
    
    # REJECTION: Third-party or insufficient indicators
    logger.info("PDF ownership: REJECTED - Insufficient ownership indicators")
    return False


 