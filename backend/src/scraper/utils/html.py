"""HTML processing and text extraction utilities."""

import trafilatura
from bs4 import BeautifulSoup
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def html_to_clean_text(html: str, url: Optional[str] = None) -> str:
    """
    ENHANCED: Convert HTML to clean text using multiple extraction methods with fallbacks.
    Enhanced to extract more complete content for sustainability analysis.
    """
    if not html or len(html.strip()) < 100:
        logger.warning(f"HTML content too small or empty: {len(html) if html else 0} chars")
        return ""
    
    original_length = len(html)
    logger.debug(f"Processing HTML: {original_length} chars for {url or 'unknown URL'}")
    
    # Method 1: Enhanced Trafilatura (best for content extraction)
    try:
        # Use more aggressive settings to capture more content
        txt = trafilatura.extract(
            html, 
            include_comments=False, 
            favour_recall=True,  # Prefer recall over precision
            include_tables=True, 
            include_links=True,  # Include link text
            include_images=False,  # Skip image alt text
            deduplicate=False,  # Don't remove duplicate content (might remove important info)
            prune_xpath=None,  # Don't prune anything
            only_with_metadata=False  # Don't require metadata
        )
        if txt and len(txt.strip()) > 50:
            logger.debug(f"Enhanced Trafilatura extraction successful: {len(txt)} chars")
            return txt.strip()
        else:
            logger.debug(f"Enhanced Trafilatura extraction failed or too short: {len(txt) if txt else 0} chars")
    except Exception as e:
        logger.debug(f"Enhanced Trafilatura extraction failed: {e}")
    
    # Method 2: Aggressive BeautifulSoup extraction (keep more content)
    try:
        soup = BeautifulSoup(html, "lxml")
        
        # Remove only the most problematic elements (keep nav, footer, header for sustainability info)
        for script in soup(["script", "style", "noscript", "iframe", "object", "embed"]):
            script.decompose()
        
        # Get text with better spacing
        txt = soup.get_text(separator=" ", strip=True)
        
        # Clean up whitespace
        txt = re.sub(r'\s+', ' ', txt).strip()
        
        if txt and len(txt) > 50:
            logger.debug(f"Aggressive BeautifulSoup extraction successful: {len(txt)} chars")
            return txt
        else:
            logger.debug(f"Aggressive BeautifulSoup extraction failed or too short: {len(txt) if txt else 0} chars")
    except Exception as e:
        logger.debug(f"Aggressive BeautifulSoup extraction failed: {e}")
    
    # Method 3: Conservative BeautifulSoup extraction (fallback)
    try:
        soup = BeautifulSoup(html, "html.parser")  # Use different parser
        
        # Remove script and style elements (more conservative)
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text with better spacing
        txt = soup.get_text(separator=" ", strip=True)
        
        # Clean up whitespace
        txt = re.sub(r'\s+', ' ', txt).strip()
        
        if txt and len(txt) > 50:
            logger.debug(f"Conservative BeautifulSoup extraction successful: {len(txt)} chars")
            return txt
        else:
            logger.debug(f"Conservative BeautifulSoup extraction failed or too short: {len(txt) if txt else 0} chars")
    except Exception as e:
        logger.debug(f"Conservative BeautifulSoup extraction failed: {e}")
    
    # Method 4: Enhanced regex-based extraction (last resort)
    try:
        # Remove HTML tags but keep text content
        txt = re.sub(r'<[^>]+>', ' ', html)
        # Remove extra whitespace
        txt = re.sub(r'\s+', ' ', txt).strip()
        # Remove common HTML entities
        txt = txt.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        txt = txt.replace('&quot;', '"').replace('&#39;', "'").replace('&apos;', "'")
        
        if txt and len(txt) > 50:
            logger.debug(f"Enhanced regex extraction successful: {len(txt)} chars")
            return txt
        else:
            logger.debug(f"Enhanced regex extraction failed or too short: {len(txt) if txt else 0} chars")
    except Exception as e:
        logger.debug(f"Enhanced regex extraction failed: {e}")
    
    # All methods failed
    logger.warning(f"All text extraction methods failed for {url or 'unknown URL'}. HTML length: {original_length}")
    return ""




