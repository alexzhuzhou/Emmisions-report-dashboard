"""
Integration layer that uses the existing analyze_scorecard.py AI functions
for criteria analysis in the scraping pipeline.

Enhanced with bulletproof evidence selection and rubric-aligned scoring.
"""

import sys
import os
import logging
import re
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

# Import the existing analyze_scorecard functions from the same directory
from .analyze_scorecard import analyze_criterion_main, CriterionFinding, verify_quote, CRITERIA_KEYWORDS, split_text_by_page

# Add these imports for the domain trust functionality
import tldextract

logger = logging.getLogger(__name__)

# Import from scorecard module
from .scorecard.validation import CriteriaEvidence, validate_evidence_against_rubric, should_replace_evidence

# Scoring rubrics aligned with actual CRITERIA_SCORE_RANGES from analyze_scorecard.py
SCORING_RUBRICS = {
    # Binary criteria (0-1 scales)
    'cng_fleet': {
        0: 'No current CNG fleet operations (exploring/considering does not count)',
        1: 'Currently operates CNG vehicles (explicit confirmation required)'
    },
    'emission_reporting': {
        0: 'No evidence of publishing emissions or sustainability reports',
        1: 'Publishes emissions/sustainability reports (evidence of publication/availability required)'
    },
    'alt_fuels': {
        0: 'No mention of biogas, biodiesel, or RNG',
        1: 'Explicitly mentions use of biogas, biodiesel, or RNG'
    },
    'clean_energy_partner': {
        0: 'No partnerships with CNG/RNG providers or clean energy infrastructure',
        1: 'Has partnerships with CNG/RNG providers, fuel suppliers, or clean energy infrastructure (explicit partnerships required)'
    },
    'regulatory': {
        0: 'Not subject to specific freight/trucking regulations',
        1: 'Subject to specific freight/trucking regulations (EPA SmartWay, CARB, etc.) or operates in highly regulated sectors'
    },
    
    # Multi-level criteria  
    'total_truck_fleet_size': {
        0: 'No fleet size information found',
        1: 'Vague fleet references (e.g., "large fleet")',
        2: 'Approximate numbers or ranges (e.g., "approximately 30,000")',
        3: 'Specific exact numbers provided (precise fleet size disclosure)'
    },
    'emission_goals': {
        0: 'No emission reduction goals mentioned',
        1: 'Basic emission reduction goal or net-zero commitment',
        2: 'Detailed targets with timeline AND interim milestones (multiple specific targets)'
    },
    'cng_fleet_size': {
        0: 'No CNG fleet size information (exploring/planning does not count)',
        1: 'Small CNG fleet or pilot program (under 500 vehicles)',
        2: 'Medium CNG fleet (500-1000 vehicles)',
        3: 'Large CNG fleet (1000+ vehicles) or very detailed size disclosure'
    }
}

def get_rubric_justification(criterion: str, score: int, evidence_text: str) -> str:
    """Add rubric-based justification to AI reasoning"""
    if criterion not in SCORING_RUBRICS:
        return ""
    
    rubric = SCORING_RUBRICS[criterion]
    if score in rubric:
        return f" Per scoring rubric: {rubric[score]}"
    return ""

def find_exact_quote_in_text(text: str, approximate_quote: str) -> Tuple[bool, str]:
    """
    Enhanced quote verification that handles multi-sentence quotes properly.
    Uses existing verify_quote function and also does direct substring matching.
    """
    # First try the existing verify_quote function
    if verify_quote(text, approximate_quote, threshold=85):
        return True, approximate_quote
    
    # For multi-sentence quotes, try to find each sentence
    sentences = re.split(r'[.!?]+', approximate_quote)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) > 1:
        # Check if each sentence can be found (allowing for some flexibility)
        found_sentences = []
        for sentence in sentences:
            if len(sentence) > 10:  # Only check substantial sentences
                if verify_quote(text, sentence, threshold=80):
                    found_sentences.append(sentence)
        
        # If we found most sentences, consider it verified
        if len(found_sentences) >= len(sentences) * 0.7:  # 70% match threshold
            return True, ". ".join(found_sentences) + "."
    
    # Try direct substring search with normalization
    text_normalized = re.sub(r'\s+', ' ', text.lower().strip())
    quote_normalized = re.sub(r'\s+', ' ', approximate_quote.lower().strip())
    
    # Check for substantial overlap
    if len(quote_normalized) > 20 and quote_normalized in text_normalized:
        return True, approximate_quote
    
    # Check for 80% of the quote being present
    words = quote_normalized.split()
    if len(words) > 5:
        found_words = sum(1 for word in words if word in text_normalized)
        if found_words >= len(words) * 0.8:
            return True, approximate_quote
    
    return False, approximate_quote

def enhance_emission_goals_evidence(original_evidence: CriterionFinding, text: str, company: str) -> CriterionFinding:
    """Enhanced emission goals evidence selection to find actual goals quotes, not regulatory text"""
    
    # Look for actual emission goal statements
    goals_patterns = [
        r'[Ww]e have committed to (?:achieving )?net-zero carbon emissions by \d{4}[^.]*',
        r'[Cc]ommitted to achieving net-zero carbon emissions by \d{4}[^.]*',
        r'[Nn]et-zero carbon emissions by \d{4}[^.]*targets[^.]*',
        r'[Cc]arbon (?:neutral|emissions reduction|footprint reduction)[^.]*by \d{4}[^.]*',
        r'[Cc]limate goals[^.]*\d{4}[^.]*',
        r'[Gg]HG reduction[^.]*targets[^.]*\d{4}[^.]*',
        r'[Ee]mission reduction[^.]*targets[^.]*\d{4}[^.]*',
        r'[Ss]cience-based targets[^.]*\d{4}[^.]*'
    ]
    
    # Look for sentences containing goal language
    goal_sentences = []
    for pattern in goals_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Extract the full sentence containing this match
            sentence = extract_sentence_containing(text, match.group(0))
            if sentence and len(sentence) > 20:  # Ensure it's substantial
                goal_sentences.append(sentence)
    
    if goal_sentences:
        # Find the best goal sentence (longest or most specific)
        best_goal = max(goal_sentences, key=len)
        
        # Score based on content
        score = 1  # Default for any goals
        if any(word in best_goal.lower() for word in ["interim", "2030", "50%", "milestone"]):
            score = 2  # Has interim targets
        
        enhanced_justification = f"Enhanced emission goals evidence: Found specific emission goals statement. " + get_rubric_justification("emission_goals", score, best_goal)
        
        return CriterionFinding(
            criteria_found=True,
            score=score,
            quote=best_goal,
            justification=enhanced_justification,
            original_passage=best_goal,
            verified=True
        )
    
    return original_evidence

def extract_fleet_size_numbers(text: str, criterion: str) -> Tuple[Optional[int], Optional[str]]:
    """Extract fleet size numbers from text and return (number, unit)"""
    
    if criterion == "total_truck_fleet_size":
        fleet_patterns = [
            r'\b([0-9]{1,3}(?:,[0-9]{3})+|\d{4,})\b',  # "125,000" or "10000"
            r'\b([0-9]+(?:\.[0-9]+)?)\s*[kK]\s*(?:vehicles?|trucks?|fleet|tractors?|trailers?)\b',  # "15K vehicles"
            r'\b(?:over|more than|approximately|~|about)\s*([0-9,]+)\s*(?:vehicles?|trucks?|fleet|tractors?|trailers?)\b',  # "over 50,000"
            r'\b([0-9]+)\s*(?:thousand|million)\s*(?:vehicles?|trucks?|fleet|tractors?|trailers?)\b',  # "30 thousand vehicles"
            r'\b(?:operates?|maintains?|has)\s*(?:approximately|about|over)?\s*([0-9,]+)\s*(?:vehicles?|trucks?|fleet|tractors?|trailers?)\b'  # "operates 125,000 vehicles"
        ]
        
        for pattern in fleet_patterns:
            fleet_match = re.search(pattern, text, re.IGNORECASE)
            if fleet_match:
                num_str = fleet_match.group(1).replace(',', '')
                try:
                    if 'k' in fleet_match.group(0).lower():
                        fleet_num = int(float(num_str) * 1000)
                    elif 'thousand' in fleet_match.group(0).lower():
                        fleet_num = int(float(num_str) * 1000)
                    elif 'million' in fleet_match.group(0).lower():
                        fleet_num = int(float(num_str) * 1000000)
                    else:
                        fleet_num = int(float(num_str))
                    return fleet_num, "vehicles"
                except ValueError:
                    continue
    
    elif criterion == "cng_fleet_size":
        cng_patterns = [
            r'\bcng\s+(\d{1,5}(?:,\d{3})*)\b',  # "CNG 3,524"
            r'\b(\d{1,5}(?:,\d{3})*)\s+cng\b',  # "3,524 CNG"
            r'\b(\d{1,5}(?:,\d{3})*)\s*(?:cng|compressed natural gas)\s*(?:vehicles?|trucks?)\b',  # "3,524 CNG vehicles"
            r'\bcng\s*(?:vehicles?|trucks?)\s*[:\-]?\s*(\d{1,5}(?:,\d{3})*)\b',  # "CNG vehicles: 3,524"
            r'\b([0-9]+(?:\.[0-9]+)?)\s*[kK]\s*(?:cng|compressed natural gas)\s*(?:vehicles?|trucks?)\b',  # "6K CNG vehicles"
            r'\b(?:over|more than|approximately|~|about)\s*([0-9,]+)\s*(?:cng|compressed natural gas)\s*(?:vehicles?|trucks?)\b',  # "over 5,000 CNG"
            r'\b([0-9]+)\s*(?:thousand|million)\s*(?:cng|compressed natural gas)\s*(?:vehicles?|trucks?)\b',  # "6 thousand CNG vehicles"
            r'\b(?:operates?|has|deployed)\s*(?:approximately|about|over)?\s*([0-9,]+)\s*(?:cng|compressed natural gas)\s*(?:vehicles?|trucks?)\b'  # "operates 6,000 CNG vehicles"
        ]
        
        for pattern in cng_patterns:
            cng_match = re.search(pattern, text, re.IGNORECASE)
            if cng_match:
                num_str = cng_match.group(1).replace(',', '')
                try:
                    if 'k' in cng_match.group(0).lower():
                        cng_num = int(float(num_str) * 1000)
                    elif 'thousand' in cng_match.group(0).lower():
                        cng_num = int(float(num_str) * 1000)
                    elif 'million' in cng_match.group(0).lower():
                        cng_num = int(float(num_str) * 1000000)
                    else:
                        cng_num = int(float(num_str))
                    return cng_num, "vehicles"
                except ValueError:
                    continue
    
    return None, None

def enhance_fleet_size_evidence(original_evidence: CriterionFinding, text: str, company: str) -> CriterionFinding:
    """Enhanced fleet size evidence selection with proper scoring per rubric"""
    
    # Look for comprehensive fleet size information - expanded patterns
    fleet_patterns = [
        r'operates more than (\d+(?:,\d+)*) delivery trucks',
        r'operates (\d+(?:,\d+)*) delivery trucks',
        r'more than (\d+(?:,\d+)*) delivery trucks',
        r'over (\d+(?:,\d+)*) delivery (?:vehicles|trucks)',
        r'operates (\d+(?:,\d+)*) tractors',
        r'(\d+(?:,\d+)*) trailers',
        r'fleet of (?:over )?(\d+(?:,\d+)*)',
        r'approximately (\d+(?:,\d+)*) (?:trucks|vehicles)',
        r'operates approximately (\d+(?:,\d+)*) vehicles',
        r'maintains (?:a fleet of )?(?:over )?(\d+(?:,\d+)*) (?:tractors|trucks|vehicles)',
        r'(\d+(?:,\d+)*) collection trucks',
        r'(\d+(?:,\d+)*)\+ (?:trucks|vehicles)',
        r'plans to expand to over (\d+(?:,\d+)*)'
    ]
    
    fleet_mentions = []
    for pattern in fleet_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                number_str = match.group(1).replace(',', '')
                # Handle cases like "13,000+" 
                if '+' in number_str:
                    number_str = number_str.replace('+', '')
                number = int(number_str)
                
                # Extract full sentence containing this match
                full_sentence = extract_sentence_containing(text, match.group(0))
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end].strip()
                
                fleet_mentions.append((number, full_sentence, context))
            except (ValueError, IndexError):
                continue
    
    if fleet_mentions:
        # Find the best quote - prefer largest numbers or total fleet mentions
        fleet_mentions.sort(key=lambda x: x[0], reverse=True)
        largest_number, best_sentence, best_context = fleet_mentions[0]
        
        # Score based on rubric
        if largest_number >= 50000:
            score = 3  # Very large fleet with specific numbers
        elif largest_number >= 10000:
            score = 3  # Large fleet with specific numbers  
        elif largest_number >= 1000:
            score = 2  # Medium-sized fleet with numbers
        else:
            score = 1  # Small fleet or approximate
        
        # If we have multiple data points, that's comprehensive disclosure
        if len(fleet_mentions) >= 2:
            score = 3
        
        enhanced_justification = f"Enhanced fleet size evidence: Found specific fleet size data ({largest_number:,} vehicles). " + get_rubric_justification("total_truck_fleet_size", score, best_sentence)
        
        return CriterionFinding(
            criteria_found=True,
            score=score,
            quote=best_sentence,
            justification=enhanced_justification,
            original_passage=best_context,
            verified=True
        )
    
    return original_evidence

def enhance_emission_reporting_evidence(original_evidence: CriterionFinding, text: str, company: str) -> CriterionFinding:
    """Enhanced emission reporting evidence that finds actual quotes instead of fallback text"""
    
    # Look for explicit emission reporting language
    reporting_patterns = [
        r'[Ww]e publish(?:ed)? (?:detailed )?(?:carbon footprint data|emissions? data|scope [123],? (?:and )?[123],? (?:and )?[123] emissions?)',
        r'[Ww]e (?:disclose|report) (?:our )?(?:scope [123],? )?emissions?',
        r'(?:annual|sustainability) report (?:disclose[ds]?|detail[s]?) (?:our )?emissions?',
        r'[Cc]arbon footprint data.*?(?:publicly available|disclosed|published)',
        r'[Ee]missions? (?:data|metrics|inventory) (?:are )?(?:publicly )?(?:available|disclosed|reported)',
        r'[Ss]ustainability report.*?(?:carbon|emissions?|environmental)'
    ]
    
    for pattern in reporting_patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            match = matches[0]
            # Extract the full sentence containing this match
            sentence = extract_sentence_containing(text, match.group(0))
            
            # Score based on specificity
            if any(term in sentence.lower() for term in ['scope 1', 'scope 2', 'scope 3']):
                score = 3  # Detailed scope reporting
            elif any(term in sentence.lower() for term in ['carbon footprint', 'emissions data', 'publish']):
                score = 2  # Explicit reporting mention
            else:
                score = 1  # General reporting
            
            enhanced_justification = f"Found explicit emission reporting statement. " + get_rubric_justification("emission_reporting", score, sentence)
            
            return CriterionFinding(
                criteria_found=True,
                score=score,
                quote=sentence,
                justification=enhanced_justification,
                original_passage=sentence,
                verified=True
            )
    
    # If no explicit reporting found but it's a sustainability report, use original logic
    return original_evidence

def extract_sentence_containing(text: str, pattern: str) -> str:
    """Extract the full sentence containing the given pattern"""
    # Find the position of the pattern
    match = re.search(re.escape(pattern), text, re.IGNORECASE)
    if not match:
        return pattern
    
    start_pos = match.start()
    
    # Find sentence boundaries
    sentence_start = start_pos
    sentence_end = match.end()
    
    # Go backward to find sentence start
    while sentence_start > 0 and text[sentence_start] not in '.!?':
        sentence_start -= 1
    if sentence_start > 0:
        sentence_start += 1
    
    # Go forward to find sentence end
    while sentence_end < len(text) and text[sentence_end] not in '.!?':
        sentence_end += 1
    if sentence_end < len(text):
        sentence_end += 1
    
    sentence = text[sentence_start:sentence_end].strip()
    return sentence

# Define the keyword mappings for each criterion
CRITERION_KEYWORDS = {
    'total_truck_fleet_size': {
        'primary': ['truck', 'fleet', 'vehicles', 'tractors', 'trailers', 'semi-trucks'],
        'secondary': ['logistics', 'delivery', 'transportation', 'operates']
    },
    'cng_fleet': {
        'primary': ['CNG', 'compressed natural gas', 'natural gas'],
        'secondary': ['alternative fuel', 'clean fuel', 'gas-powered']
    },
    'cng_fleet_size': {
        'primary': ['CNG', 'compressed natural gas', 'natural gas'],
        'secondary': ['fleet size', 'number', 'vehicles', 'trucks']
    },
    'emission_reporting': {
        'primary': ['emissions report', 'sustainability report', 'carbon footprint', 'scope 1', 'scope 2', 'scope 3'],
        'secondary': ['environmental disclosure', 'climate report', 'publish', 'disclose']
    },
    'emission_goals': {
        'primary': ['net-zero', 'carbon neutral', 'emission reduction', 'climate goals', 'GHG reduction'],
        'secondary': ['targets', 'commitment', 'goals', '2030', '2040', '2050']
    },
    'alt_fuels': {
        'primary': ['biogas', 'biodiesel', 'RNG', 'renewable natural gas'],
        'secondary': ['alternative fuels', 'biofuels', 'renewable diesel']
    },
    'clean_energy_partner': {
        'primary': ['Clean Energy Fuels', 'Trillium', 'renewable energy', 'partnership'],
        'secondary': ['clean energy', 'solar', 'wind', 'charging infrastructure']
    },
    'regulatory': {
        'primary': ['regulatory', 'compliance', 'EPA', 'CARB', 'DOT'],
        'secondary': ['regulations', 'oversight', 'environmental standards', 'SEC filing']
    }
}

def analyze_text_with_scorecard(text: str, url: str, needed: Set[str], company: str) -> Dict[str, CriteriaEvidence]:
    """
    Analyze text using OPTIMIZED multi-criteria AI analysis instead of single-criterion loops.
    CRITICAL FIX: Use call_openai_multi_criteria to avoid rate limiting.
    """
    import logging
    from .ai_criteria_analyzer import call_openai_multi_criteria
    
    logger = logging.getLogger(__name__)
    results = {}
    
    if not needed:
        return results
    
    logger.info(f"Analyzing text with OPTIMIZED multi-criteria approach for {len(needed)} criteria")
    
    try:
        # Use optimized multi-criteria analysis instead of single-criterion loop
        multi_result = call_openai_multi_criteria(text, needed, company)
        
        # Convert multi-criteria results to CriteriaEvidence format
        for criterion in needed:
            criterion_data = multi_result.get(criterion, {})
            
            if criterion_data.get('criteria_found', False):
                evidence = CriteriaEvidence(
                    criterion=criterion,
                    found=True,
                    score=criterion_data.get('score', 0),
                    evidence_text=criterion_data.get('quote', ''),
                    full_context=text,  # Use full text as context
                    justification=criterion_data.get('justification', ''),
                    url=url,
                    source_type="pdf_content" if url.endswith('.pdf') else "web_content",
                    verified=False  # Will be verified later if needed
                )
                
                # Apply stricter validation to prevent false positives
                evidence = validate_evidence_against_rubric(evidence)
                
                # Verify quote in text
                verified, verified_quote = find_exact_quote_in_text(text, evidence.evidence_text)
                if verified:
                    evidence.evidence_text = verified_quote
                    evidence.verified = True
                    logger.info(f"Quote verified for {criterion}")
                else:
                    # Use flexible verification for less exact matches
                    from .ai_criteria_analyzer import verify_quote_flexible
                    if verify_quote_flexible(text, evidence.evidence_text, criterion):
                        evidence.verified = True
                        logger.info(f"Quote flexibly verified for {criterion}")
                    else:
                        logger.warning(f"Quote for {criterion} NOT VERIFIED: '{evidence.evidence_text[:50]}....'")
                
                results[criterion] = evidence
                logger.info(f"Found evidence for {criterion} (score: {evidence.score})")
            else:
                # Create evidence showing no finding
                results[criterion] = CriteriaEvidence(
                    criterion=criterion,
                    found=False,
                    score=0,
                    evidence_text="No evidence found",
                    full_context="",
                    justification=criterion_data.get('justification', 'No evidence found in text'),
                    url=url,
                    source_type="pdf_content" if url.endswith('.pdf') else "web_content"
                )
    
    except Exception as e:
        logger.error(f"Multi-criteria analysis failed: {str(e)}")
        # Fallback: Create empty results for all criteria
        for criterion in needed:
            results[criterion] = CriteriaEvidence(
                criterion=criterion,
                found=False,
                score=0,
                evidence_text="Analysis failed",
                full_context="",
                justification=f"Error during analysis: {str(e)}",
                url=url,
                source_type="pdf_content" if url.endswith('.pdf') else "web_content"
            )
    
    logger.info(f"Multi-criteria analysis completed for {len(results)} criteria")
    return results

def analyze_search_snippets_with_scorecard(search_results: Dict[str, Dict[str, str]], company: str, needed: Set[str]) -> Dict[str, CriteriaEvidence]:
    """
    Analyze search snippets using analyze_scorecard AI with enhanced evidence selection.
    """
    evidence = {}
    
    for url, result_data in search_results.items():
        snippet = result_data.get("snippet", "")
        title = result_data.get("title", "")
        
        if not snippet and not title:
            continue
        
        combined_text = f"Title: {title}\nSnippet: {snippet}"
        
        logger.info(f"Analyzing search snippet from {url}:")
        logger.info(f"  Title: {title}")
        logger.info(f"  Snippet: {snippet}")
        
        # Analyze with scorecard
        snippet_results = analyze_text_with_scorecard(combined_text, f"{url}#search_snippet", needed, company)
        
        for criterion, evidence_data in snippet_results.items():
            evidence_data.source_type = "search_snippet"
            evidence_data.search_title = title
            evidence_data.full_snippet = snippet
            
            # Replace if better or first evidence
            if criterion not in evidence or should_replace_evidence(evidence_data, evidence[criterion], criterion):
                evidence[criterion] = evidence_data
                logger.info(f"✓ Found {criterion} evidence in search snippet from {url}")
            
    return evidence

def analyze_text_content_with_scorecard(text: str, url: str, needed: Set[str], company: str) -> Dict[str, CriteriaEvidence]:
    """
    Analyze full text content using analyze_scorecard AI with enhanced evidence selection.
    """
    logger.info(f"Analyzing full text content from {url} ({len(text)} chars)")
    return analyze_text_with_scorecard(text, url, needed, company)

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

def convert_evidence_to_dict(evidence: CriteriaEvidence) -> Dict[str, Any]:
    """Convert CriteriaEvidence to dictionary format"""
    return {
        'found': evidence.found,
        'score': evidence.score,
        'evidence': evidence.evidence_text,
        'context': evidence.full_context,
        'justification': evidence.justification,
        'url': evidence.url,
        'source_type': evidence.source_type,
        'verified': evidence.verified
    }

def convert_scorecard_results_to_legacy_format(scorecard_results: Dict[str, CriteriaEvidence]) -> Dict[str, Dict[str, Any]]:
    """Convert scorecard results to legacy format for compatibility"""
    legacy_results = {}
    for criterion, evidence in scorecard_results.items():
        # Map the scorecard confidence score (0-3) to legacy tier system
        if evidence.score >= 3:
            tier = 1  # Highest confidence
        elif evidence.score >= 2:
            tier = 2  # Medium confidence  
        else:
            tier = 3  # Lower confidence
        
        legacy_results[criterion] = {
            'found': evidence.found,
            'score': evidence.score,
            'evidence': evidence.evidence_text,
            'context': evidence.full_context,
            'justification': evidence.justification,
            'url': evidence.url,
            'source_type': evidence.source_type,
            'verified': evidence.verified,
            'tier': tier,
            'confidence': evidence.score,  # Use the score as confidence
            'tier_name': 'ai_scorecard_analysis',
            # NEW: Include extracted numeric data for fleet size criteria
            'fleet_size_number': evidence.extracted_number,
            'fleet_size_unit': evidence.extracted_unit,
            'numeric_range': evidence.numeric_range
        }
    return legacy_results

def display_evidence_with_full_context(evidence_dict: Dict[str, CriteriaEvidence]) -> None:
    """
    Display evidence with complete context, quotes, and verification details.
    Enhanced to show all details without truncation.
    """
    print("\n=== COMPLETE EVIDENCE VALIDATION - AMAZON SEARCH SNIPPETS ===\n")
    
    for criterion, evidence in evidence_dict.items():
        print(f"🔍 CRITERION: {criterion}")
        print(f"   Score: {evidence.score}/3")
        print(f"   Found: {evidence.found}")
        print(f"   Source Type: {evidence.source_type}")
        print(f"   Source URL: {evidence.url}")
        print(f"   Verified: {evidence.verified}")
        print()
        print(f"📝 COMPLETE EVIDENCE QUOTE:")
        print(f"   \"{evidence.evidence_text}\"")
        print()
        print(f"📄 FULL ORIGINAL CONTEXT:")
        print(f"   {evidence.full_context}")
        print()
        print(f"🤖 COMPLETE AI JUSTIFICATION:")
        print(f"   {evidence.justification}")
        print()
        print("=" * 100)
        print()
    
    # Summary
    print(f"SUMMARY - Found evidence for {len(evidence_dict)} criteria from search snippets:")
    for criterion, evidence in evidence_dict.items():
        print(f"  ✓ {criterion} (score: {evidence.score}): {evidence.evidence_text[:80]}...")
    print()

def validate_evidence_against_rubric(evidence: CriteriaEvidence) -> CriteriaEvidence:
    """Validate evidence against scoring rubric and clamp scores to valid ranges"""
    from .analyze_scorecard import CRITERIA_DB_MAPPING_SCORES
    
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
            
            # RELAXED: Only reject pure fuel consumption without vehicle context
            fuel_only_indicators = [
                'gallons per', 'consumption rate', 'fuel efficiency', 'mpg', 'fuel only',
                'diesel equivalent only', 'therms only', 'energy content only'
            ]
            has_fuel_only = any(indicator in evidence.evidence_text.lower() for indicator in fuel_only_indicators)
            
            # RELAXED: Only reject parts context without vehicle fleet context
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
            
            # Extract number and check minimum threshold
            number_match = re.search(r'\b(\d+[\d,]*)\b', evidence.evidence_text)
            if number_match:
                try:
                    # Strip all non-digits before parsing
                    number_str = number_match.group(1)
                    number_clean = re.sub(r'[^\d]', '', number_str)
                    if number_clean:
                        number_value = int(number_clean)
                        if number_value < 1:  # Any positive number of CNG vehicles is meaningful
                            evidence.found = False
                            evidence.score = 0
                            evidence.evidence_text = "Number too small for meaningful CNG fleet size"
                            return evidence
                except (ValueError, AttributeError):
                    evidence.found = False
                    evidence.score = 0
                    evidence.evidence_text = "Could not parse vehicle count"
                    return evidence
            
            if not (has_number and has_vehicle and not (has_parts_context and not (has_number and has_vehicle))):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No valid CNG fleet size data found"
                return evidence
        
        elif criterion == "total_truck_fleet_size":
            # Must be TOTAL fleet size across all fuel types, not fuel-specific counts
            has_number = any(char.isdigit() for char in evidence.evidence_text)
            has_vehicle = any(term in evidence.evidence_text.lower() for term in [
                'truck', 'vehicle', 'fleet', 'trailer', 'tractor', 'semi-truck', 'semi truck'
            ])
            
            # STRICT REJECTION: Fuel-specific vehicle counts (should go to specific criteria instead)
            fuel_specific_indicators = [
                'cngs', 'cng trucks', 'cng vehicles', 'natural gas vehicles', 'natural gas trucks',
                'compressed natural gas vehicles', 'electric vehicles', 'electric trucks', 'ev trucks',
                'electric delivery vehicles', 'diesel trucks only', 'hybrid vehicles'
            ]
            has_fuel_specific = any(indicator in evidence.evidence_text.lower() for indicator in fuel_specific_indicators)
            
            # STRICT REJECTION: Fuel consumption, employee counts, warehouses
            invalid_indicators = [
                'gallons', 'liters', 'consumption', 'fuel', 'delivered', 'consumed',
                'employees', 'workers', 'team members', 'staff', 'associates',
                'fulfillment centers', 'warehouses', 'facilities', 'distribution centers'
            ]
            has_invalid_context = any(indicator in evidence.evidence_text.lower() for indicator in invalid_indicators)
            
            # Only accept if it has vehicles AND numbers AND NOT fuel-specific AND NOT invalid context
            if has_fuel_specific:
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "Fuel-specific count rejected, need total fleet size across all fuel types"
                return evidence
            
            if has_invalid_context:
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "Invalid context (fuel consumption or employee count), need vehicle count"
                return evidence
            
            if not (has_number and has_vehicle):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No valid total fleet size data found"
                return evidence
        
        elif criterion == "regulatory":
            # Must be compliance/participation, not technology rollout
            url = evidence.url if isinstance(evidence, CriteriaEvidence) else getattr(evidence, 'url', '')
            
            # STRICT REJECTION: Technology rollout content
            technology_rollout_indicators = [
                'autonomous delivery technologies', 'technology modernization', 
                'modernization of truck regulations', 'adoption of technologies',
                'innovation', 'technological advancement', 'future technology',
                'technology development', 'emerging technologies'
            ]
            
            has_technology_rollout = any(indicator in evidence.evidence_text.lower() for indicator in technology_rollout_indicators)
            if has_technology_rollout:
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "Technology rollout content rejected, need compliance evidence"
                return evidence
            
            # REQUIRE: Actual compliance/participation language
            compliance_indicators = [
                'smartway', 'epa smartway', 'smartway member', 'smartway partner',
                'carb', 'carb certified', 'carb compliance', 'low-nox',
                'complies with', 'compliance with', 'certified', 'member of',
                'participates in', 'subject to regulations', 'regulatory oversight',
                'meets standards', 'follows regulations'
            ]
            
            has_compliance = any(indicator in evidence.evidence_text.lower() for indicator in compliance_indicators)
            
            # Apply existing regulatory content validation
            has_regulatory = any(term in evidence.evidence_text.lower() for term in [
                'regulation', 'compliance', 'requirement',  # Direct regulatory terms
                'regulatory', 'scrutiny', 'oversight',      # Regulatory pressure terms
                'regulators', 'regulatory pressure', 'regulatory environment',  # Regulatory context
                'carb', 'epa', 'environmental protection agency',  # Specific agencies
                'clean air act', 'zev mandate', 'smartway',          # Specific regulations
                'highly regulated', 'regulated industry',    # Regulatory status terms
                'comply with', 'complies with', 'compliance with', 'subject to',
                'laws', 'rules', 'regulations', 'filing', 'filings'
            ])
            
            # REJECT non-environmental regulatory content
            has_non_environmental = any(term in evidence.evidence_text.lower() for term in [
                'data governance', 'data quality', 'data protection', 'data privacy',
                'cybersecurity', 'information security', 'it compliance', 'software compliance',
                'financial reporting', 'sox compliance', 'audit compliance',
                'hr compliance', 'employment law', 'labor relations',
                'technical support', 'troubleshooting', 'monitoring', 'system administration',
                'user access', 'authentication', 'authorization', 'database'
            ])
            
            # REJECT job description content
            has_job_description = any(term in evidence.evidence_text.lower() for term in [
                'transport compliance manager', 'compliance manager', 'job description',
                'responsibilities include', 'role responsibilities', 'job duties',
                'position requires', 'candidate will', 'applicant must',
                'uphold standards', 'improve and streamline', 'diving deep',
                'find practical solutions', 'programme', 'associate'
            ])
            
            has_boilerplate = any(term in evidence.evidence_text.lower() for term in [
                'unless it would violate', 'notice of any legal', 'template', 'boilerplate'
            ])
            
            # Prefer explicit compliance evidence
            if not ((has_compliance or has_regulatory) and not has_non_environmental and not has_job_description and not has_boilerplate):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No valid regulatory compliance evidence found"
                return evidence
        
        elif criterion == "emission_goals":
            # Must explicitly mention goals, targets, commitments, or net-zero
            if not any(term in evidence.evidence_text.lower() for term in ["goal", "target", "commit", "net-zero", "carbon neutral", "reduction"]):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No emission goals evidence found"
                return evidence
                
        elif criterion == "emission_reporting":
            # Must explicitly mention reporting, publishing, or disclosing emissions
            if not any(term in evidence.evidence_text.lower() for term in ["report", "publish", "disclose", "sustainability data", "carbon footprint"]):
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
            
            # STRICT REJECTION: Generic investment language
            has_generic_investment = any(term in evidence.evidence_text.lower() for term in [
                'largest corporate purchaser', 'gigawatts', 'capacity purchased', 
                'investment in', 'evaluating additional opportunities'
            ])
            
            if not (has_partnership_terms and has_energy_context and not has_onsite_generation and not has_generic_investment):
                evidence.found = False
                evidence.score = 0
                evidence.evidence_text = "No valid external clean energy partnership found"
                return evidence
    
    # Clamp score to valid range
    if evidence.score > max_score:
        print(f"Score {evidence.score} for {criterion} exceeds max {max_score}, clamping to {max_score}")
        evidence.score = max_score
    
    return evidence

def score_url(url: str, needed: Set[str], company: str) -> int:
    """Enhanced URL scoring with better relevance checks."""
    try:
        score = 0
        parsed = urlparse(url)
        searchable = (parsed.path + '?' + parsed.query).lower()
        
        # Trust scoring - use the is_trusted_domain function
        if is_trusted_domain(url, company):
            score += 3
            
        # Penalize IR pages unless they're reports
        if '/investor' in searchable or '/ir/' in searchable:
            if not any(r in searchable for r in ['/report', '/10k', '/10-k', '/sustainability']):
                score -= 4
                
        # Boost sustainability content
        sustainability_terms = ['sustainability', 'esg', 'environment', 'climate']
        score += sum(2 for term in sustainability_terms if term in searchable)
        
        # PDF bonus - prioritize official reports
        if url.lower().endswith('.pdf'):
            score += 50
        
        # Count keyword matches using CRITERIA_KEYWORDS from analyze_scorecard
        for criterion in needed:
            if criterion in CRITERIA_KEYWORDS:
                score += sum(1 for kw in CRITERIA_KEYWORDS[criterion] if kw in searchable)
                
        return max(0, score)
    except Exception as e:
        logger.warning(f"URL scoring failed for {url}: {e}")
        return 0 

def is_trusted_domain(url: str, company: str) -> bool:
    """Check if URL is from a trusted domain - generic version for any company"""
    try:
        # Extract domain parts safely
        ext = tldextract.extract(url)
        domain = ext.registered_domain.lower()
        subdomain = ext.subdomain.lower()
        full_domain = f"{subdomain}.{domain}" if subdomain else domain
        
        # HIGHEST PRIORITY: Company name check (dynamic)
        company_clean = company.lower().strip()
        company_variations = [
            company_clean,
            company_clean.replace(' ', ''),
            company_clean.replace(' ', '-'),
            company_clean.replace('.', ''),
        ]
        
        # Add variations without common business suffixes
        for suffix in [' inc', ' corp', ' corporation', ' company', ' co', ' llc', ' ltd']:
            if company_clean.endswith(suffix):
                clean_no_suffix = company_clean[:-len(suffix)].strip()
                if len(clean_no_suffix) > 2:
                    company_variations.extend([
                        clean_no_suffix,
                        clean_no_suffix.replace(' ', ''),
                        clean_no_suffix.replace(' ', '-')
                    ])
                break
        
        # Check if domain contains company name variations
        for variation in company_variations:
            if len(variation) > 3 and variation in domain:
                return True
        
        # TIER 1: Government and regulatory sources (universal trust)
        tier_1_domains = [
            'sec.gov', 'edgar.sec.gov', 'epa.gov', 'energy.gov',
            'carb.ca.gov', 'dot.gov', 'transportation.gov'
        ]
        
        # TIER 2: Major financial news and rating agencies
        tier_2_domains = [
            'bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com',
            'businesswire.com', 'prnewswire.com', 'globenewswire.com'
        ]
        
        # TIER 3: Industry-specific sources (transport/logistics)
        tier_3_domains = [
            'fleetowner.com', 'ttnews.com', 'freightwaves.com',
            'truckinginfo.com', 'ccjdigital.com', 'overdriveonline.com'
        ]
        
        # TIER 4: Sustainability/ESG organizations
        tier_4_domains = [
            'cdp.net', 'globalreporting.org', 'sustainability.com',
            'ceres.org', 'bsr.org', 'sustainablebrands.com'
        ]
        
        all_trusted_domains = tier_1_domains + tier_2_domains + tier_3_domains + tier_4_domains
        
        # Check against trusted domain lists
        for trusted_domain in all_trusted_domains:
            if trusted_domain in domain or trusted_domain in full_domain:
                return True
        
        # Check for company sustainability subdomains
        sustainability_subdomains = [
            'sustainability', 'esg', 'corporate', 'investor', 'ir',
            'about', 'newsroom', 'news', 'press'
        ]
        
        if subdomain in sustainability_subdomains:
            # If it's a sustainability subdomain AND contains company name, trust it
            for variation in company_variations:
                if len(variation) > 3 and variation in domain:
                    return True
        
        return False
        
    except Exception as e:
        logger.debug(f"Domain trust check failed: {e}")
        return False

# Essential constants for the AI scraper (moved from criteria_patterns for self-containment)
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

# URL keywords for URL scoring
URL_KEYWORDS = {
    "cng_fleet": ["cng", "natural-gas", "compressed-natural-gas"],
    "cng_fleet_size": ["cng-fleet", "natural-gas-fleet", "cng-trucks"],
    "total_truck_fleet_size": ["fleet-size", "truck-fleet", "total-trucks"],
    "equipment_fleet_size": ["trailer-fleet", "container-fleet", "equipment"],
    "emission_reporting": ["sustainability-report", "esg-report", "emissions-report", "annual-report"],
    "emission_goals": ["net-zero", "carbon-neutral", "emission-target", "ghg-reduction"],
    "alt_fuels": ["hydrogen", "electric-truck", "ev-fleet", "zero-emission", "alternative-fuel"],
    "clean_energy_partner": ["clean-energy", "trillium", "cummins", "partnership"],
    "regulatory": ["compliance", "regulation", "carb", "epa", "mandate"],
} 

def is_quality_evidence(text: str, company: str, criterion: str, confidence: int, url: str = None, evidence = None) -> bool:
    """Enhanced quality check - allows strong pattern matches even with weak company mentions."""
    # --- 0. VERY short? drop.
    if not text or len(text) < 25:
        return False
    
    text_l = text.lower()
    
    # --- 1. For trusted domains OR strong patterns OR search snippets, be more lenient about company mentions
    from_trusted_domain = is_trusted_domain(url, company) if url else False
    is_search_snippet = evidence and getattr(evidence, 'source_type', evidence.get('source_type') if isinstance(evidence, dict) else None) == 'search_snippet' if evidence else False
    
    # Check if this is a strong pattern match (specific numbers with vehicles)
    has_strong_pattern = False
    if criterion in ['total_truck_fleet_size', 'cng_fleet_size']:
        # Strong pattern: specific number + vehicle type + operational context within 40 chars
        has_number = any(char.isdigit() for char in text)
        has_vehicle = any(term in text_l for term in [
            'truck', 'vehicle', 'fleet', 'trailer', 'tractor', 'semi-truck'
        ])
        
        # Check for operational context near the number
        has_operational_context = False
        if has_number and has_vehicle:
            # Find number position
            number_match = re.search(r'\b\d+[\d,]*\b', text)
            if number_match:
                num_start = number_match.start()
                num_end = number_match.end()
                
                # Check for operational terms within 40 chars before or after the number
                context_window = text_l[max(0, num_start-40):num_end+40]
                operational_terms = ['fleet', 'network', 'operate', 'operates', 'own', 'owns', 
                                   'maintain', 'maintains', 'has', 'have', 'deploy', 'deploys',
                                   'peaking', 'oscillating', 'totals', 'consists']  # Added for snippets
                has_operational_context = any(term in context_window for term in operational_terms)
        
        has_strong_pattern = has_number and has_vehicle and has_operational_context
    
    # If from trusted domain OR strong pattern OR search snippet, relax company mention requirement
    if from_trusted_domain or has_strong_pattern or is_search_snippet:
        # Just check if it's not clearly about another company
        if not is_company_mentioned_simple(text, company, url):
            # Check if it's clearly about another company
            other_company_report = any(pattern in text_l for pattern in [
                ' inc. sustainability report', ' corp sustainability report', 
                ' company sustainability report', ' group sustainability report'
            ])
            # Extract potential company name from "XYZ Sustainability Report" patterns
            sustainability_report_pattern = r'\b([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+sustainability\s+report\b'
            report_matches = re.findall(sustainability_report_pattern, text_l)
            wrong_company_report = False
            for match in report_matches:
                match_clean = match.strip()
                if (len(match_clean) > 2 and 
                    company.lower() not in match_clean and
                    match_clean not in ['annual', 'corporate', 'esg', 'environmental']):
                    wrong_company_report = True
                    break
            
            if other_company_report or wrong_company_report:
                return False
    else:
        # For non-trusted sources and non-snippets, require company mention or trusted domain
        if not is_company_mentioned_simple(text, company, url) and not is_trusted_domain(url, company):
            return False
    
    # --- 2. Criterion-specific sanity check
    return criterion_specific_validation(criterion, evidence or {}, text)

def is_company_mentioned_simple(text: str, company: str, url: str = None) -> bool:
    """Simple company mention check"""
    text_lower = text.lower()
    company_lower = company.lower()
    
    # Create company variations
    company_variations = [
        company_lower,
        company_lower.replace(' ', ''),
        company_lower.replace('inc', '').replace('corp', '').replace('llc', '').strip(),
        company_lower.replace(' ', '-'),
    ]
    
    # Check if any variation is mentioned
    return any(var in text_lower for var in company_variations if len(var) > 2)

def criterion_specific_validation(criterion: str, evidence, text: str) -> bool:
    """Enhanced validation for specific criteria - now more demanding about context."""
    if not text:
        return False
        
    text_lower = text.lower()
    
    if criterion == 'cng_fleet':
        # Check for CNG and vehicle-related terms, but exclude savings/emissions talk
        has_cng = any(term in text_lower for term in ['cng', 'compressed natural gas', 'natural gas'])
        has_vehicle = any(term in text_lower for term in [
            'truck', 'vehicle', 'fleet', 'trailer', 'tractor', 'semi-truck', 'semi truck'
        ])
        has_savings_context = any(term in text_lower for term in ['savings', 'reduced', 'avoided', 'million metric tons'])
        return has_cng and has_vehicle and not has_savings_context
        
    elif criterion in ['total_truck_fleet_size', 'cng_fleet_size']:
        # STRICT REJECTION: EV deployment contexts for total fleet size
        if criterion == 'total_truck_fleet_size':
            ev_deployment_indicators = [
                'electric vehicles deployed', 'ev deployment', 'electric vehicle deployment',
                'number of electric vehicles', 'electric trucks deployed', 'electric fleet deployed',
                'deployed in fedex operations', 'growing from', 'doubled', 'virtually doubled'
            ]
            if any(indicator in text_lower for indicator in ev_deployment_indicators):
                return False
        
        # Check for numbers and vehicles, but exclude model numbers and orders
        has_number = any(char.isdigit() for char in text)
        has_vehicle = any(term in text_lower for term in [
            'truck', 'vehicle', 'fleet', 'trailer', 'tractor', 'semi-truck', 'semi truck'
        ])
        has_model_context = any(term in text_lower for term in ['eactros', 'e-actros', 'model', 'new', 'order'])
        
        # For CNG fleet size, add minimum threshold and exclude parts/valve context
        if criterion == 'cng_fleet_size':
            has_parts_context = any(term in text_lower for term in [
                'valve', 'k5t', 'oe number', 'part number', 'replacement', 'spare', 'component',
                'egr', 'catalog', 'parts list', 'inventory'
            ])
            
            # Extract number and check minimum threshold
            number_match = re.search(r'\b(\d+[\d,]*)\b', text)
            if number_match:
                try:
                    # Strip all non-digits before parsing
                    number_str = number_match.group(1)
                    number_clean = re.sub(r'[^\d]', '', number_str)
                    if number_clean:
                        number_value = int(number_clean)
                        if number_value < 1:  # Any positive number of CNG vehicles is meaningful
                            if evidence:
                                evidence.found = False
                                evidence.score = 0
                                evidence.evidence_text = "Number too small for meaningful CNG fleet size"
                            return False
                except (ValueError, AttributeError):
                    if evidence:
                        evidence.found = False
                        evidence.score = 0
                        evidence.evidence_text = "Could not parse vehicle count"
                    return False
            
            return has_number and has_vehicle and not has_model_context and not has_parts_context
        
        # For total_truck_fleet_size specifically, require truck-related terms, not just vans
        if criterion == 'total_truck_fleet_size':
            # STRICT REJECTION: Employee counts, warehouse counts, fulfillment centers
            employee_indicators = [
                'employees', 'workers', 'team members', 'staff', 'associates', 'workforce',
                'fulfillment centers', 'warehouses', 'facilities', 'distribution centers',
                'offices', 'locations', 'sites', 'stores', 'full-time', 'part-time'
            ]
            if any(indicator in text_lower for indicator in employee_indicators):
                return False
            
            has_truck_context = any(term in text_lower for term in [
                'truck', 'trailer', 'tractor', 'semi-truck', 'semi truck', 'tractor-trailer',
                'hgv', 'heavy goods', 'commercial vehicle', 'freight', 'big rig', 'vehicles'
            ])
            has_van_only = 'van' in text_lower and not any(term in text_lower for term in [
                'truck', 'trailer', 'tractor', 'semi-truck', 'commercial'
            ])
            
            # ADDITIONAL: Exclude specific FedEx EV deployment language
            fedex_ev_deployment = any(phrase in text_lower for phrase in [
                'fy22 to fy23', 'fy23 to fy24', 'electric vehicles deployed in fedex operations',
                'both on- and off-road', 'virtually doubled'
            ])
            
            return has_number and has_truck_context and not has_model_context and not has_van_only and not fedex_ev_deployment
        
        return has_number and has_vehicle and not has_model_context
        
    elif criterion == 'clean_energy_partner':
        # ENHANCED: Require external partnerships, not on-site generation
        has_partnership_terms = any(term in text_lower for term in [
            'partnered with', 'partnership with', 'agreement with', 'signed with',
            'contracted with', 'working with', 'collaborated with',
            'signed an agreement', 'signed agreement', 'agreement to', 'partners with',
            'partnership', 'agreement', 'contract', 'collaboration', 'supplier',
            'ppa', 'power purchase agreement'
        ])
        
        has_energy_context = any(term in text_lower for term in [
            'energy', 'fuel', 'renewable', 'clean', 'solar', 'wind', 'charging',
            'sustainable', 'aviation fuel', 'saf', 'green', 'carbon neutral',
            'power purchase', 'electricity', 'biofuel'
        ])
        
        # STRICT REJECTION: On-site generation (not partnerships)
        has_onsite_generation = any(term in text_lower for term in [
            'on-site renewable energy', 'on-site generation', 'solar panels on',
            'generate on-site', 'internal generation', 'our facilities generate',
            'rooftop solar', 'facility solar', 'building solar'
        ])
        
        # STRICT REJECTION: Generic investment language
        has_generic_investment = any(term in text_lower for term in [
            'largest corporate purchaser', 'gigawatts', 'capacity purchased', 
            'investment in', 'evaluating additional opportunities'
        ])
        
        return has_partnership_terms and has_energy_context and not has_onsite_generation and not has_generic_investment
        
    elif criterion == 'alt_fuels':
        # Require specific operational context, not generic mentions
        has_alt_fuel = any(term in text_lower for term in [
            'electric', 'hydrogen', 'biodiesel', 'biogas', 'rng', 'renewable'
        ])
        has_operational_context = any(term in text_lower for term in [
            'fleet', 'trucks', 'vehicles', 'operates', 'deployed', 'using'
        ])
        # Exclude generic problem statements
        has_problem_context = any(term in text_lower for term in [
            'the problem', 'challenges', 'industry needs', 'global push'
        ])
        return has_alt_fuel and has_operational_context and not has_problem_context
        
    elif criterion == 'regulatory':
        # ENHANCED: Must be compliance/participation, not technology rollout
        url = evidence.get('url', '') if isinstance(evidence, dict) else getattr(evidence, 'url', '')
        
        # STRICT REJECTION: Technology rollout content
        technology_rollout_indicators = [
            'autonomous delivery technologies', 'technology modernization', 
            'modernization of truck regulations', 'adoption of technologies',
            'innovation', 'technological advancement', 'future technology',
            'technology development', 'emerging technologies'
        ]
        
        has_technology_rollout = any(indicator in text_lower for indicator in technology_rollout_indicators)
        if has_technology_rollout:
            return False
        
        # REQUIRE: Actual compliance/participation language
        compliance_indicators = [
            'smartway', 'epa smartway', 'smartway member', 'smartway partner',
            'carb', 'carb certified', 'carb compliance', 'low-nox',
            'complies with', 'compliance with', 'certified', 'member of',
            'participates in', 'subject to regulations', 'regulatory oversight',
            'meets standards', 'follows regulations'
        ]
        
        has_compliance = any(indicator in text_lower for indicator in compliance_indicators)
        
        # Apply existing regulatory content validation
        has_regulatory = any(term in text_lower for term in [
            'regulation', 'compliance', 'requirement',  # Direct regulatory terms
            'regulatory', 'scrutiny', 'oversight',      # Regulatory pressure terms
            'regulators', 'regulatory pressure', 'regulatory environment',  # Regulatory context
            'carb', 'epa', 'environmental protection agency',  # Specific agencies
            'clean air act', 'zev mandate', 'smartway',          # Specific regulations
            'highly regulated', 'regulated industry',    # Regulatory status terms
            'comply with', 'complies with', 'compliance with', 'subject to',
            'laws', 'rules', 'regulations', 'filing', 'filings'
        ])
        
        # REJECT non-environmental regulatory content
        has_non_environmental = any(term in text_lower for term in [
            'data governance', 'data quality', 'data protection', 'data privacy',
            'cybersecurity', 'information security', 'it compliance', 'software compliance',
            'financial reporting', 'sox compliance', 'audit compliance',
            'hr compliance', 'employment law', 'labor relations',
            'technical support', 'troubleshooting', 'monitoring', 'system administration',
            'user access', 'authentication', 'authorization', 'database'
        ])
        
        # REJECT job description content
        has_job_description = any(term in text_lower for term in [
            'transport compliance manager', 'compliance manager', 'job description',
            'responsibilities include', 'role responsibilities', 'job duties',
            'position requires', 'candidate will', 'applicant must',
            'uphold standards', 'improve and streamline', 'diving deep',
            'find practical solutions', 'programme', 'associate'
        ])
        
        has_boilerplate = any(term in text_lower for term in [
            'unless it would violate', 'notice of any legal', 'template', 'boilerplate'
        ])
        
        # ENHANCED: Prefer explicit compliance evidence
        return (has_compliance or has_regulatory) and not has_non_environmental and not has_job_description and not has_boilerplate
    
    elif criterion == 'emission_reporting':
        # Require specific reporting language, not generic third-party descriptions or TOC entries
        has_reporting_verb = any(term in text_lower for term in [
            'published', 'disclosed', 'released', 'issued', 'filed', 'submitted',
            'we publish', 'we disclose', 'we report', 'we issue', 'we release'
        ])
        has_sustainability = any(term in text_lower for term in [
            'sustainability', 'esg', 'environmental', 'emissions', 'carbon'
        ])
        has_third_party_generic = any(term in text_lower for term in [
            'corporate target monitoring', 'third-party use cases', 'for organizations'
        ])
        # EXCLUDE table of contents and generic index entries
        has_toc_language = any(term in text_lower for term in [
            'table of contents', 'reporting index', 'metric disclosure', 'overview',
            'page ', 'section ', 'chapter ', 'appendix', 'index'
        ])
        return has_reporting_verb and has_sustainability and not has_third_party_generic and not has_toc_language
        
    # For other criteria, basic validation
    return len(text) > 10 