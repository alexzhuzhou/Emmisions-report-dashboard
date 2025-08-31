# app/schemas.py (or wherever you keep Pydantic models)
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional

class SustainabilityMetricsPayload(BaseModel):
    owns_cng_fleet: bool
    cng_fleet_size_range: int
    cng_fleet_size_actual: int
    total_fleet_size: int # maps to total_truck_fleet_size_actual in JSON
    emission_report: bool
    emission_goals: int
    alt_fuels: bool
    clean_energy_partners: bool
    regulatory_pressure: bool

class MetricSourcePayload(BaseModel):
    metric_name: str
    source_url: str # Can be file URI or web URL
    contribution_text: str

class DetailedCriterionFinding(BaseModel): # For completeness if you ever want to store it
    criteria_found: bool
    score: int
    quote: str
    justification: str
    original_passage: str
    verified: bool
    evidence: str
    cng_fleet_size_actual: Optional[int] = None
    total_truck_fleet_size_actual: Optional[int] = None

class CompanySectionSummaryItem(BaseModel):
    title: str
    summary_text: str

class SourceDocumentInfo(BaseModel):
    url: str # Could be HttpUrl if you want strict validation, but str is more flexible for file paths
    title: str

class ScorecardDataCreate(BaseModel):
    company_name: str
    sustainability_metrics_payload: SustainabilityMetricsPayload
    metric_sources_payload: List[MetricSourcePayload]
    # detailed_criteria_findings: Dict[str, DetailedCriterionFinding] # Optional to receive
    company_section_summaries: Dict[str, CompanySectionSummaryItem]
    source_document_info: Optional[SourceDocumentInfo] = None
    # Add other company fields if you want to create/update them here
    website_url: Optional[str] = None # Example
    industry: Optional[str] = None    # Example