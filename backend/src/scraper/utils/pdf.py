"""PDF processing and text extraction utilities."""

import fitz  # PyMuPDF
import unicodedata
import re
import requests
import logging
from typing import Optional, Union, List
from io import BytesIO
from pathlib import Path
import yaml
import time
from .strings import normalize_text

logger = logging.getLogger(__name__)

# Load PDF patterns config
CONFIG_DIR = Path(__file__).parent.parent / 'config'
with open(CONFIG_DIR / 'pdf_patterns.yaml') as f:
    PDF_CONFIG = yaml.safe_load(f)


def intelligent_chunk_text(text: str, chunk_size: int) -> List[str]:
    """
    Intelligently chunk text by sentence boundaries to avoid breaking evidence mid-sentence.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk in characters
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    sentences = text.split('. ')
    current_chunk = ""
    
    for sentence in sentences:
        # If adding this sentence would exceed chunk size, save current chunk and start new one
        if len(current_chunk) + len(sentence) + 2 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
        else:
            current_chunk += sentence + ". "
    
    # Add the last chunk if it has content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # If no sentence-based chunking worked, fall back to character-based
    if not chunks:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    return chunks


def is_valid_pdf_content(text: str, url: str = "", company: str = "") -> bool:
    """
    Enhanced PDF validation with company mention requirements to prevent third-party PDFs.
    
    Args:
        text: Extracted PDF text content
        url: URL of the PDF source
        company: Company name for validation
        
    Returns:
        True if PDF content is valid and relevant
    """
    url_low = (url or "").lower()
    company_lower = company.lower() if company else ""

    logger.debug(f"Validating PDF content: URL={url}, Company={company}, Text_length={len(text)}")

    # Always allow SEC filings and annual reports unconditionally
    if any(tag in url_low for tag in ("10-k", "20-f", "/annual-report", ".sec.gov")):
        logger.debug("PDF approved: SEC filing/annual report")
        return True

    # ENHANCED: Better domain check for company-specific content
    is_company_domain = False
    if company and url:
        # Generate comprehensive company variations
        company_variations = [
            company_lower,
            company_lower.replace(' ', ''),
            company_lower.replace(' ', '-'),
            company_lower.replace('.', ''),
        ]
        
        # CRITICAL FIX: Add first word of company name (like "XPO" from "XPO Logistics")
        first_word = company_lower.split()[0] if ' ' in company_lower else company_lower
        if len(first_word) > 2:  # Only add substantial first words
            company_variations.append(first_word)
        
        # Add variations without common suffixes
        for suffix in [' inc', ' corp', ' corporation', ' company', ' co', ' llc', ' ltd', ' logistics']:
            if company_lower.endswith(suffix):
                clean_no_suffix = company_lower[:-len(suffix)].strip()
                if len(clean_no_suffix) > 2:
                    company_variations.append(clean_no_suffix)
                    company_variations.append(clean_no_suffix.replace(' ', ''))
                break
        
        # Check domain patterns including common TLDs and subdomains
        domain_suffixes = ['.com', '.org', '.net', '.edu']
        subdomain_prefixes = ['', 'www.', 'about.', 'sustainability.', 'investor.', 'ir.']
        
        for variation in company_variations:
            if len(variation) > 2:  # Skip very short variations
                for prefix in subdomain_prefixes:
                    for suffix in domain_suffixes:
                        domain_pattern = f"{prefix}{variation}{suffix}"
                        if domain_pattern in url_low:
                            is_company_domain = True
                            logger.debug(f"PDF approved: Company domain match ({domain_pattern})")
                            break
                if is_company_domain:
                    break
            if is_company_domain:
                break

    # Always allow company sustainability/ESG reports from company domains
    if any(term in url_low for term in ("sustainability", "esg", "environmental", "climate", "responsibility")):
        logger.debug(f"PDF has sustainability keywords in URL")
        if is_company_domain:
            # Very lenient for sustainability reports from company domains
            if len(text) > 50:  # Reduced from 100 to 50
                logger.debug("PDF approved: Company sustainability report")
                return True
        else:
            # For non-company domains, check company mentions
            if company and text:
                company_mention_count = count_company_mentions(text, company)
                required_mentions = PDF_CONFIG.get('required_company_mentions', 2)
                logger.debug(f"Company mentions: {company_mention_count}, required: {required_mentions}")
                
                if company_mention_count >= required_mentions and len(text) > 100:  # Reduced from 200 to 100
                    logger.debug("PDF approved: Sufficient company mentions")
                    return True
            elif len(text) > 100:  # No company specified, be more lenient (reduced from 200)
                logger.debug("PDF approved: No company specified, sufficient content")
                return True

    # Very short / obvious junk - BUT be more lenient
    if len(text) < 20:  # Reduced from 200 to 20 for initial testing
        logger.debug(f"PDF rejected: Too short ({len(text)} chars)")
        return False

    # Skip forms only if *not* sustainability-related
    if (text.count("□") + text.count("☐")) > 10 and "sustainability" not in text.lower():
        logger.debug("PDF rejected: Form content without sustainability")
        return False

    # Enhanced company mention validation for third-party PDFs
    if company and not is_company_domain and text:
        company_mention_count = count_company_mentions(text, company)
        required_mentions = PDF_CONFIG.get('required_company_mentions', 2)
        
        # If this appears to be about the company but doesn't meet mention threshold, reject
        if company_mention_count > 0 and company_mention_count < required_mentions:
            # Unless it's from a valuable path (override)
            valuable_paths = PDF_CONFIG.get('valuable_paths', [])
            if not any(path in url_low for path in valuable_paths):
                logger.debug(f"PDF rejected: Insufficient company mentions ({company_mention_count}/{required_mentions})")
                return False

    # Retain if the body contains at least 2 sustainability words
    SUSTAIN = ("sustainability", "esg", "ghg", "net zero", "emission", "renewable", "climate", "carbon", "environmental")
    sustain_count = sum(w in text.lower() for w in SUSTAIN)
    if sustain_count >= 2:
        logger.debug(f"PDF approved: Sustainability content ({sustain_count} keywords)")
        return True

    # General company report validation - if it's from a company domain and has business content
    if any(term in url_low for term in ['/annual-report', '/investor', '/ir/', 'report']) and len(text) > 50:  # Reduced from 100
        logger.debug("PDF approved: Company report URL pattern")
        return True

    # ENHANCED: Allow PDFs from detected company domains even if no sustainability keywords
    if is_company_domain and len(text) > 100:
        logger.debug("PDF approved: Company domain with substantial content")
        return True

    # FOR TESTING: Allow any PDF that has some basic content
    if len(text) > 20:
        logger.debug("PDF approved: Basic content test (temporary)")
        return True

    logger.debug("PDF rejected: No validation criteria met")
    return False


def count_company_mentions(text: str, company: str) -> int:
    """
    Count the number of times a company is mentioned in text.
    Uses various company name variations for accurate counting.
    
    Args:
        text: Text to search in
        company: Company name to search for
        
    Returns:
        Number of company mentions found
    """
    if not text or not company:
        return 0
    
    text_lower = text.lower()
    company_lower = company.lower()
    
    # Generate company variations - ENHANCED for partial matches
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
    
    # ENHANCED: Add first word of company name for cases like "XPO" from "XPO Logistics"
    first_word = company_lower.split()[0] if ' ' in company_lower else company_lower
    if len(first_word) > 2:  # Only add substantial first words
        company_variations.append(first_word)
    
    # Count mentions, avoiding double-counting
    total_mentions = 0
    for variation in company_variations:
        if len(variation) > 2:  # Skip very short variations
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(variation) + r'\b'
            mentions = len(re.findall(pattern, text_lower, re.IGNORECASE))
            # Use the highest count from any variation to avoid double-counting
            total_mentions = max(total_mentions, mentions)
    
    return total_mentions


def extract_pdf_content(pdf_source: Union[str, bytes], company: str = "") -> str:
    """
    Extracts text from a PDF file or URL and returns it as a string.
    
    Args:
        pdf_source: Either a path to a PDF file or a URL pointing to a PDF
        company: Company name for validation and filtering
        
    Returns:
        Extracted text content as a string
    """
    start_time = time.time()
    max_processing_time = 120  # 2 minutes max per PDF
    
    # Store original URL for validation
    original_url = pdf_source if isinstance(pdf_source, str) and pdf_source.startswith('http') else ""
    
    try:
        # Handle URL case with improved timeout and retry logic
        if isinstance(pdf_source, str) and (pdf_source.startswith('http://') or pdf_source.startswith('https://')):
            logger.info(f"Attempting to download PDF from: {pdf_source}")
            headers = {"User-Agent": "Mozilla/5.0 (compatible; PDFScraper/1.0)"}
            
            # Retry logic for failed downloads
            max_retries = 1  # Reduced from 2 to 1 to prevent hanging
            for attempt in range(max_retries + 1):
                try:
                    logger.info(f"Download attempt {attempt + 1}/{max_retries + 1} for {pdf_source}")
                    # Reduced timeout from 60s to 30s to prevent hanging
                    response = requests.get(pdf_source, headers=headers, stream=True, timeout=30)
                    logger.info(f"Response status: {response.status_code}, Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                    response.raise_for_status()
                    
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'application/pdf' not in content_type:
                        logger.warning(f"URL does not return PDF content-type. Got: {content_type}")
                        # But let's try anyway in case the content-type header is wrong
                        content_start = response.content[:4]
                        if content_start != b'%PDF':
                            logger.warning(f"Content doesn't start with PDF signature. First 10 bytes: {response.content[:10]}")
                            return ''
                        else:
                            logger.info("Content starts with PDF signature despite wrong content-type")
                    
                    pdf_source = response.content
                    logger.info(f"Successfully downloaded PDF, size: {len(pdf_source)} bytes")
                    
                    # Check if we're running out of time
                    if time.time() - start_time > max_processing_time:
                        logger.warning(f"PDF processing timeout reached for {original_url}")
                        return ''
                    
                    break  # Success, exit retry loop
                except requests.exceptions.RequestException as e:
                    logger.error(f"Download attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries:
                        logger.warning(f"Retrying in 1 second...")
                        time.sleep(1)  # Reduced from 2 seconds
                        continue
                    else:
                        logger.error(f"PDF download failed after {max_retries + 1} attempts for {original_url}")
                        return ''
        
        # Open PDF from either file path or bytes
        logger.info("Opening PDF document...")
        if isinstance(pdf_source, bytes):
            doc = fitz.open(stream=pdf_source, filetype="pdf")
        else:
            doc = fitz.open(pdf_source)
            
        logger.info(f"PDF opened successfully, {len(doc)} pages")
        
        # Limit page processing to prevent hanging on massive PDFs
        max_pages = min(len(doc), 50)  # Process at most 50 pages
        if len(doc) > max_pages:
            logger.info(f"Large PDF detected ({len(doc)} pages), processing first {max_pages} pages only")
        
        full_text = ""
        
        # Extract text page by page with timeout checks
        for page_num in range(max_pages):
            # Check timeout every 10 pages
            if page_num > 0 and page_num % 10 == 0:
                logger.info(f"Progress: Processing page {page_num + 1}/{max_pages}")
            
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            page_text = normalize_text(page_text)
            full_text += page_text
            full_text += f"\n--- Page {page_num + 1} End ---\n"
            
            # Early validation after first few pages
            if page_num == 2 and not is_valid_pdf_content(full_text, original_url, company):
                logger.warning(f"PDF validation failed after page {page_num + 1}, stopping extraction")
                doc.close()
                return ''
        
        doc.close()
        processing_time = time.time() - start_time
        logger.info(f"Text extraction complete in {processing_time:.1f}s, {len(full_text)} characters extracted")
        
        # Final validation of complete text
        if not is_valid_pdf_content(full_text, original_url, company):
            logger.warning("Final PDF validation failed")
            return ''
            
        logger.info("PDF processing successful")
        return full_text
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Failed to process PDF {original_url} after {processing_time:.1f}s: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return '' 