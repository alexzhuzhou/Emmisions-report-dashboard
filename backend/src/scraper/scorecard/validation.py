"""Validation logic for sustainability criteria evidence."""

import re
import logging
from typing import Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CriteriaEvidence:
    """Evidence found for a specific criterion - preserves full context"""
    criterion: str
    found: bool
    score: int  # 0-3 score (matches AI output and system expectations)
    evidence_text: str  # The specific quote/evidence
    full_context: str   # The full original passage for verification
    justification: str  # AI's reasoning with rubric reference
    url: str
    source_type: str = "web_content"  # web_content, search_snippet, pdf_content
    verified: bool = False  # Whether the evidence was verified by the AI
    search_title: str = ""  # For search snippet evidence
    full_snippet: str = ""  # For search snippet evidence
    
    # NEW: Extracted numeric data for fleet size criteria
    extracted_number: Optional[int] = None  # The actual numeric value (e.g., 3500)
    extracted_unit: Optional[str] = None    # The unit (e.g., "vehicles", "trucks")
    numeric_range: Optional[Tuple[int, int]] = None   # For ranges like "5,000-10,000 vehicles"


def validate_evidence_against_rubric(evidence: CriteriaEvidence) -> CriteriaEvidence:
    """Validate evidence against scoring rubric and clamp scores to valid ranges"""
    from ..analyze_scorecard import CRITERIA_DB_MAPPING_SCORES
    
    criterion = evidence.criterion
    max_score = CRITERIA_DB_MAPPING_SCORES.get(criterion, (0, 3))[1]
    
    # Additional validation for evidence quality
    if evidence.found:
        # RELAXED: Check if evidence text is too short to be meaningful (reduced from 10 to 5)
        if len(evidence.evidence_text.strip()) < 5:
            print(f"[WARN] Evidence for {criterion} too short, marking as not found")
            evidence.found = False
            evidence.score = 0
            evidence.evidence_text = "No meaningful evidence found"
            return evidence
        
        # RELAXED: Only reject truly generic phrases, allow approximate language
        truly_generic_phrases = [
            "no explicit mention",
            "not explicitly stated", 
            "does not provide specific",
            "no clear evidence"
            # REMOVED: "operates approximately" and "competitive market" as these might contain useful info
        ]
        
        if any(phrase in evidence.evidence_text.lower() for phrase in truly_generic_phrases):
            print(f"[WARN] Generic evidence for {criterion}, marking as not found")
            evidence.found = False
            evidence.score = 0
            evidence.evidence_text = "No meaningful evidence found"
            return evidence
        
        # Criterion-specific validation
        if criterion == "cng_fleet":
            # Must explicitly mention CNG vehicles in operation
            if not any(term in evidence.evidence_text.lower() for term in ["cng", "compressed natural gas", "natural gas vehicle"]):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No CNG fleet evidence found"
                return evidence
        
        elif criterion == "cng_fleet_size":
            # RELAXED: Allow mixed context if vehicle numbers are present
            has_number = any(char.isdigit() for char in evidence.evidence_text)
            has_vehicle = any(term in evidence.evidence_text.lower() for term in [
                'truck', 'vehicle', 'fleet', 'trailer', 'tractor', 'semi-truck', 'semi truck',
                'cngs', 'cng trucks', 'cng vehicles', 'natural gas vehicles', 'natural gas trucks',
                'compressed natural gas vehicles', 'compressed natural gas trucks'
            ])
            
            # BALANCED VALIDATION: Alternative fuel vs CNG-only distinction
            alternative_fuel_terms = [
                'alternative fuel', 'alternative fuel and advanced technology', 'total alternative fuel',
                'alternative fuel vehicles', 'alternative fuel and technology', 'alt fuel',
                'alternative fuel fleet', 'alternative fuel and advanced', 'clean fuel vehicles'
            ]
            
            # Check if this mentions alternative fuel numbers without CNG-specific breakdown
            has_alt_fuel_language = any(term in evidence.evidence_text.lower() for term in alternative_fuel_terms)
            
            # If it mentions alternative fuel + number, check if it ALSO has CNG-specific terms
            if has_alt_fuel_language and has_number:
                # Look for CNG-specific qualifiers in the same text (expanded list)
                cng_specific_terms = [
                    'cng', 'compressed natural gas', 'natural gas only', 'cng vehicles',
                    'cng trucks', 'cng tractors', 'cng portion', 'cng-powered',
                    'natural gas powered', 'natural gas-powered', 'of which', 'including',
                    # Additional CNG-specific terms
                    'natural gas', 'lng', 'liquefied natural gas', 'cng fleet',
                    'natural gas fleet', 'gas vehicles', 'gas trucks', 'gas-powered'
                ]
                
                has_cng_specific = any(term in evidence.evidence_text.lower() for term in cng_specific_terms)
                
                # IMPROVED: Instead of outright rejection, reduce confidence and add warning
                if not has_cng_specific:
                    # Log the potential issue but don't reject entirely
                    logger.warning(f"CNG fleet size evidence mentions alternative fuel without CNG-specific breakdown: {evidence.evidence_text[:100]}")
                    
                    # Reduce score significantly but don't reject completely  
                    if hasattr(evidence, 'score') and evidence.score > 1:
                        evidence.score = min(evidence.score, 1)  # Cap at low confidence (0-3 scale)
                    
                    # Add warning to justification instead of rejecting
                    if hasattr(evidence, 'justification'):
                        evidence.justification += " [WARNING: Alternative fuel context without clear CNG breakdown]"
                    else:
                        evidence.justification = "Alternative fuel context detected - may need verification"
                    
                    # Don't return early - continue with other validation
                else:
                    logger.info(f"CNG fleet size evidence has both alternative fuel context and CNG-specific terms - accepting")
            
            # STRICT REJECTION: Fuel consumption indicators (keep this strict)
            fuel_consumption_indicators = [
                'gallons', 'liters', 'consumption', 'fuel', 'delivered', 'consumed',
                'diesel equivalent', 'mmbtu', 'therms', 'energy content',
                'fuel data', 'fuel usage', 'fuel statistics', 'gallons of', 'liters of'
            ]
            has_fuel_only = any(indicator in evidence.evidence_text.lower() for indicator in fuel_only_indicators)
            
            # STRICT REJECTION: Parts/valve context (keep this strict)
            has_parts_context = any(term in evidence.evidence_text.lower() for term in [
                'valve', 'k5t', 'oe number', 'part number', 'replacement', 'spare', 'component',
                'egr', 'catalog', 'parts list', 'inventory'
            ])
            
            # Only reject if it's PURELY fuel consumption or parts without any vehicle fleet context
            if (has_fuel_only and not (has_number and has_vehicle)) or (has_parts_context and not (has_number and has_vehicle)):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "Invalid context (fuel only or parts only), need vehicle count"
                return evidence
            
            if not (has_number and has_vehicle):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No valid CNG fleet size data found"
                return evidence
        
        elif criterion == "total_truck_fleet_size":
            # RELAXED: Allow some mixed context if vehicle numbers are clearly present
            has_number = any(char.isdigit() for char in evidence.evidence_text)
            has_vehicle = any(term in evidence.evidence_text.lower() for term in [
                'truck', 'vehicle', 'fleet', 'trailer', 'tractor', 'semi-truck', 'semi truck',
                'vehicles', 'trucks', 'tractors', 'total fleet', 'operates', 'maintains'
            ])
            
            # RELAXED: Only reject clearly invalid contexts, allow some mixed data
            clearly_invalid_contexts = [
                # Only employee-only references
                'employees only', 'workforce only', 'staff only', 'jobs only',
                # Only fuel consumption without vehicle context
                'gallons only', 'consumption only', 'fuel efficiency', 'mpg',
                # Only container/cargo without fleet context
                'containers only', 'packages only', 'teus only', 'cargo only',
                # Only financial data
                'revenue only', 'cost only', 'investment only'
            ]
            
            has_clearly_invalid = any(indicator in evidence.evidence_text.lower() for indicator in clearly_invalid_contexts)
            
            # Only reject if clearly invalid context AND no vehicle fleet numbers
            if has_clearly_invalid and not (has_number and has_vehicle):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "Invalid context (non-vehicle data only), need vehicle count"
                return evidence
            
            if not (has_number and has_vehicle):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No valid total fleet size data found"
                return evidence
        
        elif criterion == "regulatory":
            # RELAXED: Accept broader compliance evidence, not just specific programs
            url = evidence.url if isinstance(evidence, CriteriaEvidence) else getattr(evidence, 'url', '')
            
            # Still reject pure technology rollout content
            technology_rollout_indicators = [
                'autonomous delivery technologies', 'technology modernization', 
                'modernization of truck regulations', 'adoption of technologies',
                'innovation only', 'technological advancement only', 'future technology only'
            ]
            
            has_technology_rollout = any(indicator in evidence.evidence_text.lower() for indicator in technology_rollout_indicators)
            if has_technology_rollout:
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "Technology rollout content rejected, need compliance evidence"
                return evidence
            
            # RELAXED: Accept broader compliance/regulatory language
            compliance_indicators = [
                'smartway', 'epa smartway', 'smartway member', 'smartway partner',
                'carb', 'carb certified', 'carb compliance', 'low-nox',
                'complies with', 'compliance with', 'certified', 'member of',
                'participates in', 'subject to regulations', 'regulatory oversight',
                'meets standards', 'follows regulations', 'regulatory requirements',
                'environmental standards', 'emission standards', 'safety standards',
                'dot regulations', 'federal requirements', 'state requirements'
            ]
            
            has_compliance = any(indicator in evidence.evidence_text.lower() for indicator in compliance_indicators)
            
            # RELAXED: Broader regulatory context acceptance
            has_regulatory = any(term in evidence.evidence_text.lower() for term in [
                'regulation', 'regulatory', 'compliance', 'standard', 'requirement',
                'freight', 'transportation', 'trucking', 'logistics', 'shipping',
                'environmental law', 'emission regulation', 'safety regulation'
            ])
            
            # Still reject clearly non-environmental regulations
            has_non_environmental = any(term in evidence.evidence_text.lower() for term in [
                'financial regulation only', 'securities regulation only', 'banking regulation only',
                'data privacy only', 'gdpr only', 'hipaa only'
            ])
            
            # RELAXED: Only reject obvious job descriptions
            has_job_description = any(term in evidence.evidence_text.lower() for term in [
                'job description', 'role responsibilities', 'position requires',
                'candidate will', 'applicant must', 'now hiring'
            ])
            
            # RELAXED: Accept if has compliance OR regulatory context (not both required)
            if not (has_compliance or has_regulatory) or has_non_environmental or has_job_description:
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No valid regulatory compliance evidence found"
                return evidence
        
        elif criterion == "emission_goals":
            # RELAXED: Accept broader goal/target language
            if not any(term in evidence.evidence_text.lower() for term in [
                "goal", "target", "commit", "net-zero", "carbon neutral", "reduction",
                "plan", "objective", "aim", "initiative", "strategy", "pathway"
            ]):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No emission goals evidence found"
                return evidence
                
        elif criterion == "emission_reporting":
            # RELAXED: Accept broader reporting/disclosure language
            if not any(term in evidence.evidence_text.lower() for term in [
                "report", "publish", "disclose", "sustainability data", "carbon footprint",
                "transparency", "communicate", "share", "data", "metrics", "tracking"
            ]):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No emission reporting evidence found"
                return evidence
                
        elif criterion == "alt_fuels":
            # Must be biodiesel/RNG/SAF, not CNG/LNG
            evidence_lower = evidence.evidence_text.lower()
            
            # REJECT if it's only CNG/LNG (those aren't "alternative" fuels for scoring purposes)
            if ("cng" in evidence_lower or "lng" in evidence_lower or "natural gas" in evidence_lower):
                # Check if it ONLY mentions CNG/LNG without other alt fuels
                true_alt_fuel_terms = [
                    "biodiesel", "biogas", "rng", "renewable natural gas", "renewable diesel",
                    "saf", "sustainable aviation fuel", "biofuel", "bio-diesel", "bio-gas",
                    "renewable fuel", "alternative fuel blend", "b20", "b5", "r99"
                ]
                
                if not any(term in evidence_lower for term in true_alt_fuel_terms):
                    print(f"[REJECT] Alt fuels evidence only mentions CNG/LNG, need biodiesel/RNG/SAF: {evidence.evidence_text[:100]}")
                    evidence.found = False
                    evidence.score = 0
                    evidence.evidence_text = "Found CNG/LNG only, need biodiesel/RNG/SAF evidence"
                    return evidence
            
            # REQUIRE true alternative fuel terms
            true_alt_fuel_terms = [
                "biodiesel", "biogas", "rng", "renewable natural gas", "renewable diesel",
                "saf", "sustainable aviation fuel", "biofuel", "bio-diesel", "bio-gas",
                "alternative fuel", "renewable fuel"
            ]
            
            if not any(term in evidence_lower for term in true_alt_fuel_terms):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No alternative fuels evidence found"
                return evidence
                
        elif criterion == "clean_energy_partner":
            # ENHANCED: Require external partnerships, not on-site generation
            has_partnership_terms = any(term in evidence.evidence_text.lower() for term in [
                'partnered with', 'partnership with', 'agreement with', 'signed with',
                'contracted with', 'working with', 'collaborated with',
                'signed an agreement', 'signed agreement', 'agreement to', 'partners with',
                'partnership', 'agreement', 'contract', 'collaboration', 'supplier',
                'ppa', 'power purchase agreement'
            ])
            
            has_energy_context = any(term in evidence.evidence_text.lower() for term in [
                'energy', 'fuel', 'renewable', 'clean', 'solar', 'wind', 'charging',
                'sustainable', 'aviation fuel', 'saf', 'green', 'carbon neutral',
                'power purchase', 'electricity', 'biofuel'
            ])
            
            # STRICT REJECTION: On-site generation (not partnerships)
            has_onsite_generation = any(term in evidence.evidence_text.lower() for term in [
                'on-site renewable energy', 'on-site generation', 'solar panels on',
                'generate on-site', 'internal generation', 'our facilities generate',
                'rooftop solar', 'facility solar', 'building solar'
            ])
            
            if has_onsite_generation:
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "On-site generation rejected, need external partnerships"
                return evidence
            
            if not (has_partnership_terms and has_energy_context):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No clean energy partnership evidence found"
                return evidence
    
    # Clamp score to valid range for this criterion
    evidence.score = max(0, min(max_score, evidence.score))
    
    return evidence


def should_replace_evidence(new_evidence: CriteriaEvidence, existing_evidence: CriteriaEvidence, criterion: str) -> bool:
    """Determine if new evidence should replace existing evidence"""
    
    # Always prefer verified evidence
    if new_evidence.verified and not existing_evidence.verified:
        return True
    
    # Prefer higher scores
    if new_evidence.score > existing_evidence.score:
        return True
    
    # For same scores, prefer source types in order: pdf_content > web_content > search_snippet
    source_priority = {"pdf_content": 3, "web_content": 2, "search_snippet": 1}
    new_priority = source_priority.get(new_evidence.source_type, 0)
    existing_priority = source_priority.get(existing_evidence.source_type, 0)
    
    if new_priority > existing_priority:
        return True
    
    return False 