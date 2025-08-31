"""
Scraper package for extracting sustainability data from company websites.

Enhanced with AI-based analysis using proven analyze_scorecard.py logic.
"""

# Main AI scraper functions (primary interface)
from .main_ai_scraper import (
    analyze_company_sustainability,
    ALL_CRITERIA
)

# Core utilities that external users might need
from .utils.pdf import extract_pdf_content
from .ai_criteria_analyzer import CriteriaEvidence

__all__ = [
    # Main AI scraper (primary interface)
    'analyze_company_sustainability',
    'ALL_CRITERIA',
    
    # Core utilities
    'extract_pdf_content',
    'CriteriaEvidence'
] 