import sys
import os
import time
import logging
import heapq
import random
import json
from typing import Dict, Set, Optional, List, Any, Tuple
from urllib.parse import urlparse, urljoin, urldefrag
from pathlib import Path
import re

# Windows Playwright fix
import asyncio
if sys.platform == "win32":
    # Set the event loop policy for Windows to avoid subprocess issues
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Playwright and web scraping imports
from playwright.sync_api import sync_playwright
import trafilatura
import requests
from bs4 import BeautifulSoup

# Add paths for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import AI analysis functions  
# (Legacy conversion removed - now using modern CriteriaEvidence format only)

# Import search and analysis functions
from ..search.google_search import (
    search_google,
    get_enhanced_missing_criteria_seeds,
    get_company_domain,
    filter_search_results,
    get_sustainability_reports,
    analyze_search_snippets,  # REVERT: Use original working version
    CRITERIA_QUESTIONS  # Add this import
)

# Import efficient AI analysis functions
from .ai_criteria_analyzer import (
    analyze_text_with_ai_batched,
    CriteriaEvidence,
    should_replace_evidence_ai
)

# Import scraping utilities and scoring
from .utils.pdf import extract_pdf_content
from .utils.html import html_to_clean_text
from .crawler.fetch import should_crawl, should_crawl_pdf, safe_get_page_content, is_trusted_domain_ai
from .analysis.company import validate_pdf_ownership
from .ai_scorecard_integration import score_url  # URL scoring function

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration constants - OPTIMIZED FOR PRODUCTION
MAX_PDFS = 3  # Increased from 2 → 3 (most companies have 1-3 key reports)
MAX_PDF_CHARS = 200000  # Increased from 120k → 200k (full sustainability reports)
MAX_AI_BATCHES = 5  # Increased from 3 → 5 (thorough analysis without waste)
PLAYWRIGHT_TIMEOUT = 12000  # Increased from 8s → 12s (corporate sites can be slow)
OPENAI_TIMEOUT = 30  # 30 seconds timeout for OpenAI API calls (network only)
FIRST_CHUNK_CHARS = 25000  # Increased from 20k → 25k (better executive summary capture)

# Page limits for web scraping (replacing timeout-based approach)
MAX_WEB_PAGES_PER_PHASE = 8  # Increased from 5 to 8 for more comprehensive web scraping
MAX_CRAWL_PAGES = 12  # Increased from 8 to 12 for deeper crawling
MAX_SEARCH_PAGES_PER_CRITERION = 3  # Increased from 2 to 3 for more search depth

# JavaScript for link extraction
ALL_LINKS_JS = "Array.from(document.querySelectorAll('a[href]')).map(a => a.href)"



# All criteria that can be analyzed
ALL_CRITERIA = {
    'total_truck_fleet_size',
    'cng_fleet', 
    'cng_fleet_size',
    'emission_reporting',
    'emission_goals',
    'alt_fuels',
    'clean_energy_partner',
    'regulatory'
}

# Define company industry detection and criteria filtering
def get_relevant_criteria_for_company(company: str, all_criteria: Set[str]) -> Tuple[Set[str], Set[str]]:
    """
    Return all criteria as relevant - no industry-based filtering.
    Let the AI analyze everything and report "not found" when appropriate.
    Returns (relevant_criteria, na_criteria)
    """
    # No filtering - analyze all criteria for all companies
    return all_criteria, set()

def is_mostly_javascript(text: str) -> bool:
    """
    Detect if content is mostly JavaScript code rather than readable text.
    Returns True if content appears to be primarily JavaScript.
    """
    if not text or len(text.strip()) < 50:
        return False
    
    text_lower = text.lower()
    
    # JavaScript patterns that indicate script content
    js_patterns = [
        'function(',
        'window.',
        'document.',
        'var ',
        'let ',
        'const ',
        'return ',
        '=>',
        '(function',
        'function(){',
        'function (',
        '.prototype.',
        '&&',
        '||',
        'null',
        'undefined',
        'typeof',
        'addEventListener',
        'querySelector',
        'getElementById',
        'createElement',
        'appendChild',
        'removeChild',
        'innerHTML',
        'eval(',
        'new Date',
        'new Array',
        'new Object',
        'console.log',
        'alert(',
        'parseInt(',
        'parseFloat(',
        'isNaN(',
        'setTimeout(',
        'setInterval(',
        'clearTimeout(',
        'clearInterval(',
        'location.href',
        'window.location',
        'document.ready',
        'jquery',
        'ajax',
        'json',
        '.push(',
        '.pop(',
        '.shift(',
        '.unshift(',
        '.splice(',
        '.slice(',
        '.length',
        '.indexOf(',
        '.charAt(',
        '.substring(',
        '.substr(',
        '.replace(',
        '.split(',
        '.join(',
        '.toLowerCase(',
        '.toUpperCase(',
        '.trim(',
        'if(',
        'else{',
        'for(',
        'while(',
        'switch(',
        'case ',
        'break;',
        'continue;',
        'try{',
        'catch(',
        'throw ',
        'finally{',
        'this.',
        'self.',
        'arguments',
        'callee',
        'caller',
        'apply(',
        'call(',
        'bind(',
        'prototype',
        '__proto__',
        'constructor',
        'hasOwnProperty',
        'instanceof',
        'typeof',
        'boolean',
        'number',
        'string',
        'object',
        'symbol',
        'bigint',
        'require(',
        'import ',
        'export ',
        'module.exports',
        'exports.',
        'webpack',
        'babel',
        'minified',
        'compressed',
        'obfuscated',
        # Analytics and tracking patterns
        'analytics',
        'tracking',
        'gtag',
        'ga(',
        'google',
        'facebook',
        'twitter',
        'linkedin',
        'pinterest',
        'instagram',
        'youtube',
        'tiktok',
        'snapchat',
        'boomerang',
        'hotjar',
        'mixpanel',
        'segment',
        'amplitude',
        'datadog',
        'newrelic',
        'sentry',
        'bugsnag',
        'rollbar',
        'logrocket',
        'fullstory',
        'smartlook',
        'mouseflow',
        'crazyegg',
        'kissmetrics',
        'intercom',
        'zendesk',
        'drift',
        'olark',
        'livechat',
        'tawk',
        'freshchat',
        'uservoice',
        'usabilla',
        'qualtrics',
        'surveymonkey',
        'typeform',
        'mailchimp',
        'hubspot',
        'marketo',
        'pardot',
        'eloqua',
        'salesforce',
        'pipedrive',
        'stripe',
        'paypal',
        'square',
        'braintree',
        'authorize',
        'worldpay',
        'adyen',
        'checkout',
        'payment',
        'billing',
        'subscription'
    ]
    
    # Count JavaScript patterns
    js_pattern_count = 0
    for pattern in js_patterns:
        if pattern in text_lower:
            js_pattern_count += text_lower.count(pattern)
    
    # Calculate ratios
    total_words = len(text.split())
    js_ratio = js_pattern_count / max(total_words, 1)
    
    # Check for common JavaScript syntax patterns
    syntax_patterns = [
        '{',
        '}',
        '(',
        ')',
        '[',
        ']',
        ';',
        '=',
        '!',
        '&',
        '|',
        '<',
        '>',
        '?',
        ':',
        '+',
        '-',
        '*',
        '/',
        '%',
        '^',
        '~'
    ]
    
    syntax_count = 0
    for pattern in syntax_patterns:
        syntax_count += text.count(pattern)
    
    syntax_ratio = syntax_count / max(len(text), 1)
    
    # Check for very long lines (often minified JavaScript)
    lines = text.split('\n')
    long_line_count = sum(1 for line in lines if len(line) > 200)
    long_line_ratio = long_line_count / max(len(lines), 1)
    
    # Check for lack of readable sentences
    sentences = text.split('.')
    readable_sentences = sum(1 for sentence in sentences if len(sentence.strip()) > 10 and ' ' in sentence.strip())
    readable_ratio = readable_sentences / max(len(sentences), 1)
    
    # Decision logic - Made less aggressive
    if js_ratio > 0.25:  # More than 25% JavaScript patterns (was 10%)
        return True
    
    if syntax_ratio > 0.25:  # More than 25% syntax characters (was 15%)
        return True
    
    if long_line_ratio > 0.5:  # More than 50% long lines (was 30%)
        return True
    
    if readable_ratio < 0.1:  # Less than 10% readable sentences (was 20%)
        return True
    
    # Additional checks for common JavaScript libraries/frameworks
    js_library_patterns = [
        'jquery',
        'angular',
        'react',
        'vue',
        'bootstrap',
        'lodash',
        'underscore',
        'moment',
        'axios',
        'fetch',
        'promise',
        'async',
        'await',
        'websocket',
        'webrtc',
        'canvas',
        'webgl',
        'three.js',
        'd3.js',
        'chart.js',
        'plotly',
        'leaflet',
        'mapbox',
        'google maps',
        'firebase',
        'aws',
        'azure',
        'gcp',
        'cdn',
        'api',
        'rest',
        'graphql',
        'socket.io',
        'express',
        'node.js',
        'npm',
        'yarn',
        'webpack',
        'babel',
        'typescript',
        'eslint',
        'prettier',
        'jest',
        'mocha',
        'chai',
        'sinon',
        'cypress',
        'selenium',
        'puppeteer',
        'playwright'
    ]
    
    library_count = sum(1 for pattern in js_library_patterns if pattern in text_lower)
    if library_count > 3:  # Multiple JavaScript libraries mentioned
        return True
    
    return False

def process_content_with_ai(
    content: str,
    url: str,
    page,
    needed: Set[str],
    evidence_details: Dict[str, CriteriaEvidence],
    visited: Set[str],
    results: List[Dict[str, Any]],
    queue: List[tuple],
    depth: int,
    captured: Set[str],
    company: str,
    is_pdf: bool = False,
    verbose: bool = False
) -> bool:
    """Process HTML content with AI analysis and evidence collection - PDFs handled in Phase 1"""
    if not content or len(content) < 50:
        return False
    
    # PDFs should not reach this function - they're handled in Phase 1
    if is_pdf:
        logger.warning("PDFs should be handled in Phase 1, not here")
        return False
        
    # For HTML content, always use analyze_text_with_ai_batched which handles large content internally
    # No need for manual chunking - let the AI batching function handle it
    findings = analyze_text_with_ai_batched(content, url, needed, company)
        
    # Store evidence and update tracking
    if findings:
        for criterion, evidence in findings.items():
            if criterion not in evidence_details or should_replace_evidence_ai(evidence, evidence_details[criterion]):
                evidence_details[criterion] = evidence
                needed.discard(criterion)  # Remove from needed set
                
        logger.info(f"Found evidence for {len(findings)} criteria at {url}")
        
    # Continue looking for more evidence if needed (only for non-PDF content)
    if needed and not is_pdf:
        # Get both static and dynamically loaded links
        try:
            # Guard against None page object and ensure it's not a PDF
            page_links = set(page.evaluate(ALL_LINKS_JS)) if page and not is_pdf else set()
            logger.debug(f"[LINKS] Found {len(page_links)} static links at {url}")
        except Exception as e:
            logger.warning(f"Failed to extract links from {url}: {e}")
            page_links = set()
        
        all_links = page_links.union(captured)
        logger.debug(f"[LINKS] Total {len(all_links)} links (including {len(captured)} captured) at {url}")
        
        # Track found links
        sublinks = []
        pdf_links = []
        
        # Process each discovered link
        for link in all_links:
            try:
                abs_url = urldefrag(urljoin(url, link))[0]
                if abs_url not in visited:
                    if abs_url.lower().endswith('.pdf'):
                        # Collect relevant PDFs
                        if should_crawl(abs_url, needed, company):
                            pdf_links.append(abs_url)
                            logger.debug(f"[PDF] Found relevant PDF: {abs_url}")
                    # Only filter non-seed URLs
                    elif depth == 0 or should_crawl(abs_url, needed, company):
                        sublinks.append(abs_url)
                        # Add to queue with priority score
                        link_score = score_url(abs_url, needed, company)
                        heapq.heappush(queue, (-link_score, abs_url, depth + 1))
                        logger.debug(f"[QUEUE] Added {abs_url} with score {link_score}")
            except Exception as e:
                logger.warning(f"Failed to process link {link}: {e}")
                continue
        
        # Update results with discovered links
        results.append({
            'url': url,
            'is_pdf': is_pdf,
            'title': page.title() if page and not is_pdf else None,
            'text': content,
            'sublinks': sublinks,
            'pdf_links': pdf_links
        })
    else:
        # For PDFs or when no links needed, store basic results
        results.append({
            'url': url,
            'is_pdf': is_pdf,
            'title': page.title() if page and not is_pdf else None,
            'text': content,
            'sublinks': [],
            'pdf_links': []
        })
    
    # Return True if we found evidence, False otherwise
    return bool(findings)

def get_complete_website_content(page, url: str, verbose: bool = False) -> str:
    """
    FIXED: Get COMPLETE readable website content, filtering out JavaScript.
    Focuses on extracting actual readable content, not script code.
    """
    try:
        # Step 1: Wait for page to fully load including dynamic content
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
            if verbose:
                print(f"    Page fully loaded with dynamic content")
        except Exception as e:
            if verbose:
                print(f"    Dynamic content wait failed: {e}")
        
        # Step 2: Get clean readable content using multiple methods
        extraction_methods = []
        
        # Method 1: Enhanced HTML to text conversion (primary method)
        try:
            html_content = page.content()
            clean_text = html_to_clean_text(html_content, url)
            if clean_text and len(clean_text.strip()) > 100:
                # Validate that it's not mostly JavaScript
                if not is_mostly_javascript(clean_text):
                    extraction_methods.append(("HTML_CLEAN", clean_text))
                    if verbose:
                        print(f"    Clean HTML text: {len(clean_text):,} characters")
                else:
                    if verbose:
                        print(f"    Clean HTML text rejected (mostly JavaScript): {len(clean_text):,} characters")
        except Exception as e:
            if verbose:
                print(f"    HTML cleaning failed: {e}")
        
        # Method 2: Simple innerText extraction
        try:
            body_text = page.evaluate("() => document.body ? document.body.innerText : ''")
            if body_text and len(body_text.strip()) > 100:
                # Validate that it's not mostly JavaScript
                if not is_mostly_javascript(body_text):
                    extraction_methods.append(("VISIBLE_TEXT", body_text))
                    if verbose:
                        print(f"    Visible text: {len(body_text):,} characters")
                else:
                    if verbose:
                        print(f"    Visible text rejected (mostly JavaScript): {len(body_text):,} characters")
        except Exception as e:
            if verbose:
                print(f"    Visible text extraction failed: {e}")
        
        # Method 3: Content-specific selectors (main content areas)
        try:
            content_selectors = [
                "main", "article", ".content", ".main-content", "#content", "#main",
                ".post-content", ".entry-content", ".page-content", ".article-content",
                ".container", ".wrapper", ".body-content"
            ]
            
            for selector in content_selectors:
                try:
                    selector_text = page.evaluate(f"() => {{ const el = document.querySelector('{selector}'); return el ? el.innerText : ''; }}")
                    if selector_text and len(selector_text.strip()) > 100:
                        if not is_mostly_javascript(selector_text):
                            extraction_methods.append((f"SELECTOR_{selector}", selector_text))
                            if verbose:
                                print(f"    Content from {selector}: {len(selector_text):,} characters")
                            break  # Use first successful selector
                except Exception as e:
                    if verbose:
                        print(f"    Selector {selector} failed: {e}")
                    continue
        except Exception as e:
            if verbose:
                print(f"    Selector extraction failed: {e}")
        
        # Method 4: Table extraction (important for fleet data)
        try:
            table_text = page.evaluate("""() => {
                const tables = document.querySelectorAll('table');
                let data = '';
                tables.forEach(t => {
                    const rows = t.querySelectorAll('tr');
                    rows.forEach(r => {
                        const cells = r.querySelectorAll('td, th');
                        const rowData = Array.from(cells).map(c => c.innerText.trim()).join(' | ');
                        if (rowData) data += rowData + '\\n';
                    });
                });
                return data;
            }""")
            if table_text and len(table_text.strip()) > 50:
                extraction_methods.append(("TABLE_DATA", table_text))
                if verbose:
                    print(f"    Table data: {len(table_text):,} characters")
        except Exception as e:
            if verbose:
                print(f"    Table extraction failed: {e}")
        
        # Step 3: Validate and combine extraction methods
        if not extraction_methods:
            if verbose:
                print(f"    No valid content extracted, trying fallback")
            # Fallback: aggressive content extraction
            try:
                fallback_text = page.evaluate("""() => {
                    const elems = document.querySelectorAll('p, div, h1, h2, h3, h4, h5, h6, li, span');
                    let text = '';
                    elems.forEach(el => {
                        const t = el.innerText;
                        if (t && t.length > 10) text += t + '\\n';
                    });
                    return text;
                }""")
                if fallback_text and len(fallback_text.strip()) > 100:
                    extraction_methods.append(("FALLBACK_PARAGRAPHS", fallback_text))
                    if verbose:
                        print(f"    Fallback paragraph extraction: {len(fallback_text):,} characters")
            except Exception as e:
                if verbose:
                    print(f"    Fallback extraction failed: {e}")
        
        if not extraction_methods:
            if verbose:
                print(f"    No readable content extracted, trying HTML fallback")
            # Last resort: use HTML cleaning even if it was rejected as JavaScript
            try:
                html_content = page.content()
                fallback_html_text = html_to_clean_text(html_content, url)
                if fallback_html_text and len(fallback_html_text.strip()) > 50:
                    if verbose:
                        print(f"    Using HTML fallback content: {len(fallback_html_text):,} characters (may contain some JavaScript)")
                    return fallback_html_text
            except Exception as e:
                if verbose:
                    print(f"    HTML fallback failed: {e}")
            return ""
        
        # Find the best extraction (prefer HTML_CLEAN, then longest)
        html_clean = next((item for item in extraction_methods if item[0] == "HTML_CLEAN"), None)
        if html_clean:
            best_extraction = html_clean
        else:
            best_extraction = max(extraction_methods, key=lambda x: len(x[1]))
        
        primary_content = best_extraction[1]
        
        if verbose:
            print(f"    Primary content from {best_extraction[0]}: {len(primary_content):,} characters")
        
        # Add supplementary content that's meaningful and different
        supplementary_content = []
        for method_name, content in extraction_methods:
            if method_name != best_extraction[0]:
                # Include if it's substantially different and meaningful
                if len(content) > len(primary_content) * 0.2 and len(content) < len(primary_content) * 3:
                    # Check if it has meaningful different content
                    unique_words = len(set(content.split()) - set(primary_content.split()))
                    if unique_words > 20:
                        supplementary_content.append(f"=== {method_name} ===\n{content}")
        
        # Combine primary + supplementary content
        if supplementary_content:
            combined_parts = [f"=== PRIMARY_CONTENT ===\n{primary_content}"]
            combined_parts.extend(supplementary_content)
            final_content = "\n\n".join(combined_parts)
        else:
            final_content = primary_content  # Don't add headers if only one source
        
        if verbose:
            print(f"    Final combined content: {len(final_content):,} characters")
            print(f"    Content sources: {len(extraction_methods)} extraction methods")
            print(f"    Content preview: {final_content[:300]}...")
        
        return final_content
        
    except Exception as e:
        logger.error(f"Enhanced content extraction failed for {url}: {e}")
        # Fallback to basic HTML conversion
        try:
            html_content = page.content()
            fallback_text = html_to_clean_text(html_content, url)
            if not is_mostly_javascript(fallback_text):
                return fallback_text
            else:
                return ""
        except:
            return ""

def get_complete_content_from_html(html_content: str, url: str, verbose: bool = False) -> str:
    """
    ENHANCED: Get COMPLETE content from HTML string (for requests fallback).
    Uses aggressive extraction methods to ensure maximum content capture.
    """
    try:
        if verbose:
            print(f"    Raw HTML content: {len(html_content):,} characters")
        
        extraction_methods = []
        
        # Method 1: Trafilatura (excellent for article content)
        try:
            clean_text = html_to_clean_text(html_content, url)
            if clean_text and len(clean_text.strip()) > 100:
                if not is_mostly_javascript(clean_text):
                    extraction_methods.append(("TRAFILATURA", clean_text))
                    if verbose:
                        print(f"    Trafilatura extraction: {len(clean_text):,} characters")
                else:
                    if verbose:
                        print(f"    Trafilatura extraction rejected (mostly JavaScript): {len(clean_text):,} characters")
        except Exception as e:
            if verbose:
                print(f"    Trafilatura extraction failed: {e}")
        
        # Method 2: Aggressive BeautifulSoup extraction
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove only the most problematic elements
            for element in soup(["script", "style", "noscript", "head"]):
                element.decompose()
            
            # Get all text with better spacing
            aggressive_text = soup.get_text(separator=" ", strip=True)
            aggressive_text = re.sub(r'\s+', ' ', aggressive_text).strip()
            
            if aggressive_text and len(aggressive_text.strip()) > 100:
                if not is_mostly_javascript(aggressive_text):
                    extraction_methods.append(("AGGRESSIVE_SOUP", aggressive_text))
                    if verbose:
                        print(f"    Aggressive BeautifulSoup: {len(aggressive_text):,} characters")
                else:
                    if verbose:
                        print(f"    Aggressive BeautifulSoup rejected (mostly JavaScript): {len(aggressive_text):,} characters")
        except Exception as e:
            if verbose:
                print(f"    Aggressive BeautifulSoup failed: {e}")
        
        # Method 3: Conservative BeautifulSoup (keep more structure)
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove only scripts and styles
            for element in soup(["script", "style"]):
                element.decompose()
            
            # Get text preserving some structure
            conservative_text = soup.get_text(separator=" ", strip=True)
            conservative_text = re.sub(r'\s+', ' ', conservative_text).strip()
            
            if conservative_text and len(conservative_text.strip()) > 100:
                if not is_mostly_javascript(conservative_text):
                    extraction_methods.append(("CONSERVATIVE_SOUP", conservative_text))
                    if verbose:
                        print(f"    Conservative BeautifulSoup: {len(conservative_text):,} characters")
                else:
                    if verbose:
                        print(f"    Conservative BeautifulSoup rejected (mostly JavaScript): {len(conservative_text):,} characters")
        except Exception as e:
            if verbose:
                print(f"    Conservative BeautifulSoup failed: {e}")
        
        # Method 4: Table extraction (important for fleet data)
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            
            tables = soup.find_all("table")
            table_data = []
            
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    row_data = " | ".join(cell.get_text(strip=True) for cell in cells if cell.get_text(strip=True))
                    if row_data:
                        table_data.append(row_data)
            
            if table_data:
                table_text = "\n".join(table_data)
                extraction_methods.append(("TABLE_DATA", table_text))
                if verbose:
                    print(f"    Table extraction: {len(table_text):,} characters")
        except Exception as e:
            if verbose:
                print(f"    Table extraction failed: {e}")
        
        # Method 5: Content-specific extraction (main, article, etc.)
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            
            content_selectors = ["main", "article", ".content", ".main-content", "#content", "#main"]
            
            for selector in content_selectors:
                try:
                    if selector.startswith('.'):
                        elements = soup.find_all(class_=selector[1:])
                    elif selector.startswith('#'):
                        elements = soup.find_all(id=selector[1:])
                    else:
                        elements = soup.find_all(selector)
                    
                    if elements:
                        selector_text = " ".join(elem.get_text(separator=" ", strip=True) for elem in elements)
                        if selector_text and len(selector_text.strip()) > 100:
                            if not is_mostly_javascript(selector_text):
                                extraction_methods.append((f"SELECTOR_{selector}", selector_text))
                                if verbose:
                                    print(f"    Content from {selector}: {len(selector_text):,} characters")
                                break  # Use first successful selector
                except:
                    continue
        except Exception as e:
            if verbose:
                print(f"    Content selector extraction failed: {e}")
        
        # Method 6: Raw text extraction (last resort)
        try:
            raw_text = re.sub(r'<[^>]+>', ' ', html_content)
            raw_text = re.sub(r'\s+', ' ', raw_text).strip()
            # Remove common HTML entities
            raw_text = raw_text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            
            if raw_text and len(raw_text.strip()) > 100:
                if not is_mostly_javascript(raw_text):
                    extraction_methods.append(("RAW_TEXT", raw_text))
                    if verbose:
                        print(f"    Raw text extraction: {len(raw_text):,} characters")
                else:
                    if verbose:
                        print(f"    Raw text extraction rejected (mostly JavaScript): {len(raw_text):,} characters")
        except Exception as e:
            if verbose:
                print(f"    Raw text extraction failed: {e}")
        
        # Combine all extraction methods intelligently
        if not extraction_methods:
            if verbose:
                print(f"    No content extracted, returning empty")
            return ""
        
        # Find the best extraction (longest with good content)
        best_extraction = max(extraction_methods, key=lambda x: len(x[1]))
        primary_content = best_extraction[1]
        
        if verbose:
            print(f"    Primary content from {best_extraction[0]}: {len(primary_content):,} characters")
        
        # Add supplementary content that's significantly different
        supplementary_content = []
        for method_name, content in extraction_methods:
            if method_name != best_extraction[0]:
                # Include if it's substantially different or contains additional info
                if len(content) > len(primary_content) * 0.2 and len(content) < len(primary_content) * 5:
                    # Check if it has meaningful different content
                    content_words = set(content.split())
                    primary_words = set(primary_content.split())
                    unique_words = content_words - primary_words
                    
                    if len(unique_words) > 10:  # Has meaningful unique content
                        supplementary_content.append(f"=== {method_name} ===\n{content}")
        
        # Combine primary + supplementary content
        combined_parts = [f"=== PRIMARY_CONTENT ===\n{primary_content}"]
        combined_parts.extend(supplementary_content)
        
        final_content = "\n\n".join(combined_parts)
        
        if verbose:
            print(f"    Final combined content: {len(final_content):,} characters")
            print(f"    Content sources: {len(combined_parts)} different extraction methods")
            print(f"    Content preview: {final_content[:300]}...")
        
        return final_content
        
    except Exception as e:
        logger.error(f"Enhanced HTML content extraction failed for {url}: {e}")
        # Fallback to basic HTML conversion
        try:
            return html_to_clean_text(html_content, url)
        except:
            return ""



def analyze_company_sustainability(
    company_name: str,
    criteria: Optional[Set[str]] = None,
    max_search_pages: int = 4,  # Increased from 2 to 4 for more search depth
    max_pdf_reports: int = 8,   # Increased from 5 to 8 for more PDF analysis
    max_web_pages: int = 6,     # Increased from 3 to 6 for more web scraping
    verbose: bool = True,
    use_crawler: bool = False
) -> Dict[str, Any]:
    """
    IMPROVED: AI-powered sustainability analysis with page-based limits:
    1. Process full PDFs without interruption (no timeout limits)
    2. Use page limits instead of timeouts for web scraping
    3. Incremental saves for recovery
    4. Heartbeat feedback to show progress
    5. Graceful error handling for API failures
    6. Optional deep crawling for comprehensive coverage
    
    Args:
        company_name: Name of the company to analyze
        criteria: Set of criteria to analyze (defaults to all 8)
        max_search_pages: Maximum search result pages per query
        max_pdf_reports: Maximum number of PDF reports to analyze fully
        max_web_pages: Maximum number of web pages to scrape (TEMPORARILY DISABLED - scrapes all URLs)
        verbose: Whether to show detailed progress output
        use_crawler: Enable deep web crawling for long-tail evidence (slower but more comprehensive)
    """
    start_time = time.time()
    
    # Set up criteria to analyze
    if criteria is None:
        criteria = ALL_CRITERIA.copy()
    else:
        criteria = set(criteria)
    
    evidence_details = {}
    
    # Comprehensive tracking for detailed return information
    analysis_tracking = {
        'pdfs_checked': [],
        'web_pages_scraped': [],
        'search_queries': [],
        'phases_completed': [],
        'processing_errors': [],
        'phase_times': {},
        'sources_attempted': [],
        'sources_successful': []
    }
    
    # Set up temporary save file for incremental progress
    import tempfile
    temp_save_path = tempfile.mktemp(suffix=f"_{company_name.replace(' ', '_')}_analysis.json")
    
    def show_final_summary():
        """Show the final results summary"""
        total_time = time.time() - start_time
        if verbose:
            print(f"\n🔍 Final Results Summary")
            print("-" * 40)
            print(f"  Final evidence: {len(evidence_details)}/{len(criteria)} criteria")
            print(f"  Total analysis time: {total_time:.2f}s")
            print(f"  Sources checked: {len(analysis_tracking['sources_attempted'])} total")
            print(f"  Successful sources: {len(analysis_tracking['sources_successful'])}")
            print("\n" + "=" * 60)
            
            print(f"🎯 **RESULTS SUMMARY FOR {company_name.upper()}**")
            print("=" * 60)
            print(format_results_as_markdown_table(evidence_details, criteria))
            print("=" * 60)
            summary_printed = True
            
            # Show missing criteria  
            missing_criteria = criteria - set(evidence_details.keys())
            if missing_criteria:
                print(f"\n**Still Missing:** {', '.join(sorted(missing_criteria))}")
            
            # Show source summary
            if analysis_tracking['pdfs_checked']:
                print(f"\n**PDFs Analyzed:** {len(analysis_tracking['pdfs_checked'])}")
            if analysis_tracking['web_pages_scraped']:
                print(f"**Web Pages Scraped:** {len(analysis_tracking['web_pages_scraped'])}")
            if analysis_tracking['search_queries']:
                print(f"**Search Queries:** {len(analysis_tracking['search_queries'])}")
            
            print(f"\n🎉 Analysis completed successfully!")
            print("=" * 60)
        
        return {
            'company': company_name,
            'criteria_analyzed': list(criteria),
            'evidence_details': evidence_details,
            'total_criteria': len(criteria),
            'found_criteria': len(evidence_details),
            'analysis_time': total_time,
            'timestamp': time.time(),
            
            # Comprehensive analysis summary
            'analysis_summary': {
                'criteria_found': list(evidence_details.keys()),
                'criteria_not_found': list(criteria - set(evidence_details.keys())),
                'sources_analyzed': {
                    'pdfs_checked': analysis_tracking['pdfs_checked'],
                    'web_pages_scraped': analysis_tracking['web_pages_scraped'],
                    'search_queries_executed': analysis_tracking['search_queries'],
                    'total_sources_count': len(analysis_tracking['sources_attempted']),
                    'successful_sources_count': len(analysis_tracking['sources_successful'])
                },
                'phases_completed': analysis_tracking['phases_completed'],
                'processing_errors': analysis_tracking['processing_errors']
            },
            
            # Evidence quality breakdown
            'evidence_quality': {
                'high_confidence': [k for k, v in evidence_details.items() if v.confidence >= 90],
                'medium_confidence': [k for k, v in evidence_details.items() if 70 <= v.confidence < 90],
                'low_confidence': [k for k, v in evidence_details.items() if v.confidence < 70],
                'source_breakdown': {
                    'pdf_evidence': [k for k, v in evidence_details.items() if v.source_type == 'pdf_content'],
                    'web_evidence': [k for k, v in evidence_details.items() if v.source_type == 'web_content'],
                    'search_evidence': [k for k, v in evidence_details.items() if v.source_type == 'search_snippet']
                }
            },
            
            # Performance metrics
            'performance_metrics': {
                'total_analysis_time': total_time,
                'phase_breakdown': analysis_tracking['phase_times'],
                'efficiency_score': len(evidence_details) / max(total_time, 1) * 100,  # criteria found per second * 100
                'sources_per_criterion': len(analysis_tracking['sources_attempted']) / max(len(criteria), 1),
                'success_rate': len(analysis_tracking['sources_successful']) / max(len(analysis_tracking['sources_attempted']), 1) * 100
            }
        }
    
    if verbose:
        print(f"\nAI SUSTAINABILITY ANALYSIS: {company_name}")
        print("=" * 60)
        print(f"Analyzing {len(criteria)} criteria using PURE AI logic")
        print(f"Standardized limits: Search={MAX_SEARCH_PAGES_PER_CRITERION}, Web=UNLIMITED (all URLs), PDFs=Full analysis")
        print("=" * 60)

    # Phase 0: SMART INITIAL SEARCH (NEW - Use available search functions)
    if verbose:
        print(f"\nPhase 0: PDF Sustainability Reports (PRIORITY)")
        print("-" * 40)
        print(f"  Analyzing sustainability PDFs first - highest quality evidence")
    
    # EFFICIENCY: Filter needed criteria to exclude already verified evidence
    remaining_criteria = criteria.copy()
    
    initial_search_start_time = time.time()
    analysis_tracking['phases_completed'].append('Phase 0: PDF Analysis Started')
    try:
        if max_pdf_reports > 0:
            # Step 1: Get high-quality PDF sustainability reports FIRST (as user requested)
            if verbose:
                print(f"  Getting sustainability PDF reports...")
                
            sustainability_pdfs = get_sustainability_reports(company_name, max_results=max_pdf_reports)
        else:
            sustainability_pdfs = []
            if verbose:
                print(f"  Skipping PDF analysis (max_pdf_reports=0)")
        if verbose:
            print(f"  Found {len(sustainability_pdfs)} sustainability PDFs")
        
        # Track PDF sources
        analysis_tracking['pdfs_checked'] = list(sustainability_pdfs)
        analysis_tracking['sources_attempted'].extend(sustainability_pdfs)

        # Step 2: Analyze PDF content with OPTIMIZED multi-criteria batching 
        for i, pdf_url in enumerate(sustainability_pdfs):
            if not remaining_criteria:  # Early exit if all found
                break
                
            if verbose:
                print(f"  Analyzing PDF {i+1}/{len(sustainability_pdfs)}: {pdf_url}")
            
            try:
                pdf_text = extract_pdf_content(pdf_url, company_name)
                if not pdf_text:
                    if verbose:
                        print(f"    PDF {i+1}: Empty or invalid content")
                    continue
                    
                # Validate PDF ownership to prevent third-party PDFs
                if not validate_pdf_ownership(pdf_url, pdf_text, company_name):
                    if verbose:
                        print(f"    PDF {i+1}: Failed ownership validation - skipping")
                    continue
                        
                full_pdf_length = len(pdf_text)
                if verbose:
                    print(f"    PDF {i+1}: {full_pdf_length:,} characters extracted")
                
                # Use EFFICIENT AI batching - analyze_text_with_ai_batched handles large texts internally
                page_evidence = analyze_text_with_ai_batched(
                    pdf_text, pdf_url, remaining_criteria, company_name
                )
                
                # Update evidence from PDF
                pdf_found_evidence = False
                for criterion, evidence in page_evidence.items():
                    if evidence.found and evidence.score > 0:
                        pdf_found_evidence = True
                        if criterion not in evidence_details:
                            # New find
                            evidence_details[criterion] = evidence
                            remaining_criteria.discard(criterion)
                            if verbose:
                                print(f"    Found {criterion} in PDF (score: {evidence.score})")
                        elif evidence.score > evidence_details[criterion].score:
                            # Better evidence for existing criterion
                            evidence_details[criterion] = evidence
                            if verbose:
                                print(f"    Found better {criterion} in PDF (score: {evidence.score} vs {evidence_details[criterion].score})")
                        else:
                            # We already have same or better evidence
                            if verbose:
                                print(f"    Already found {criterion} with score {evidence_details[criterion].score} (PDF score: {evidence.score})")
                
                # Track successful PDF processing
                if pdf_found_evidence:
                    analysis_tracking['sources_successful'].append(pdf_url)
                
            except Exception as e:
                if verbose:
                    print(f"    PDF {i+1} analysis failed: {e}")
                analysis_tracking['processing_errors'].append(f"PDF analysis failed for {pdf_url}: {str(e)}")
                continue
    
        initial_search_time = time.time() - initial_search_start_time
        remaining_criteria = criteria - set(evidence_details.keys())
        
        # Track phase completion
        analysis_tracking['phase_times']['Phase 0: PDF Analysis'] = initial_search_time
        analysis_tracking['phases_completed'].append(f'Phase 0: PDF Analysis Complete ({len(evidence_details)} criteria found)')
        
        # Progress logging
        criteria_found = len(evidence_details)
        progress_pct = (criteria_found / len(criteria)) * 100
        logger.info(f"📊 Phase 0 complete: {criteria_found}/{len(criteria)} criteria found ({progress_pct:.1f}%) in {initial_search_time:.1f}s")
        
        if verbose:
            print(f"  Phase 0 found evidence for {len(evidence_details)}/{len(criteria)} criteria")
            
            # GRACEFUL: Show that PDF failures are non-blocking
            if not evidence_details and sustainability_pdfs:
                print(f"  PDF analysis complete - no company PDFs found, proceeding to search analysis")
            
            # MODIFIED: Continue searching for better evidence instead of early exit
            if len(evidence_details) >= len(criteria):
                # Calculate average evidence quality
                total_score = sum(evidence.score for evidence in evidence_details.values())
                avg_score = total_score / len(evidence_details)
                quality_threshold = 2.0  # Target average score of 2.0/3.0
                
                if avg_score >= quality_threshold:
                    if verbose:
                        print(f"  ALL CRITERIA FOUND with high quality (avg score: {avg_score:.2f}) - skipping web scraping")
                        return show_final_summary()
                else:
                    if verbose:
                        print(f"  ALL CRITERIA FOUND but continuing search for better evidence (avg score: {avg_score:.2f})")
                    # Continue to web scraping to find better evidence
            
    except KeyboardInterrupt:
        raise  # Allow immediate Ctrl-C
    except Exception as e:
        logger.error(f"Phase 0 analysis failed: {e}")
        analysis_tracking['processing_errors'].append(f"Phase 0 failed: {str(e)}")
        if verbose:
            print(f"  Phase 0 failed: {e}")

    # Phase 1: Enhanced Search Analysis (for remaining criteria only)
    # EFFICIENCY: Update remaining criteria and skip if all found
    remaining_criteria = criteria - set(evidence_details.keys())
    if not remaining_criteria:
        if verbose:
            print(f"  ALL CRITERIA FOUND in Phase 0 - skipping remaining phases")
        analysis_tracking['phases_completed'].append('All criteria found in Phase 0 - remaining phases skipped')
        return show_final_summary()
        
    if remaining_criteria and verbose:
        print(f"\nPhase 1: Enhanced Search Analysis")
        print("-" * 40)
        print(f"  Analyzing search results for {len(remaining_criteria)} missing criteria: {list(remaining_criteria)}")
    
    snippet_start_time = time.time()
    analysis_tracking['phases_completed'].append('Phase 1: Enhanced Search Analysis Started')
    
    # Initialize enhanced_search_urls to ensure it's always available for Phase 3
    enhanced_search_urls = []
    
    try:
        if remaining_criteria and max_search_pages > 0:
            # ENHANCED: Use the sophisticated search functions for missing criteria
            if verbose:
                print(f"  Getting enhanced targeted search results...")
            
            try:
                # Collect evidence from individual searches instead of re-analyzing everything
                individual_evidence = {}
                
                # For each missing criterion, do targeted searches and collect evidence
                for criterion in remaining_criteria:
                    if criterion in CRITERIA_QUESTIONS:
                        questions = CRITERIA_QUESTIONS[criterion][:2]  # Use first 2 questions
                        
                        for question_template in questions:
                            try:
                                query = question_template.format(company=company_name)
                                search_phrase = query.replace(f"{company_name} ", "")
                                # Track search query
                                analysis_tracking['search_queries'].append(f"{company_name} {search_phrase}")
                                analysis_tracking['sources_attempted'].append(f"Search: {search_phrase}")
                                search_results = search_google(company_name, search_phrase, max_pages=max_search_pages)
                                
                                if search_results:
                                    if verbose:
                                        print(f"    {criterion}: Found {len(search_results)} search results")
                                    
                                    # Actually analyze and collect evidence from individual searches
                                    criterion_evidence = analyze_search_snippets(
                                        search_results, company_name, {criterion}
                                    )
                                    
                                    # Store evidence from individual searches (analyze_search_snippets now returns CriteriaEvidence objects)
                                    for found_criterion, evidence_data in criterion_evidence.items():
                                        if found_criterion == criterion:  # Only the targeted criterion
                                            # analyze_search_snippets now always returns CriteriaEvidence objects
                                            individual_evidence[criterion] = evidence_data
                                            
                                            if verbose:
                                                print(f"    Found {criterion} in targeted search (score: {evidence_data.score}, confidence: {evidence_data.confidence}%)")
                                            # Track successful search
                                            analysis_tracking['sources_successful'].append(f"Search: {search_phrase}")
                                            break  # Found evidence for this criterion, move to next
                                    
                                    # Also collect URLs for potential web scraping
                                    enhanced_search_urls.extend(list(search_results.keys())[:2])
                                
                            except Exception as e:
                                logger.warning(f"Enhanced search failed for {criterion}: {e}")
                                continue
                    
                    # Early exit if found evidence for this criterion
                    if criterion in individual_evidence:
                        continue
                
                # Use evidence collected from individual searches with proper replacement logic
                if individual_evidence:
                    for criterion, evidence_data in individual_evidence.items():
                        # Check if we should add or replace existing evidence
                        if criterion not in evidence_details:
                            # New evidence
                            evidence_details[criterion] = evidence_data
                            remaining_criteria.discard(criterion)
                            if verbose:
                                print(f"    Added new evidence for {criterion} (score: {evidence_data.score})")
                        else:
                            # Check if new evidence is better than existing
                            existing_evidence = evidence_details[criterion]
                            if should_replace_evidence_ai(evidence_data, existing_evidence):
                                evidence_details[criterion] = evidence_data
                                if verbose:
                                    print(f"    Replaced evidence for {criterion} (new score: {evidence_data.score} vs old: {existing_evidence.score})")
                            else:
                                if verbose:
                                    print(f"    Kept existing evidence for {criterion} (existing score: {existing_evidence.score} vs new: {evidence_data.score})")
                            
                    if verbose:
                        print(f"  Enhanced search processed evidence for {len(individual_evidence)} criteria")
                
                if verbose:
                    print(f"  Collected {len(enhanced_search_urls)} enhanced search results")
                
                # SKIP redundant batch analysis since we already analyzed individual searches
                
            except Exception as e:
                logger.error(f"Enhanced search analysis failed: {e}")
                if verbose:
                    print(f"  Enhanced search analysis failed: {e}")
        elif remaining_criteria and max_search_pages == 0:
            if verbose:
                print(f"  Skipping search analysis (max_search_pages=0)")
        
        snippet_time = time.time() - snippet_start_time
        remaining_criteria = criteria - set(evidence_details.keys())
        
        # Track phase completion
        analysis_tracking['phase_times']['Phase 1: Enhanced Search'] = snippet_time
        analysis_tracking['phases_completed'].append(f'Phase 1: Enhanced Search Complete ({len(evidence_details)} criteria found)')
        
        # Progress logging
        criteria_found = len(evidence_details)
        progress_pct = (criteria_found / len(criteria)) * 100
        logger.info(f"📊 Phase 1 complete: {criteria_found}/{len(criteria)} criteria found ({progress_pct:.1f}%) in {snippet_time:.1f}s")
        
        if verbose:
            print(f"  Total evidence: {len(evidence_details)}/{len(criteria)} criteria")
            print(f"  Analysis time: {snippet_time:.2f}s")
            
        # MODIFIED: Continue searching for better evidence instead of early exit
        if len(evidence_details) >= len(criteria):
            # Calculate average evidence quality
            total_score = sum(evidence.score for evidence in evidence_details.values())
            avg_score = total_score / len(evidence_details)
            quality_threshold = 2.0  # Target average score of 2.0/3.0
            
            if avg_score >= quality_threshold:
                if verbose:
                    print(f"  ALL CRITERIA FOUND with high quality (avg score: {avg_score:.2f}) - skipping web scraping")
                    return show_final_summary()
            else:
                if verbose:
                    print(f"  ALL CRITERIA FOUND but continuing search for better evidence (avg score: {avg_score:.2f})")
                # Continue to web scraping to find better evidence

    except Exception as e:
        logger.error(f"Enhanced search analysis failed: {e}")
        if verbose:
            print(f"  Enhanced search analysis failed: {e}")

    # Phase 3: Smart Web Scraping (FINAL FALLBACK with user-specified limits)
    # TIMER: Initialize Phase 3 timer variables
    phase3_start_time = None
    phase3_timeout = 40 * 60  # 40 minutes in seconds
    
    if remaining_criteria and max_web_pages > 0:
        # TEMPORARILY DISABLED: Use user-specified limit for web scraping
        # dynamic_page_limit = max_web_pages
        dynamic_page_limit = 999  # Effectively unlimited for now
        scraping_intensity = "UNLIMITED"
        
        # TIMER: Start timer for Phase 3 web scraping (40 minute limit)
        phase3_start_time = time.time()
        
        if verbose:
            print(f"\nPhase 3: Smart Web Scraping (FINAL FALLBACK - {scraping_intensity})")
            print("-" * 40)
            print(f"  Scraping ALL collected URLs for {len(remaining_criteria)} missing criteria: {list(remaining_criteria)}")
            print(f"  ⏰ TIMER: Phase 3 has 40-minute timeout - will stop automatically if exceeded")
        
        try:
            # ENHANCED: Balanced URL collection ensuring each criterion gets representation
            scraping_urls = []
            
            # Source 1: Enhanced search URLs from Phase 1 (with proper error handling)
            phase1_urls = []
            if enhanced_search_urls:
                phase1_urls = enhanced_search_urls[:dynamic_page_limit]
                if verbose:
                    print(f"  Phase 1 provided {len(phase1_urls)} URLs from enhanced search")
                    logger.debug(f"Enhanced search URLs: {phase1_urls}")
            else:
                if verbose:
                    print(f"  No Phase 1 URLs available (likely due to max_search_pages=0)")
            
            # Source 2: Get balanced URLs ensuring each criterion gets representation
            try:
                if remaining_criteria:
                    # BALANCED APPROACH: Get URLs per criterion, then distribute fairly
                    urls_per_criterion = {}
                    total_criterion_urls = 0
                    
                    if verbose:
                        print(f"  Getting balanced URLs for {len(remaining_criteria)} criteria...")
                    
                    # Collect URLs for each missing criterion separately
                    for criterion in remaining_criteria:
                        # TIMER CHECK: Check if Phase 3 has exceeded 40 minutes during URL collection
                        current_phase3_time = time.time() - phase3_start_time
                        if current_phase3_time > phase3_timeout:
                            if verbose:
                                print(f"  ⏰ TIMER EXPIRED: Phase 3 exceeded 40 minutes during URL collection ({current_phase3_time/60:.1f} minutes)")
                                print(f"  Stopping URL collection and proceeding with current URLs")
                            analysis_tracking['processing_errors'].append(f"Phase 3 URL collection timeout after {current_phase3_time/60:.1f} minutes")
                            break
                            
                        try:
                            criterion_urls = get_enhanced_missing_criteria_seeds(
                                company_name, {criterion}, max_per_criterion=5
                            )
                            urls_per_criterion[criterion] = criterion_urls
                            total_criterion_urls += len(criterion_urls)
                            if verbose:
                                print(f"    {criterion}: {len(criterion_urls)} URLs found (Phase 3 time: {current_phase3_time/60:.1f} minutes)")
                                if criterion_urls:
                                    print(f"      URLs collected for {criterion}:")
                                    for j, url in enumerate(criterion_urls, 1):
                                        print(f"        {j}. {url}")
                                else:
                                    print(f"      No URLs found for {criterion}")
                        except Exception as e:
                            logger.warning(f"Failed to get URLs for {criterion}: {e}")
                            urls_per_criterion[criterion] = []
                    
                    if verbose:
                        print(f"  Total URLs collected: {total_criterion_urls} (before balanced distribution)")
                    
                    # SIMPLE COMBINATION: Add all collected URLs (no fair allocation needed)
                    scraping_urls.extend(phase1_urls)
                    
                    # Add all criterion-specific URLs
                    if urls_per_criterion:
                        all_criterion_urls = []
                        for criterion, criterion_urls in urls_per_criterion.items():
                            if criterion_urls:
                                all_criterion_urls.extend(criterion_urls)
                                if verbose:
                                    print(f"    {criterion}: collected {len(criterion_urls)} URLs")
                        
                        scraping_urls.extend(all_criterion_urls)
                        
                        if verbose:
                            print(f"  Total criterion-specific URLs: {len(all_criterion_urls)}")
                            print(f"  Total URLs before deduplication: {len(scraping_urls)} (Phase 1: {len(phase1_urls)}, Criterion-specific: {len(all_criterion_urls)})")
                    else:
                        if verbose:
                            print(f"  No criterion-specific URLs found")
                            print(f"  Total URLs before deduplication: {len(scraping_urls)} (Phase 1 only: {len(phase1_urls)})")
                    
            except Exception as e:
                logger.warning(f"Failed to get balanced URLs: {e}")
                # Fallback to Phase 1 URLs only
                scraping_urls.extend(phase1_urls)
            
            if verbose:
                print(f"  Total URLs collected before deduplication: {len(scraping_urls)}")
                logger.debug(f"All collected URLs: {scraping_urls}")
            
            # Remove duplicates while preserving order and criterion balance
            seen_urls = set()
            unique_scraping_urls = []
            pdf_count = 0
            duplicate_count = 0
            none_count = 0
            
            if verbose:
                print(f"  Processing {len(scraping_urls)} URLs for deduplication:")
            
            for i, url in enumerate(scraping_urls, 1):
                # TIMER CHECK: Check if Phase 3 has exceeded 40 minutes during deduplication
                current_phase3_time = time.time() - phase3_start_time
                if current_phase3_time > phase3_timeout:
                    if verbose:
                        print(f"  ⏰ TIMER EXPIRED: Phase 3 exceeded 40 minutes during deduplication ({current_phase3_time/60:.1f} minutes)")
                        print(f"  Stopping deduplication and proceeding with current unique URLs")
                    analysis_tracking['processing_errors'].append(f"Phase 3 deduplication timeout after {current_phase3_time/60:.1f} minutes")
                    break
                    
                if not url:
                    none_count += 1
                    if verbose:
                        print(f"    {i}. [SKIPPED - None/empty URL]")
                elif url.endswith('.pdf'):
                    pdf_count += 1
                    if verbose:
                        print(f"    {i}. [SKIPPED - PDF] {url}")
                elif url in seen_urls:
                    duplicate_count += 1
                    if verbose:
                        print(f"    {i}. [SKIPPED - DUPLICATE] {url}")
                elif url not in seen_urls:
                    seen_urls.add(url)
                    unique_scraping_urls.append(url)
                    if verbose:
                        print(f"    {i}. [ACCEPTED] {url}")
            
            if verbose:
                print(f"  URLs after deduplication: {len(unique_scraping_urls)}")
                print(f"  Filtered out: {pdf_count} PDFs, {duplicate_count} duplicates, {none_count} None/empty")
                print(f"  Balanced distribution ensures each criterion gets representation")
                print(f"  Final URLs to scrape:")
                for i, url in enumerate(unique_scraping_urls, 1):
                    print(f"    {i}. {url}")
                logger.debug(f"Unique URLs: {unique_scraping_urls}")
            
            max_scrape_pages = min(dynamic_page_limit, len(unique_scraping_urls))  # Use dynamic limit
            
            if unique_scraping_urls:
                if verbose:
                    print(f"  Found {len(unique_scraping_urls)} targeted URLs to scrape")
                
                # Track remaining criteria at start to avoid modification during iteration
                criteria_to_find = remaining_criteria.copy()
                
                # Try Playwright first
                playwright_success = False
                try:
                    # TIMER CHECK: Check if Phase 3 has exceeded 40 minutes before browser launch
                    current_phase3_time = time.time() - phase3_start_time
                    if current_phase3_time > phase3_timeout:
                        if verbose:
                            print(f"  ⏰ TIMER EXPIRED: Phase 3 exceeded 40 minutes before browser launch ({current_phase3_time/60:.1f} minutes)")
                            print(f"  Skipping Playwright and trying fallback scraping")
                        analysis_tracking['processing_errors'].append(f"Phase 3 browser launch timeout after {current_phase3_time/60:.1f} minutes")
                        playwright_success = False
                    else:
                        with sync_playwright() as p:
                            # Windows-compatible browser launch
                            if sys.platform == "win32":
                                browser = p.chromium.launch(
                                    headless=True,
                                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
                                )
                            else:
                                browser = p.chromium.launch(headless=True)
                            
                            page = browser.new_page()
                            
                            # Process targeted pages
                            for i, url in enumerate(unique_scraping_urls[:max_scrape_pages]):
                                if not criteria_to_find:  # Early exit if all criteria found
                                    break
                                
                                # TIMER CHECK: Check if Phase 3 has exceeded 40 minutes
                                current_phase3_time = time.time() - phase3_start_time
                                if current_phase3_time > phase3_timeout:
                                    if verbose:
                                        print(f"  ⏰ TIMER EXPIRED: Phase 3 exceeded 40 minutes ({current_phase3_time/60:.1f} minutes)")
                                        print(f"  Stopping web scraping and returning current results")
                                    analysis_tracking['processing_errors'].append(f"Phase 3 timeout after {current_phase3_time/60:.1f} minutes")
                                    analysis_tracking['phases_completed'].append(f'Phase 3: Web Scraping Timeout ({len(evidence_details)} criteria found)')
                                    return show_final_summary()
                                    
                                try:
                                    if verbose:
                                        print(f"  Scraping page {i+1}/{max_scrape_pages}: {url} (Phase 3 time: {current_phase3_time/60:.1f} minutes)")
                                    
                                    # Get page content with timeout (network timeout only)
                                    if verbose:
                                        print(f"    Navigating to {url}...")
                                    response = page.goto(url, timeout=PLAYWRIGHT_TIMEOUT)
                                    
                                    if verbose:
                                        print(f"    Response status: {response.status if response else 'No response'}")
                                    
                                    if response and response.status == 200:
                                        if verbose:
                                            print(f"    Getting COMPLETE website content...")
                                        
                                        # NEW: Get complete website content with multiple extraction methods
                                        complete_content = get_complete_website_content(page, url, verbose)
                                        
                                        if len(complete_content.strip()) < 50:
                                            if verbose:
                                                print(f"    WARNING: Very little content extracted ({len(complete_content)} chars)")
                                                print(f"    Raw content preview: {complete_content[:200]}")
                                        
                                        # Print scraped content for debugging
                                        if verbose:
                                            print(f"    Analyzing COMPLETE content from {url} ({len(complete_content)} chars)")
                                            print(f"    --- COMPLETE SCRAPED CONTENT START ---")
                                            print(complete_content[:3000] + "..." if len(complete_content) > 3000 else complete_content)
                                            print(f"    --- COMPLETE SCRAPED CONTENT END ---")
                                        
                                        if len(complete_content.strip()) > 50:  # Only analyze if we have meaningful content
                                            # Use the existing batching function with COMPLETE extracted content
                                            web_evidence = analyze_text_with_ai_batched(
                                                complete_content, url, criteria_to_find, company_name
                                            )
                                            
                                            # Update evidence for final missing criteria
                                            for criterion, evidence in web_evidence.items():
                                                if (criterion not in evidence_details and 
                                                    evidence.found and evidence.score > 0):
                                                    evidence_details[criterion] = evidence
                                                    remaining_criteria.discard(criterion)
                                                    criteria_to_find.discard(criterion)
                                                    if verbose:
                                                        print(f"    Web scraping found {criterion} (score: {evidence.score})")
                                        else:
                                            if verbose:
                                                print(f"    Skipping AI analysis - insufficient content")
                                    else:
                                        if verbose:
                                            print(f"    Failed to load page - Status: {response.status if response else 'No response'}")
                                            if response:
                                                print(f"    Response URL: {response.url}")
                                                print(f"    Response headers: {dict(response.headers)}")
                                                    
                                except Exception as e:
                                    logger.error(f"Failed to scrape {url}: {e}")
                                    if verbose:
                                        print(f"    Page {i+1}: Scraping failed - {e}")
                                        import traceback
                                        print(f"    Full error: {traceback.format_exc()}")
                                    continue
                            
                            browser.close()
                            playwright_success = True
                        
                except Exception as browser_error:
                    logger.error(f"Browser launch failed: {browser_error}")
                    if verbose:
                        print(f"  Browser launch failed: {browser_error}")
                
                # Fallback to requests if Playwright failed and we still need criteria
                if not playwright_success and criteria_to_find:
                    if verbose:
                        print(f"  Falling back to requests-based scraping...")
                    
                                    # Process URLs using requests instead of browser (respecting max_scrape_pages)
                for i, url in enumerate(unique_scraping_urls[:max_scrape_pages]):
                    if not criteria_to_find:  # Early exit if all criteria found
                        break
                    
                    # TIMER CHECK: Check if Phase 3 has exceeded 40 minutes
                    current_phase3_time = time.time() - phase3_start_time
                    if current_phase3_time > phase3_timeout:
                        if verbose:
                            print(f"  ⏰ TIMER EXPIRED: Phase 3 exceeded 40 minutes ({current_phase3_time/60:.1f} minutes)")
                            print(f"  Stopping fallback scraping and returning current results")
                        analysis_tracking['processing_errors'].append(f"Phase 3 fallback timeout after {current_phase3_time/60:.1f} minutes")
                        analysis_tracking['phases_completed'].append(f'Phase 3: Fallback Scraping Timeout ({len(evidence_details)} criteria found)')
                        return show_final_summary()
                        
                    try:
                        if verbose:
                            print(f"  Fallback scraping {i+1}: {url} (Phase 3 time: {current_phase3_time/60:.1f} minutes)")
                        
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                        
                        if verbose:
                            print(f"    Making HTTP request to {url}...")
                        response = requests.get(url, headers=headers, timeout=10)
                        
                        if verbose:
                            print(f"    Response status: {response.status_code}")
                            print(f"    Response headers: {dict(response.headers)}")
                            print(f"    Raw response length: {len(response.text)} chars")
                        
                        if response.status_code == 200:
                            # NEW: Get complete content using multiple extraction methods
                            complete_content = get_complete_content_from_html(response.text, url, verbose)
                            
                            if len(complete_content.strip()) < 50:
                                if verbose:
                                    print(f"    WARNING: Very little content extracted ({len(complete_content)} chars)")
                                    print(f"    Raw content preview: {complete_content[:200]}")
                            
                            # Print scraped content for debugging
                            if verbose:
                                print(f"    Analyzing COMPLETE fallback content from {url} ({len(complete_content)} chars)")
                                print(f"    --- COMPLETE FALLBACK SCRAPED CONTENT START ---")
                                print(complete_content[:3000] + "..." if len(complete_content) > 3000 else complete_content)
                                print(f"    --- COMPLETE FALLBACK SCRAPED CONTENT END ---")
                            
                            if len(complete_content.strip()) > 50:  # Only analyze if we have meaningful content
                                # Use the existing batching function with COMPLETE extracted content
                                web_evidence = analyze_text_with_ai_batched(
                                    complete_content, url, criteria_to_find, company_name
                                )
                                
                                # Update evidence for final missing criteria
                                for criterion, evidence in web_evidence.items():
                                    if (criterion not in evidence_details and 
                                        evidence.found and evidence.score > 0):
                                        evidence_details[criterion] = evidence
                                        remaining_criteria.discard(criterion)
                                        criteria_to_find.discard(criterion)
                                        if verbose:
                                            print(f"    Fallback scraping found {criterion} (score: {evidence.score})")
                            else:
                                if verbose:
                                    print(f"    Skipping AI analysis - insufficient content")
                        else:
                            if verbose:
                                print(f"    HTTP request failed - Status: {response.status_code}")
                                        
                    except Exception as e:
                        logger.warning(f"Fallback scraping failed for {url}: {e}")
                        if verbose:
                            print(f"    Fallback scraping failed: {e}")
                            import traceback
                            print(f"    Full error: {traceback.format_exc()}")
                        continue
            else:
                if verbose:
                    print(f"  No suitable URLs found for web scraping")
                    
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            if verbose:
                print(f"  Web scraping failed: {e}")
    
    # TIMER: Track Phase 3 completion time
    if phase3_start_time is not None:
        phase3_total_time = time.time() - phase3_start_time
        analysis_tracking['phase_times']['Phase 3: Web Scraping'] = phase3_total_time
        analysis_tracking['phases_completed'].append(f'Phase 3: Web Scraping Complete ({len(evidence_details)} criteria found) in {phase3_total_time/60:.1f} minutes')
        
        if verbose:
            print(f"  Phase 3 completed in {phase3_total_time/60:.1f} minutes")
            if phase3_total_time < phase3_timeout:
                print(f"  ⏰ Timer: Phase 3 completed within 40-minute limit")
            else:
                print(f"  ⏰ Timer: Phase 3 exceeded 40-minute limit but completed")
    elif remaining_criteria and max_web_pages == 0:
        if verbose:
            print(f"\nPhase 3: Skipping Web Scraping")
            print("-" * 40)
            print(f"  Web scraping disabled (max_web_pages=0)")
    else:
        if verbose:
            print(f"\nPhase 3: Skipping Web Scraping")
            print("-" * 40)
            print(f"  All criteria found - no web scraping needed!")

    # Final Results - ALWAYS DISPLAY SUMMARY
    remaining_criteria = criteria - set(evidence_details.keys())
    
    # Final progress logging
    criteria_found = len(evidence_details)
    progress_pct = (criteria_found / len(criteria)) * 100
    total_time = time.time() - start_time
    logger.info(f"🎯 Analysis complete: {criteria_found}/{len(criteria)} criteria found ({progress_pct:.1f}%) in {total_time:.1f}s")
    
    if remaining_criteria:
        logger.info(f"🔍 Missing criteria: {', '.join(sorted(remaining_criteria))}")
    
    if verbose:
        print(f"\nFinal Results Summary")
        print("-" * 40)
        
        print(f"RESULTS SUMMARY FOR {company_name.upper()}")
        print("=" * 60)
        print(format_results_as_markdown_table(evidence_details, criteria))
        print("=" * 60)
        summary_printed = True
        
        # Show missing criteria
        if remaining_criteria:
            print(f"\nStill Missing: {', '.join(sorted(remaining_criteria))}")
        
        print(f"\nAnalysis completed successfully!")
        print("=" * 60)
    
    # Return comprehensive format with full analysis details
    return show_final_summary()



def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-powered sustainability analysis scraper')
    parser.add_argument('company', help='Company name to analyze')
    parser.add_argument('--criteria', nargs='*', 
                       choices=list(ALL_CRITERIA), 
                       help='Specific criteria to analyze (default: all)')
    parser.add_argument('--max-search-pages', type=int, default=4,
                       help='Maximum search pages per query (default: 4)')
    parser.add_argument('--max-pdf-reports', type=int, default=8,  
                       help='Maximum PDF reports to analyze (default: 8)')
    parser.add_argument('--max-web-pages', type=int, default=6,  
                       help='Maximum web pages to crawl (default: 6)')
    parser.add_argument('--verbose', action='store_true', default=True,
                       help='Enable verbose output')
    parser.add_argument('--use-crawler', action='store_true', default=False,
                       help='Enable deep web crawling for comprehensive coverage')
    parser.add_argument('--json-output', type=str, 
                       help='Specify JSON output filename (default: {company}_sustainability_results.json)')
    parser.add_argument('--no-json', action='store_true', default=False,
                       help='Skip JSON export (not recommended - PostgreSQL upload will not be possible)')
    
    args = parser.parse_args()
    
    # Configure logging level based on verbose flag
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    
    # Convert criteria list to set if provided
    criteria_set = set(args.criteria) if args.criteria else None
    
    try:
        results = analyze_company_sustainability(
            company_name=args.company,
            criteria=criteria_set,
            max_search_pages=args.max_search_pages,
            max_pdf_reports=args.max_pdf_reports,
            max_web_pages=args.max_web_pages,
            use_crawler=args.use_crawler,
            verbose=args.verbose
        )
        
        # JSON Export functionality - ALWAYS export for PostgreSQL readiness unless --no-json
        if not args.no_json:
            try:
                from .export.json_exporter import SustainabilityDataExporter
                
                exporter = SustainabilityDataExporter()
                
                # Set company info
                exporter.set_company_info(args.company)
                
                # Process the analysis results - Use the stored evidence_details
                if 'evidence_details' in results:
                    # Use the original evidence_details stored during analysis
                    exporter.process_criteria_evidence(results['evidence_details'], args.company)
                else:
                    # Fallback: convert legacy format back to evidence_details format for export
                    evidence_found = results.get('evidence_found', {})
                    evidence_details_for_export = {}
                    
                    for criterion, evidence_data in evidence_found.items():
                        if evidence_data.get('found', False):
                            # Create CriteriaEvidence object for export
                            from .ai_criteria_analyzer import CriteriaEvidence
                            evidence_details_for_export[criterion] = CriteriaEvidence(
                                criterion=criterion,
                                found=True,
                                score=evidence_data.get('score', 1),
                                evidence_text=evidence_data.get('evidence', ''),
                                justification=evidence_data.get('justification', ''),
                                url=evidence_data.get('url', ''),
                                source_type=evidence_data.get('source_type', 'unknown'),
                                verified=evidence_data.get('verified', False),
                                full_context=evidence_data.get('context', '')
                            )
                    
                    exporter.process_criteria_evidence(evidence_details_for_export, args.company)
                
                # Export to JSON
                json_data = exporter.export_to_json()
                json_output = json.dumps(json_data, indent=2, ensure_ascii=False)
                
                # Determine filename
                if args.json_output:
                    filename = args.json_output
                else:
                    filename = f"{args.company.lower().replace(' ', '_')}_sustainability_results.json"
                
                # Save to file
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                
                print(f"\nJSON Export:")
                print(f"Results saved to: {filename}")
                print(f"File size: {len(json_output):,} characters")
                print(f"Structure: company info, sustainability_metrics, metric_sources, summaries")
                
                # Also return the JSON string for programmatic use
                results['json_export'] = json_output
                results['json_filename'] = filename
                
            except Exception as e:
                print(f"\nJSON export failed: {e}")
                logger.error(f"JSON export failed: {e}")
                # Still return results even if JSON export fails
                results['json_export'] = None
                results['json_filename'] = None
        else:
            print(f"\nJSON export skipped (--no-json flag used)")
            print(f"PostgreSQL upload will not be possible without JSON export")
            results['json_export'] = None
            results['json_filename'] = None
        
        # Results are already displayed in the function
        return results
        
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        return {}
    except TimeoutError as e:
        print(f"\n\n{e}")
        return {}
    except Exception as e:
        print(f"\n\nAnalysis failed: {e}")
        logger.error(f"Analysis failed: {e}")
        return {}





def format_results_as_markdown_table(evidence_details: Dict[str, CriteriaEvidence], all_criteria: Set[str]) -> str:
    # Get score ranges for proper display 
    from .analyze_scorecard import CRITERIA_DB_MAPPING_SCORES
    
    table = "## Sustainability Criteria Analysis Results\n\n"
    table += "| Criterion | Status | Score/Max | Evidence | Source | URL |\n"
    table += "|-----------|--------|-----------|----------|--------|---------|\n"
    
    for criterion in sorted(all_criteria):
        # Get max score for this criterion
        max_score = CRITERIA_DB_MAPPING_SCORES.get(criterion, (0, 3))[1]
        
        if criterion in evidence_details and evidence_details[criterion].found:
            evidence = evidence_details[criterion]
            status = "**FOUND**"
            score_display = f"**{evidence.score}/{max_score}**"
            
            # Truncate evidence and get source
            evidence_text = evidence.evidence_text[:100] + "..." if len(evidence.evidence_text) > 100 else evidence.evidence_text
            evidence_text = evidence_text.replace('|', '\\|').replace('\n', ' ')
            
            # Enhanced source type display with reliability ratings
            source_types = {
                'pdf_content': '**PDF** (High)',
                'web_content': '**Web** (Medium)', 
                'search_snippet': '**Snippet** (Low)'
            }
            source_display = source_types.get(evidence.source_type, evidence.source_type)
            
            # Clean and display actual URL instead of generic labels
            if hasattr(evidence, 'url') and evidence.url:
                if evidence.url.endswith('#search_snippet'):
                    actual_url = evidence.url.replace('#search_snippet', '')
                else:
                    actual_url = evidence.url
                
                # Truncate long URLs for table display
                if len(actual_url) > 50:
                    url_display = actual_url[:47] + "..."
                else:
                    url_display = actual_url
                    
                url_cell = f"[Link]({actual_url})"
            else:
                url_cell = "N/A"
                
        else:
            # Not found
            status = "**NOT FOUND**"
            score_display = f"0/{max_score}"
            evidence_text = "No evidence found in analyzed sources"
            source_display = "N/A"
            url_cell = "N/A"
        
        table += f"| {criterion} | {status} | {score_display} | {evidence_text} | {source_display} | {url_cell} |\n"
    
    return table

if __name__ == "__main__":
    main() 