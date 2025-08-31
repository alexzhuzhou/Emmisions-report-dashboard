import json
import logging
import re
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, asdict
from pathlib import Path

from ..ai_criteria_analyzer import CriteriaEvidence

logger = logging.getLogger(__name__)

# Module-level constants
FLEET_SIZE_PATTERNS = [
    r'(\d+(?:,\d+)*)\s*(?:trucks|vehicles)',
    r'(\d+(?:,\d+)*)',  # any number
]

TARGET_YEAR_PATTERNS = [
    re.compile(r'by\s*(\d{4})', re.IGNORECASE),
    re.compile(r'(\d{4})\s*target', re.IGNORECASE),
    re.compile(r'achieve.*?(\d{4})', re.IGNORECASE),
    re.compile(r'goal.*?(\d{4})', re.IGNORECASE),
]

class ExportError(Exception):
    """Custom exception for JSON export errors"""
    pass

@dataclass
class CompanyInfo:
    """Company information structure"""
    company_name: str
    company_summary: str = ""
    website_url: str = ""
    industry: str = ""
    cso_linkedin_url: str = ""

@dataclass
class SustainabilityMetrics:
    """Sustainability metrics with boolean/integer values"""
    owns_cng_fleet: Optional[bool] = None
    cng_fleet_size_range: Optional[int] = None  # 0-3 range code
    cng_fleet_size_actual: Optional[int] = None  # actual number
    total_fleet_size: Optional[int] = None
    emission_report: Optional[bool] = None
    emission_goals: Optional[int] = None  # 0-2 range code
    alt_fuels: Optional[bool] = None
    clean_energy_partners: Optional[bool] = None
    regulatory_pressure: Optional[bool] = None

@dataclass
class MetricSource:
    """Source information for metrics"""
    metric_name: List[str]  # Always a list for consistency
    source_url: str
    contribution_text: str

@dataclass
class SimpleSummary:
    """Generic summary structure"""
    metric_name: str
    summary_text: str = ""

@dataclass
class EmissionsSummary:
    """Emissions-related summary with additional fields"""
    metric_name: str = "emission_report"
    emissions_summary: str = ""
    emissions_goals_summary: str = ""
    current_emissions: Optional[int] = None
    target_year: Optional[int] = None
    target_emissions: Optional[int] = None

@dataclass
class Summaries:
    """All summary blocks"""
    fleet_summary: SimpleSummary
    emissions_summary: EmissionsSummary
    alt_fuels_summary: SimpleSummary
    clean_energy_partners_summary: SimpleSummary
    regulatory_pressure_summary: SimpleSummary

@dataclass
class ExportData:
    """Complete export data structure"""
    company: CompanyInfo
    sustainability_metrics: SustainabilityMetrics
    metric_sources: List[MetricSource]
    summaries: Summaries

class SustainabilityDataExporter:
    """Main exporter class for converting analysis results to JSON"""
    
    def __init__(self):
        self.company_info = None
        self.metrics = SustainabilityMetrics()
        self.metric_sources = []
        self.summaries = None
        self._processed_evidence = False
        self._evidence_cache = {}  # Store evidence for detailed summaries
        self._enhanced_evidence_cache = {}  # Store enhanced evidence data (justifications, confidence, etc.)
        
    def set_company_info(self, company_name: str, website_url: str = "", 
                        industry: str = "", cso_linkedin_url: str = ""):
        """Set basic company information"""
        if not company_name or not company_name.strip():
            raise ExportError("Company name cannot be empty")
            
        self.company_info = CompanyInfo(
            company_name=company_name.strip(),
            company_summary="",  # Will be generated at export time
            website_url=website_url.strip(),
            industry=industry.strip(),
            cso_linkedin_url=cso_linkedin_url.strip()
        )
    
    def process_criteria_evidence(self, evidence_dict: Dict[str, CriteriaEvidence], 
                                company_name: str) -> None:
        """Process evidence from CriteriaEvidence objects"""
        
        def get_fields(criterion, evidence):
            if not (hasattr(evidence, "criterion") and hasattr(evidence, "found")):
                logger.warning(f"Skipping criterion {criterion}: bad evidence object {type(evidence)}")
                return None
            if not evidence.found:
                return None
            # Extract all relevant fields from CriteriaEvidence
            return (
                evidence.score, 
                evidence.evidence_text.strip(), 
                evidence.url.strip(),
                evidence.justification.strip(),
                evidence.extracted_number,
                evidence.extracted_unit,
                evidence.confidence,
                evidence.source_type,
                evidence.verified,
                evidence.full_context.strip() if hasattr(evidence, 'full_context') and evidence.full_context else ""
            )
        
        self._ingest_evidence(evidence_dict.items(), get_fields)
    
    def _ingest_evidence(self, items, get_fields_cb):
        """Common evidence ingestion logic"""
        if not items:
            logger.warning("No evidence provided")
            return
            
        # Group sources by URL
        sources_by_url = {}
        
        # Track if any evidence was actually processed
        evidence_processed = False
        
        for criterion, item in items:
            fields = get_fields_cb(criterion, item)
            if not fields:
                continue
                
            # Unpack all fields from get_fields
            if len(fields) == 3:
                # Legacy format (score, evidence_text, url)
                score, evidence_text, url = fields
                justification, extracted_number, extracted_unit, confidence, source_type, verified, full_context = None, None, None, 0, "unknown", False, ""
            elif len(fields) == 9:
                # Previous format without full_context
                score, evidence_text, url, justification, extracted_number, extracted_unit, confidence, source_type, verified = fields
                full_context = ""
            else:
                # New format with all fields including full_context
                score, evidence_text, url, justification, extracted_number, extracted_unit, confidence, source_type, verified, full_context = fields
            
            # Store evidence for detailed summaries
            self._evidence_cache[criterion] = evidence_text
            
            # Store enhanced evidence data for potential use in summaries
            self._enhanced_evidence_cache[criterion] = {
                'evidence_text': evidence_text,
                'full_context': full_context,
                'justification': justification,
                'confidence': confidence,
                'source_type': source_type,
                'verified': verified,
                'extracted_number': extracted_number,
                'extracted_unit': extracted_unit
            }
            
            # Set metric value with additional context
            self._set_metric_value(criterion, score, evidence_text, extracted_number, extracted_unit, confidence, source_type, verified)
            evidence_processed = True  # Mark that we processed at least one piece of evidence
            
            # Track source information with enhanced metadata
            if url:
                if url not in sources_by_url:
                    sources_by_url[url] = {
                        'metrics': [], 
                        'longest_text': evidence_text,  # Use evidence_text directly
                        'confidence_scores': [],
                        'source_types': set(),
                        'verification_status': [],
                        'justifications': []
                    }
                
                sources_by_url[url]['metrics'].append(criterion)
                sources_by_url[url]['confidence_scores'].append(confidence)
                sources_by_url[url]['source_types'].add(source_type)
                sources_by_url[url]['verification_status'].append(verified)
                if justification:
                    sources_by_url[url]['justifications'].append(justification)
                
                # Use evidence_text as the contribution text (changed from priority system)
                current_text = evidence_text
                
                if len(current_text) > len(sources_by_url[url]['longest_text']):
                    sources_by_url[url]['longest_text'] = current_text
        
        # Set the processed flag AFTER the loop completes
        self._processed_evidence = evidence_processed
        
        # Create metric sources from grouped data with enhanced metadata
        for url, source_data in sources_by_url.items():
            # Calculate average confidence for this source
            avg_confidence = sum(source_data['confidence_scores']) / len(source_data['confidence_scores']) if source_data['confidence_scores'] else 0
            # Get primary source type (most common)
            primary_source_type = max(source_data['source_types'], key=lambda x: list(source_data['source_types']).count(x)) if source_data['source_types'] else "unknown"
            # Check if any evidence from this source was verified
            any_verified = any(source_data['verification_status'])
            
            metric_source = MetricSource(
                metric_name=source_data['metrics'],
                source_url=url,
                contribution_text=source_data['longest_text']
            )
            self.metric_sources.append(metric_source)
            
            # Log source quality information
            logger.info(f"Source {url}: {len(source_data['metrics'])} metrics, avg confidence: {avg_confidence:.1f}%, "
                       f"source type: {primary_source_type}, verified: {any_verified}")
        
        if not self._processed_evidence:
            logger.warning("No valid evidence data was processed")
    
    def _set_metric_value(self, criterion: str, score: Optional[int], evidence_text: str, 
                         extracted_number: Optional[int] = None, extracted_unit: Optional[str] = None,
                         confidence: int = 0, source_type: str = "unknown", verified: bool = False) -> None:
        """Unified metric value setter with enhanced data extraction"""
        # Handle None and float scores properly
        if score is None:
            score = 0
        else:
            # Convert to int, handling floats properly
            try:
                score = int(round(float(score)))
            except (ValueError, TypeError):
                logger.warning(f"Invalid score type for {criterion}: {type(score)} - using 0")
                score = 0
        
        evidence_lower = evidence_text.lower() if evidence_text else ""
        
        if criterion == 'cng_fleet':
            if score > 0:
                self.metrics.owns_cng_fleet = True
            else:
                # Check if we have explicit "no CNG" evidence vs just no evidence
                if any(phrase in evidence_lower for phrase in ['no cng', 'not cng', 'without cng', 'do not have cng']):
                    self.metrics.owns_cng_fleet = False
            
        elif criterion == 'cng_fleet_size':
            self.metrics.cng_fleet_size_range = max(0, min(3, score))
            # Set CNG fleet size actual number if available
            if extracted_number is not None and extracted_number > 0:
                self.metrics.cng_fleet_size_actual = extracted_number
                logger.info(f"Using AI-extracted CNG fleet size: {extracted_number} {extracted_unit or 'vehicles'}")
            else:
                # No valid extracted number available
                self.metrics.cng_fleet_size_actual = None
                logger.info("No valid CNG fleet size extracted by AI")
            
            # LOGICAL FIX: If we have CNG fleet size evidence, we must have a CNG fleet
            if self.metrics.cng_fleet_size_actual and self.metrics.cng_fleet_size_actual > 0:
                self.metrics.owns_cng_fleet = True
                logger.info(f"Setting owns_cng_fleet=True based on extracted fleet size: {self.metrics.cng_fleet_size_actual}")
            else:
                # Only set to False if we have evidence but no fleet size
                # (don't override if we have no evidence at all)
                if evidence_text and 'cng' in evidence_text.lower():
                    self.metrics.owns_cng_fleet = False
                    logger.info("Setting owns_cng_fleet=False - CNG mentioned but no fleet size found")
            
        elif criterion == 'total_truck_fleet_size':
            # Set total fleet size actual number if available
            if extracted_number is not None and extracted_number > 0:
                self.metrics.total_fleet_size = extracted_number
                logger.info(f"Using AI-extracted total fleet size: {extracted_number} {extracted_unit or 'vehicles'}")
            else:
                # No valid extracted number available
                self.metrics.total_fleet_size = None
                logger.info("No valid total fleet size extracted by AI")
            
        elif criterion == 'emission_reporting':
            if score > 0:
                self.metrics.emission_report = True
            else:
                if any(phrase in evidence_lower for phrase in ['no report', 'not report', 'do not publish']):
                    self.metrics.emission_report = False
            
        elif criterion == 'emission_goals':
            self.metrics.emission_goals = max(0, min(2, score))
            
        elif criterion == 'alt_fuels':
            if score > 0:
                self.metrics.alt_fuels = True
            else:
                if any(phrase in evidence_lower for phrase in ['no alternative', 'not alternative', 'only diesel']):
                    self.metrics.alt_fuels = False
            
        elif criterion == 'clean_energy_partner':
            if score > 0:
                self.metrics.clean_energy_partners = True
            else:
                if any(phrase in evidence_lower for phrase in ['no partner', 'not partner', 'no clean energy']):
                    self.metrics.clean_energy_partners = False
            
        elif criterion == 'regulatory':
            if score > 0:
                self.metrics.regulatory_pressure = True
            else:
                if any(phrase in evidence_lower for phrase in ['not subject', 'no regulation', 'not regulated']):
                    self.metrics.regulatory_pressure = False
    

    
    def _extract_target_year(self, text: str) -> Optional[int]:
        """Extract target year using pre-compiled patterns"""
        if not text:
            return None
            
        for pattern in TARGET_YEAR_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    year = int(match.group(1))
                    if 2020 <= year <= 2100:  # Reasonable range for targets
                        return year
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def _create_summaries_from_justifications(self) -> None:
        """Create summaries using AI-generated justifications from CriteriaEvidence objects"""
        
        # Map criteria to summary fields
        criteria_to_summary = {
            'cng_fleet': 'fleet_summary',
            'cng_fleet_size': 'fleet_summary',  # Both CNG criteria go to fleet summary
            'emission_reporting': 'emissions_summary',
            'emission_goals': 'emissions_summary',  # Both emission criteria go to emissions summary
            'alt_fuels': 'alt_fuels_summary',
            'clean_energy_partner': 'clean_energy_partners_summary',
            'regulatory': 'regulatory_pressure_summary'
        }
        
        # Initialize summary texts with defaults
        fleet_text = "No CNG fleet information found."
        emissions_text = "No emission reporting information found."
        goals_text = "No emission goals information found."
        alt_fuels_text = "No alternative fuels information found."
        partners_text = "No clean energy partnerships information found."
        regulatory_text = "No regulatory pressure information found."
        
        # Extract target year for emissions goals
        target_year = None
        
        # Process each criterion's justification
        for criterion, evidence_data in self._enhanced_evidence_cache.items():
            justification = evidence_data.get('justification', '')
            if not justification:
                continue
                
            # Map to appropriate summary
            if criterion in criteria_to_summary:
                summary_field = criteria_to_summary[criterion]
                
                if summary_field == 'fleet_summary':
                    fleet_text = justification
                elif summary_field == 'emissions_summary':
                    if criterion == 'emission_reporting':
                        emissions_text = justification
                    elif criterion == 'emission_goals':
                        goals_text = justification
                        # Try to extract target year from justification
                        target_year = self._extract_target_year(justification)
                elif summary_field == 'alt_fuels_summary':
                    alt_fuels_text = justification
                elif summary_field == 'clean_energy_partners_summary':
                    partners_text = justification
                elif summary_field == 'regulatory_pressure_summary':
                    regulatory_text = justification
        
        # Create the summaries object
        self.summaries = Summaries(
            fleet_summary=SimpleSummary("owns_cng_fleet", fleet_text),
            emissions_summary=EmissionsSummary(
                emissions_summary=emissions_text,
                emissions_goals_summary=goals_text,
                target_year=target_year
            ),
            alt_fuels_summary=SimpleSummary("alt_fuels", alt_fuels_text),
            clean_energy_partners_summary=SimpleSummary("clean_energy_partners", partners_text),
            regulatory_pressure_summary=SimpleSummary("regulatory_pressure", regulatory_text)
        )
    
    def _create_company_summary(self) -> str:
        
        if not self.company_info:
            return ""
        
        company_name = self.company_info.company_name
        industry = self.company_info.industry
        
        # Extract key facts for structured paragraphs
        sustainability_facts = []
        transportation_facts = []
        
        # Paragraph 1: Sustainability reporting and goals
        if self.metrics.emission_report is True:
            sustainability_facts.append("has published a comprehensive sustainability report")
        elif self.metrics.emission_report is False:
            sustainability_facts.append("does not currently publish formal emission reports, though this may reflect different reporting priorities or frameworks")
        
        # Emission goals with target year and strategy details
        if self.metrics.emission_goals and self.metrics.emission_goals > 0:
            target_year = None
            for source in self.metric_sources:
                if 'emission_goals' in source.metric_name:
                    target_year = self._extract_target_year(source.contribution_text)
                    break
            
            if target_year:
                if self.metrics.emission_goals == 2:
                    sustainability_facts.append(f"has established ambitious emissions reduction goals, including specific net-zero carbon emission targets across its operations by {target_year}")
                else:
                    sustainability_facts.append(f"has implemented structured emissions reduction initiatives with defined targets for {target_year}")
            else:
                if self.metrics.emission_goals == 2:
                    sustainability_facts.append("has established comprehensive emissions reduction goals including detailed net-zero carbon targets and measurable milestones")
                else:
                    sustainability_facts.append("has implemented emissions reduction goals as part of its environmental strategy")
        elif self.metrics.emission_goals is not None and self.metrics.emission_goals == 0:
            sustainability_facts.append("has not yet established formal emissions reduction goals, which may indicate either early-stage sustainability planning or alternative environmental focus areas")
        
        # Strategy details for paragraph 1
        strategy_elements = []
        if self.metrics.clean_energy_partners is True:
            strategy_elements.append("investing in carbon-free energy solutions and infrastructure")
            strategy_elements.append("collaborating with partners to broaden environmental impact and leverage shared resources")
        elif self.metrics.clean_energy_partners is False:
            strategy_elements.append("focusing on internal operational improvements rather than external clean energy partnerships")
        
        # Regulatory context
        if self.metrics.regulatory_pressure is True:
            strategy_elements.append("responding to regulatory requirements and compliance frameworks in their operational regions")
        elif self.metrics.regulatory_pressure is False:
            strategy_elements.append("proactively addressing environmental concerns beyond current regulatory requirements")
        
        # Paragraph 2: Transportation operations and fleet details
        if self.metrics.owns_cng_fleet is True:
            if self.metrics.cng_fleet_size_actual:
                transportation_facts.append(f"operates a compressed natural gas (CNG) fleet consisting of {self.metrics.cng_fleet_size_actual:,} vehicles, representing a significant investment in cleaner fuel technology")
            else:
                transportation_facts.append("operates compressed natural gas (CNG) trucks as part of its commitment to reducing transportation emissions")
        elif self.metrics.owns_cng_fleet is False:
            transportation_facts.append("does not currently operate CNG vehicles, potentially focusing on other emission reduction strategies or fuel alternatives")
        
        # Total fleet context
        if self.metrics.total_fleet_size:
            if self.metrics.owns_cng_fleet is True and self.metrics.cng_fleet_size_actual:
                cng_percentage = (self.metrics.cng_fleet_size_actual / self.metrics.total_fleet_size) * 100
                transportation_facts.append(f"maintains a total fleet of {self.metrics.total_fleet_size:,} vehicles, with CNG vehicles representing approximately {cng_percentage:.1f}% of the fleet")
            else:
                transportation_facts.append(f"operates a substantial transportation fleet of {self.metrics.total_fleet_size:,} vehicles across its operations")
        elif self.metrics.owns_cng_fleet is True:
            transportation_facts.append("maintains fleet operations with a focus on natural gas technology integration")
        
        # Alternative fuels in transportation context
        if self.metrics.alt_fuels is True:
            fuel_types = []
            for source in self.metric_sources:
                if 'alt_fuels' in source.metric_name:
                    text = source.contribution_text.lower()
                    if 'biodiesel' in text:
                        fuel_types.append('biodiesel')
                    if any(term in text for term in ['biogas', 'rng', 'renewable natural gas']):
                        fuel_types.append('renewable natural gas')
                    if 'hydrogen' in text:
                        fuel_types.append('hydrogen')
                    if 'electric' in text:
                        fuel_types.append('electric')
                    break
            
            if fuel_types:
                transportation_facts.append(f"has diversified its fuel portfolio by incorporating alternative fuels including {', '.join(fuel_types)}, demonstrating a multi-faceted approach to emission reduction")
            else:
                transportation_facts.append("actively utilizes alternative fuels in its operations, indicating a strategic commitment to sustainable transportation solutions")
        elif self.metrics.alt_fuels is False:
            transportation_facts.append("currently relies on conventional fuel sources, though this may reflect operational considerations or regional fuel availability constraints")
        
        # Build the structured summary
        paragraphs = []
        
        # Paragraph 1: Sustainability reporting and strategy (always create)
        if sustainability_facts:
            first_paragraph = f"{company_name} demonstrates environmental awareness through multiple channels. The company {sustainability_facts[0]}."
            
            # Add additional sustainability facts
            if len(sustainability_facts) > 1:
                for i, fact in enumerate(sustainability_facts[1:], 1):
                    if i == 1:
                        first_paragraph += f" Furthermore, the company {fact}."
                    else:
                        first_paragraph += f" Additionally, {company_name} {fact}."
            
            # Add strategy details with enhanced context
            if strategy_elements:
                if len(strategy_elements) == 1:
                    first_paragraph += f" The company's environmental strategy encompasses {strategy_elements[0]}."
                else:
                    strategy_text = ", ".join(strategy_elements[:-1]) + f", and {strategy_elements[-1]}"
                    first_paragraph += f" To achieve these environmental objectives, the company has outlined a comprehensive strategy that includes {strategy_text}."
            elif not strategy_elements and len(sustainability_facts) > 0:
                # Add generic strategy context when no specific strategy elements found
                first_paragraph += f" This environmental focus reflects {company_name}'s recognition of sustainability as an important business consideration."
        else:
            # Create paragraph even with minimal sustainability data
            first_paragraph = f"{company_name} operates in an evolving environmental landscape."
            if industry:
                first_paragraph += f" As a company in the {industry} sector, environmental considerations are increasingly relevant to operational planning and stakeholder expectations."
            else:
                first_paragraph += " The company's environmental approach may be developing or may focus on areas not captured in standard sustainability reporting frameworks."
        
        paragraphs.append(first_paragraph)
        
        # Paragraph 2: Transportation and fleet operations (always create)
        if transportation_facts:
            if self.metrics.owns_cng_fleet is True or self.metrics.total_fleet_size:
                second_paragraph = f"Regarding transportation operations and fleet management, {company_name} has made specific infrastructure investments that impact its environmental footprint."
            else:
                second_paragraph = f"In terms of transportation and logistics operations, {company_name} manages various operational considerations that influence its environmental impact."
            
            # Add transportation facts with connecting language
            for i, fact in enumerate(transportation_facts):
                if i == 0:
                    second_paragraph += f" The company {fact}."
                else:
                    second_paragraph += f" Additionally, the organization {fact}."
            
            # Add fleet context conclusion
            if self.metrics.owns_cng_fleet is True:
                second_paragraph += " This investment in natural gas technology represents a strategic approach to balancing operational efficiency with environmental responsibility."
            elif transportation_facts:
                second_paragraph += " These fleet management decisions reflect the company's approach to balancing operational requirements with environmental considerations."
            else:
                second_paragraph += " The company's transportation strategy appears to prioritize operational efficiency while considering environmental factors."
        else:
            # Create transportation paragraph even with minimal data
            second_paragraph = f"Regarding transportation and fleet operations, {company_name} manages logistics infrastructure that plays a role in its overall environmental profile."
            if industry and any(transport_word in industry.lower() for transport_word in ['transport', 'logistics', 'shipping', 'delivery', 'freight']):
                second_paragraph += f" As a {industry} company, transportation operations are central to the business model and represent both operational priorities and environmental considerations."
            else:
                second_paragraph += " While specific fleet details were not identified, transportation and logistics decisions remain important factors in the company's environmental footprint."
            second_paragraph += " The company's approach to fleet management and fuel choices reflects broader industry trends toward operational efficiency and environmental awareness."
        
        paragraphs.append(second_paragraph)
        
        return "\n\n".join(paragraphs)
    
    def export_to_json(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export all collected data to JSON format with validation"""
        
        # Validate inputs
        if not self.company_info:
            raise ExportError("Company info must be set before exporting. Call set_company_info() first.")
        
        if not self._processed_evidence:
            logger.warning("No evidence data was processed. The export will contain only default/null values.")
        
        # Generate summaries from AI justifications
        self._create_summaries_from_justifications()
        
        # Generate company summary at export time
        self.company_info.company_summary = self._create_company_summary()
        
        # Validate that we have some meaningful data
        metrics_dict = asdict(self.metrics)
        has_any_metrics = any(value is not None for value in metrics_dict.values())
        
        if not has_any_metrics:
            logger.warning("No sustainability metrics were found. Export will contain all null values.")
        
        # Create the complete export structure
        export_data = ExportData(
            company=self.company_info,
            sustainability_metrics=self.metrics,
            metric_sources=self.metric_sources,
            summaries=self.summaries
        )
        
        # Convert to dictionary
        export_dict = asdict(export_data)
        
        # Basic validation
        self._validate_export_data(export_dict)
        
        # Write to file if path provided
        if output_path:
            self._write_json_file(export_dict, output_path)
        
        return export_dict
    
    def _validate_export_data(self, data: Dict[str, Any]) -> None:
        """Validate the export data structure"""
        try:
            # Check required top-level keys
            required_keys = {'company', 'sustainability_metrics', 'metric_sources', 'summaries'}
            missing_keys = required_keys - set(data.keys())
            if missing_keys:
                raise ExportError(f"Missing required keys in export data: {missing_keys}")
            
            # Validate company info
            company = data['company']
            if not company.get('company_name'):
                raise ExportError("Company name is required but missing")
            
            # Validate metric sources structure
            for i, source in enumerate(data['metric_sources']):
                if not isinstance(source.get('metric_name'), list):
                    raise ExportError(f"metric_sources[{i}].metric_name must be a list, got {type(source.get('metric_name'))}")
                
                if not source.get('source_url'):
                    logger.warning(f"metric_sources[{i}] has empty source_url")
            
            logger.debug("Export data validation passed")
            
        except Exception as e:
            raise ExportError(f"Export data validation failed: {e}")
    
    def _write_json_file(self, data: Dict[str, Any], output_path: str) -> None:
        """Write JSON data to file with enhanced error handling"""
        try:
            output_file = Path(output_path)
            
            # Create parent directories if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if we can write to the file
            if output_file.exists() and not output_file.is_file():
                raise ExportError(f"Output path exists but is not a file: {output_path}")
            
            # Write with UTF-8 encoding and proper formatting
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
                
            logger.info(f"Successfully exported data to {output_path}")
            
            # Log some summary stats
            metrics_count = sum(1 for v in data['sustainability_metrics'].values() if v is not None and v is not False)
            sources_count = len(data['metric_sources'])
            logger.info(f"Export summary: {metrics_count} metrics found, {sources_count} sources tracked")
            
        except PermissionError:
            raise ExportError(f"Permission denied writing to {output_path}")
        except OSError as e:
            raise ExportError(f"OS error writing to {output_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to write JSON file {output_path}: {e}")
            raise ExportError(f"Failed to write JSON file: {e}") 