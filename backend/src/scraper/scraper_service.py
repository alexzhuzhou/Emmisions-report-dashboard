"""
Scraper Service Module
Provides a clean interface for scraper functionality with structured JSON output.
This module wraps the main scraper and export functionality to provide a consistent API.
"""

import os
import sys
from typing import Dict, Any, Optional, Set
from dotenv import load_dotenv
import logging

# Set up logging for debugging
logger = logging.getLogger(__name__)

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables with debugging
env_path = os.path.join(project_root, '.env')
logger.debug(f"ScraperService: Looking for .env file at: {env_path}")
logger.debug(f"ScraperService: .env file exists: {os.path.exists(env_path)}")

load_dotenv(dotenv_path=env_path)

# Debug environment variable loading
logger.debug(f"ScraperService: OPENAI_API_KEY loaded: {'✓' if os.getenv('OPENAI_API_KEY') else '✗'}")
logger.debug(f"ScraperService: GOOGLE_CSE_API_KEY loaded: {'✓' if os.getenv('GOOGLE_CSE_API_KEY') else '✗'}")
logger.debug(f"ScraperService: GOOGLE_CSE_ID loaded: {'✓' if os.getenv('GOOGLE_CSE_ID') else '✗'}")

# Import scraper functions
from .main_ai_scraper import analyze_company_sustainability
from .export.json_exporter import SustainabilityDataExporter
from .ai_criteria_analyzer import CriteriaEvidence


class ScraperService:
    """
    Service class that provides a clean interface to the AI scraper with structured JSON output.
    This matches the CLI format and handles all the JSON export processing internally.
    """
    
    # Criteria weights based on scorecard (must sum to 100%)
    CRITERIA_WEIGHTS = {
        "cng_fleet": 10,           # CNG Fleet Presence: 10%
        "cng_fleet_size": 25,      # CNG Fleet Size: 25%
        "emission_reporting": 10,   # Emission Reporting: 10%
        "emission_goals": 15,      # Emission Reduction Goals: 15%
        "alt_fuels": 15,           # Alternative Fuels Mentioned: 15%
        "clean_energy_partner": 15, # Clean Energy Partnerships/CNG Infrastructure: 15%
        "regulatory": 10           # Regulatory Pressure/Market Type: 10%
    }
    
    # Maximum possible scores for each criterion (from analyze_scorecard.py)
    CRITERIA_MAX_SCORES = {
        "cng_fleet": 1,           # 0=No, 1=Yes
        "cng_fleet_size": 3,      # 0=None, 1=1-10, 2=11-50, 3=51+
        "emission_reporting": 1,   # 0=No, 1=Yes
        "emission_goals": 2,      # 0=No, 1=Mentioned, 2=Timeline/SBTi
        "alt_fuels": 1,           # 0=No, 1=Yes
        "clean_energy_partner": 1, # 0=No, 1=Yes
        "regulatory": 1           # 0=No, 1=Yes
    }
    
    def __init__(self):
        """Initialize the scraper service with environment validation."""
        self.project_root = project_root
        self._validate_environment()
    
    def _validate_environment(self) -> None:
        """Validate that required environment variables are available."""
        required_vars = ["GOOGLE_CSE_API_KEY", "GOOGLE_CSE_ID", "OPENAI_API_KEY"]
        missing_vars = []
        
        logger.debug(f"ScraperService: Validating environment variables...")
        logger.debug(f"ScraperService: Project root path: {self.project_root}")
        logger.debug(f"ScraperService: Working directory: {os.getcwd()}")
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
                logger.error(f"ScraperService: Missing environment variable: {var}")
            else:
                # Show first/last 4 characters of the key for debugging
                masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
                logger.debug(f"ScraperService: Found {var}: {masked_value}")
        
        if missing_vars:
            env_file_path = os.path.join(self.project_root, '.env')
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Expected .env file location: {env_file_path}\n"
                f".env file exists: {os.path.exists(env_file_path)}\n"
                f"Current working directory: {os.getcwd()}\n"
                f"Project root: {self.project_root}\n"
                f"Please ensure your .env file contains:\n"
                + "\n".join([f"  {var}=your_{var.lower()}_here" for var in missing_vars])
            )
            logger.error(f"ScraperService: Environment validation failed:\n{error_msg}")
            raise EnvironmentError(error_msg)
    
    def analyze_company(
        self,
        company_name: str,
        criteria: Optional[Set[str]] = None,
        max_search_pages: int = 5,
        max_pdf_reports: int = 5,
        max_web_pages: int = 5,
        verbose: bool = False,
        use_crawler: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze a company's sustainability and return structured JSON format.
        
        This method provides the same structured output as the CLI version with:
        - company: Company information and metadata
        - sustainability_metrics: Boolean and numeric sustainability metrics  
        - metric_sources: Audit trail of evidence sources
        - summaries: Human-readable summaries of findings
        
        Args:
            company_name: Name of the company to analyze
            criteria: Set of criteria to analyze (defaults to all)
            max_search_pages: Maximum search result pages per query
            max_pdf_reports: Maximum number of PDF reports to analyze
            max_web_pages: Maximum number of web pages to scrape
            verbose: Whether to show detailed progress output
            use_crawler: Enable deep web crawling for comprehensive coverage
            
        Returns:
            Dict containing structured sustainability analysis results
            
        Raises:
            EnvironmentError: If required API keys are missing
            Exception: If scraper execution fails
        """
        try:
            # Step 1: Run the main AI scraper
            print(f"ScrapeService: Starting analysis for {company_name}")
            
            scraper_results = analyze_company_sustainability(
                company_name=company_name,
                criteria=criteria,
                max_search_pages=max_search_pages,
                max_pdf_reports=max_pdf_reports,
                max_web_pages=max_web_pages,
                verbose=verbose,
                use_crawler=use_crawler
            )
            
            print(f"ScrapeService: Scraper analysis completed for {company_name}")
            
            # Step 2: Process through JSON exporter for structured format
            try:
                exporter = SustainabilityDataExporter()
                
                # Set company info
                exporter.set_company_info(company_name)
                
                # Process the analysis results - Use stored evidence_details if available
                if 'evidence_details' in scraper_results:
                    # Use the original evidence_details stored during analysis
                    exporter.process_criteria_evidence(scraper_results['evidence_details'], company_name)
                else:
                    # Fallback: convert legacy format to evidence_details format for export
                    evidence_found = scraper_results.get('evidence_found', {})
                    evidence_details_for_export = {}
                    
                    for criterion, evidence_data in evidence_found.items():
                        if evidence_data.get('found', False):
                            # Create CriteriaEvidence object for export
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
                    
                    exporter.process_criteria_evidence(evidence_details_for_export, company_name)
                
                # Export to structured JSON format (same as CLI)
                structured_data = exporter.export_to_json()
                
                # Calculate and add overall score
                if "sustainability_metrics" in structured_data:
                    overall_score = self.calculate_overall_score(structured_data["sustainability_metrics"])
                    structured_data["overall_score"] = overall_score
                    print(f"ScrapeService: Overall sustainability score: {overall_score['overall_score_percentage']}%")
                else:
                    print("ScrapeService: Warning - No sustainability_metrics found, skipping overall score calculation")
                
                print(f"ScrapeService: Successfully converted to structured JSON format")
                return structured_data
                
            except Exception as e:
                print(f"ScrapeService: JSON export failed, returning raw results: {e}")
                # Fallback to raw results if JSON export fails
                return scraper_results
                
        except Exception as e:
            print(f"ScrapeService: Analysis failed for {company_name}: {e}")
            raise Exception(f"Scraper service failed: {str(e)}")
    
    def get_supported_criteria(self) -> Set[str]:
        """
        Get the set of all supported sustainability criteria.
        
        Returns:
            Set of supported criteria names
        """
        from .main_ai_scraper import ALL_CRITERIA
        return ALL_CRITERIA.copy()
    
    def validate_criteria(self, criteria: Set[str]) -> bool:
        """
        Validate that the provided criteria are supported.
        
        Args:
            criteria: Set of criteria to validate
            
        Returns:
            True if all criteria are supported, False otherwise
        """
        supported = self.get_supported_criteria()
        return criteria.issubset(supported)
    
    def calculate_overall_score(self, sustainability_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate the overall sustainability score based on weighted criteria.
        
        Args:
            sustainability_metrics: The sustainability metrics from the JSON export
            
        Returns:
            Dict containing overall score and breakdown by criteria
        """
        total_weighted_score = 0.0
        total_possible_score = 0.0
        criteria_breakdown = {}
        
        # FIXED: Map sustainability_metrics keys to our internal criteria names
        # These keys match the actual JSON output from the scraper
        metrics_mapping = {
            "owns_cng_fleet": "cng_fleet",
            "cng_fleet_size_range": "cng_fleet_size", 
            "emission_report": "emission_reporting",           # FIXED: was "emission_reporting"
            "emission_goals": "emission_goals",
            "alt_fuels": "alt_fuels",                         # FIXED: was "alt_fuels_mentioned"
            "clean_energy_partners": "clean_energy_partner",  # FIXED: was "clean_energy_partnerships"
            "regulatory_pressure": "regulatory"
        }
        
        # FIXED: Also check if fleet size range needs recalculation based on actual size
        if sustainability_metrics.get("cng_fleet_size_actual") and sustainability_metrics.get("cng_fleet_size_range") is not None:
            actual_size = sustainability_metrics["cng_fleet_size_actual"]
            current_range = sustainability_metrics["cng_fleet_size_range"]
            correct_range = self._calculate_fleet_size_range(actual_size)
            
            if correct_range != current_range:
                print(f"ScraperService: Correcting fleet size range from {current_range} to {correct_range} (actual size: {actual_size})")
                # Update the range in the metrics for correct scoring
                sustainability_metrics["cng_fleet_size_range"] = correct_range
        
        for metric_key, criterion_key in metrics_mapping.items():
            if criterion_key in self.CRITERIA_WEIGHTS:
                # Get the score from sustainability metrics
                metric_value = sustainability_metrics.get(metric_key, 0)
                
                # Handle both boolean and numeric values
                if isinstance(metric_value, bool):
                    score = 1 if metric_value else 0
                else:
                    score = int(metric_value) if metric_value is not None else 0
                
                # Get max possible score and weight for this criterion
                max_score = self.CRITERIA_MAX_SCORES[criterion_key]
                weight = self.CRITERIA_WEIGHTS[criterion_key]
                
                # Calculate normalized score (0-1) and apply weight
                if max_score > 0:
                    normalized_score = min(score / max_score, 1.0)  # Cap at 1.0
                else:
                    normalized_score = 0.0
                
                weighted_score = normalized_score * weight
                total_weighted_score += weighted_score
                total_possible_score += weight
                
                # Store breakdown for this criterion
                criteria_breakdown[criterion_key] = {
                    "name": self._get_criterion_display_name(criterion_key),
                    "raw_score": score,
                    "max_score": max_score,
                    "normalized_score": round(normalized_score * 100, 1),  # As percentage
                    "weight_percentage": weight,
                    "weighted_contribution": round(weighted_score, 1),
                    "possible_contribution": weight
                }
        
        # Calculate overall percentage
        overall_percentage = round((total_weighted_score / total_possible_score * 100), 1) if total_possible_score > 0 else 0.0
        
        return {
            "overall_score_percentage": overall_percentage,
            "total_weighted_score": round(total_weighted_score, 1),
            "total_possible_score": round(total_possible_score, 1),
            "criteria_breakdown": criteria_breakdown,
            "score_calculation": {
                "description": "Overall score calculated as weighted average of all criteria",
                "formula": "Sum of (normalized_score * weight) / Sum of all weights * 100",
                "total_criteria_evaluated": len(criteria_breakdown)
            }
        }
    
    def _calculate_fleet_size_range(self, fleet_size: int) -> int:
        """
        Calculate the correct fleet size range based on actual fleet size.
        
        Args:
            fleet_size: Actual number of CNG vehicles
            
        Returns:
            Range value: 0=None, 1=1-10, 2=11-50, 3=51+
        """
        if fleet_size == 0:
            return 0
        elif 1 <= fleet_size <= 10:
            return 1
        elif 11 <= fleet_size <= 50:
            return 2
        else:  # 51+
            return 3
    
    def _get_criterion_display_name(self, criterion_key: str) -> str:
        """Get user-friendly display name for criteria."""
        display_names = {
            "cng_fleet": "CNG Fleet Presence",
            "cng_fleet_size": "CNG Fleet Size",
            "emission_reporting": "Emission Reporting",
            "emission_goals": "Emission Reduction Goals",
            "alt_fuels": "Alternative Fuels Mentioned",
            "clean_energy_partner": "Clean Energy Partnerships/CNG Infrastructure",
            "regulatory": "Regulatory Pressure/Market Type"
        }
        return display_names.get(criterion_key, criterion_key)


# Convenience function for direct usage
def analyze_company_structured(
    company_name: str,
    criteria: Optional[Set[str]] = None,
    max_search_pages: int = 5,
    max_pdf_reports: int = 5,
    max_web_pages: int = 5,
    verbose: bool = False,
    use_crawler: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to analyze a company and get structured results.
    
    This is the main function that FastAPI routes should call.
    
    Args:
        company_name: Name of the company to analyze
        criteria: Set of criteria to analyze (defaults to all)
        max_search_pages: Maximum search result pages per query
        max_pdf_reports: Maximum number of PDF reports to analyze
        max_web_pages: Maximum number of web pages to scrape
        verbose: Whether to show detailed progress output
        use_crawler: Enable deep web crawling for comprehensive coverage
        
    Returns:
        Dict containing structured sustainability analysis results with:
        - company: Company information and metadata
        - sustainability_metrics: Boolean and numeric sustainability metrics
        - metric_sources: Audit trail of evidence sources  
        - summaries: Human-readable summaries of findings
        - overall_score: Weighted overall sustainability score with criteria breakdown
        
    Example:
        results = analyze_company_structured("Amazon")
        company_info = results["company"]
        metrics = results["sustainability_metrics"]
        sources = results["metric_sources"]
        summaries = results["summaries"]
        overall_score = results["overall_score"]
        
        # Access overall score data:
        score_percentage = overall_score["overall_score_percentage"]  # e.g., 73.5
        criteria_breakdown = overall_score["criteria_breakdown"]      # Detailed breakdown per criterion
    """
    service = ScraperService()
    return service.analyze_company(
        company_name=company_name,
        criteria=criteria,
        max_search_pages=max_search_pages,
        max_pdf_reports=max_pdf_reports,
        max_web_pages=max_web_pages,
        verbose=verbose,
        use_crawler=use_crawler
    )   