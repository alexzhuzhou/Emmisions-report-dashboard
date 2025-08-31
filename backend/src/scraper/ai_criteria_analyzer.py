import os
import json
import logging
import re
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
import openai
from openai import OpenAI
from pathlib import Path
import time
from fuzzywuzzy import fuzz
import random

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration constants
CRITERION_DEADLINE_SEC = 60  # Maximum time per criterion to prevent monopolization
MAX_BATCHES_PER_CRITERION = 10  # Increased from 6 to 10 for more thorough analysis

@dataclass
class CriteriaEvidence:
    """Evidence found for a specific criterion"""
    criterion: str
    found: bool
    score: int  # 0-3 score (matches AI output and system expectations)
    evidence_text: str
    justification: str
    url: str
    source_type: str = "web_content"  # web_content, search_snippet, pdf_content
    verified: bool = False  # Whether the evidence was verified by the AI
    full_context: str = ""  # The full original passage for verification
    confidence: int = 0  # 0-100 confidence in this finding
    potential_issues: str = ""  # Any concerns about data quality or interpretation
    
    # NEW: Extracted numeric data for fleet size criteria
    extracted_number: Optional[int] = None  # The actual numeric value (e.g., 3500)
    extracted_unit: Optional[str] = None    # The unit (e.g., "vehicles", "trucks")
    numeric_range: Optional[Tuple[int, int]] = None  # For ranges like "5,000-10,000 vehicles"
    
def batch_text(text: str, max_length: int = 4000) -> List[str]:
    """Split text into batches for AI analysis"""
    if len(text) <= max_length:
        return [text]
    
    # Split by sentences first, then batch
    sentences = re.split(r'(?<=[.!?])\s+', text)
    batches = []
    current_batch = ""
    
    for sentence in sentences:
        if len(current_batch) + len(sentence) + 1 <= max_length:
            current_batch += " " + sentence if current_batch else sentence
        else:
            if current_batch:
                batches.append(current_batch)
            current_batch = sentence
    
    if current_batch:
        batches.append(current_batch)
    
    return batches

def batch_text_with_overlap(text: str, max_length: int = 4000, overlap: int = 500) -> List[str]:
    """Split text into batches with overlap to prevent sentence splitting"""
    if len(text) <= max_length:
        return [text]
    
    # Split by sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text)
    batches = []
    current_batch = ""
    overlap_buffer = ""
    
    for sentence in sentences:
        if len(current_batch) + len(sentence) + 1 <= max_length:
            current_batch += " " + sentence if current_batch else sentence
        else:
            if current_batch:
                batches.append(current_batch)
                
                # Create overlap buffer from end of current batch
                words = current_batch.split()
                overlap_words = []
                overlap_chars = 0
                
                # Take words from the end until we reach overlap limit
                for word in reversed(words):
                    if overlap_chars + len(word) + 1 <= overlap:
                        overlap_words.insert(0, word)
                        overlap_chars += len(word) + 1
                    else:
                        break
                
                overlap_buffer = " ".join(overlap_words)
                
            # Start new batch with overlap + current sentence
            current_batch = overlap_buffer + " " + sentence if overlap_buffer else sentence
    
    if current_batch:
        batches.append(current_batch)
    
    return batches

# def _make_openai_call(context: str, criterion: str, company_name: str, is_retry: bool = False) -> Dict:
#     """
#     Make OpenAI API call with timeout and error handling.
#     Enhanced with exponential backoff rate limiting to prevent 429 errors.
#     """
#     # OPTIMIZED: Better rate limiting with exponential backoff
#     if is_retry:
#         time.sleep(2.0 + random.uniform(0, 1.0))  # Longer delay for retries
#     else:
#         time.sleep(0.8 + random.uniform(0, 0.4))  # Base delay: 0.8-1.2 seconds
    
#     # Use GPT-4o-mini for better cost efficiency
#     try:
#         import openai
        
#         response = openai.chat.completions.create(
#             model="gpt-4o-mini",  # Cheaper and faster than GPT-4
#             messages=[
#                 {"role": "system", "content": f"You are a sustainability analyst. Analyze if {company_name} meets the specific criterion in the given text."},
#                 {"role": "user", "content": f"""
#                 Criterion: {criterion}
#                 Company: {company_name}
#                 Text: {context[:4000]}
                
#                 Return JSON:
#                 {{
#                     "criteria_found": true/false,
#                     "score": 0-3,
#                     "quote": "exact quote from text (15-80 words)",
#                     "justification": "brief explanation"
#                 }}
#                 """}
#             ],
#             temperature=0.1,
#             max_tokens=500,  # Limit tokens for efficiency
#             timeout=20  # Shorter timeout
#         )
        
#         result_text = response.choices[0].message.content.strip()
        
#         # Parse JSON response
#         try:
#             # ENHANCED: Handle JSON wrapped in markdown code blocks
#             cleaned_text = result_text.strip()
            
#             # Remove markdown code block markers if present
#             if cleaned_text.startswith('```json'):
#                 cleaned_text = cleaned_text[7:]  # Remove ```json
#             elif cleaned_text.startswith('```'):
#                 cleaned_text = cleaned_text[3:]  # Remove ```
            
#             if cleaned_text.endswith('```'):
#                 cleaned_text = cleaned_text[:-3]  # Remove trailing ```
            
#             cleaned_text = cleaned_text.strip()
            
#             result = json.loads(cleaned_text)
            
#             # Validate and clean up the response
#             validated_result = {}
#             for criterion in criteria:
#                 if criterion in result:
#                     criterion_data = result[criterion]
#                     validated_result[criterion] = {
#                         'criteria_found': bool(criterion_data.get('criteria_found', False)),
#                         'score': max(0, min(3, int(criterion_data.get('score', 0)))),  # Clamp to 0-3
#                         'quote': str(criterion_data.get('quote', ''))[:200],  # Limit quote length
#                         'justification': str(criterion_data.get('justification', ''))[:300]  # Limit justification
#                     }
#                 else:
#                     # Add missing criteria as not found
#                     validated_result[criterion] = {
#                         'criteria_found': False,
#                         'score': 0,
#                         'quote': '',
#                         'justification': 'Not found in text'
#                     }
            
#             return validated_result
        
#         except json.JSONDecodeError as e:
#             logger.error(f"Failed to parse multi-criteria JSON response: {e}")
#             logger.error(f"Response was: {result_text}")
            
#             # Fallback: return empty results for all criteria
#             return {criterion: {
#                 'criteria_found': False,
#                 'score': 0,
#                 'quote': '',
#                 'justification': 'JSON parsing failed'
#             } for criterion in criteria}
        
#     except Exception as e:
#         if "rate_limit" in str(e).lower() or "429" in str(e):
#             # Exponential backoff for rate limits
#             backoff_time = 5.0 + random.uniform(0, 5.0)
#             logger.warning(f"Rate limited, backing off {backoff_time:.1f}s")
#             time.sleep(backoff_time)
        
#         logger.error(f"OpenAI API call failed: {e}")
#         return {"criteria_found": False, "score": 0, "quote": "", "justification": f"API error: {str(e)[:50]}"}

# def call_openai_criterion(context: str, criterion: str, company_name: str, max_retries: int = 1) -> Dict:
#     """
#     OPTIMIZED: Reduced retries and better error handling.
#     """
#     for attempt in range(max_retries + 1):
#         result = _make_openai_call(context, criterion, company_name, is_retry=(attempt > 0))
            
#         if result.get("criteria_found") or attempt >= max_retries:
#                 return result
        
#         # Only retry if there was an API error, not if content was irrelevant
#         if "error" not in result.get("justification", "").lower():
#             break
    
#     return result

def analyze_text_with_ai_batched(text: str, url: str, needed: Set[str], company: str) -> Dict[str, CriteriaEvidence]:
    """
    OPTIMIZED: Analyze multiple criteria in a single OpenAI call to reduce API usage by ~70%.
    """
    findings = {}
    

    
    # Configuration constants
    first_chunk_chars = 25000  # For fallback text sampling when keyword filtering is too aggressive
    
    # Determine source type
    source_type = "pdf_content" if url.lower().endswith('.pdf') else "web_content"
    if 'search_snippet' in url.lower() or len(text) < 500:
        source_type = "search_snippet"
    
    # Keep original text - let keyword filtering handle optimization
    analysis_text = text
    
    # OPTIMIZATION: Keyword pre-filtering to skip irrelevant chunks
    # Build combined keyword set for all needed criteria
    criteria_keywords = {
        'total_truck_fleet_size': [
            # Core terms
            'fleet', 'truck', 'vehicle', 'trailer', 'tractor', 'approximate', 'operates', 'total',
            # Expanded variations
            'trucks', 'vehicles', 'trailers', 'tractors', 'fleet size', 'number of trucks', 'truck count',
            'transportation fleet', 'delivery vehicles', 'commercial vehicles', 'motor vehicles',
            'semi-truck', 'semi truck', 'big rig', 'freight vehicles', 'logistics fleet',
            'owns', 'maintains', 'operates', 'deployed', 'utilizes', 'manages'
        ],
        'cng_fleet': [
            # Core terms  
            'cng', 'compressed natural gas', 'natural gas', 'lng', 'biogas',
            # Expanded variations
            'ngv', 'natural gas vehicles', 'cng-powered', 'gas-powered', 'cng trucks', 'cng vehicles',
            'natural gas trucks', 'natural gas fleet', 'compressed gas', 'methane', 'clean fuel',
            'alternative fuel vehicles', 'gas fuel', 'cng technology', 'natural gas technology'
        ],
        'cng_fleet_size': [
            # Core terms
            'cng', 'compressed natural gas', 'natural gas vehicle', 'fleet size',
            # Expanded variations  
            'ngv', 'cng trucks', 'cng vehicles', 'natural gas trucks', 'natural gas fleet',
            'cng-powered vehicles', 'gas-powered trucks', 'cng tractors', 'cng-fueled',
            'compressed gas vehicles', 'methane', 'clean fuel', 'alternative fuel vehicles',
            'gas fuel', 'cng technology', 'natural gas technology',
            # NEW: Context terms that often appear near fleet size info
            'number of cng', 'cng count', 'natural gas vehicle count', 'operates cng',
            'owns cng', 'cng fleet composition', 'portion cng', 'percentage cng',
            'cng deployment', 'cng operations', 'alternative fuel breakdown',
            'fleet mix', 'vehicle types', 'fuel composition', 'green fleet',
            'clean vehicles', 'environmental fleet', 'sustainable transportation'
        ],
        'emission_reporting': [
            # Core terms
            'emission', 'sustainability report', 'esg report', 'environmental', 'carbon', 'ghg',
            # Expanded variations
            'emissions', 'carbon footprint', 'greenhouse gas', 'environmental report', 'climate report',
            'sustainability disclosure', 'environmental disclosure', 'carbon disclosure', 'esg disclosure',
            'annual sustainability', 'corporate responsibility', 'environmental impact', 'carbon inventory',
            'emission data', 'environmental performance', 'climate data', 'sustainability metrics'
        ],
        'emission_goals': [
            # Core terms
            'net zero', 'carbon neutral', 'emission', 'target', 'goal', 'reduction', 'climate',
            # Expanded variations
            'net-zero', 'carbon neutrality', 'emission reduction', 'climate goals', 'climate targets',
            'sustainability goals', 'environmental goals', 'carbon goals', 'decarbonization',
            'emission targets', 'greenhouse gas reduction', 'ghg reduction', 'carbon reduction',
            'climate commitment', 'environmental commitment', 'sustainability commitment',
            'science-based targets', 'carbon footprint reduction'
        ],
        'alt_fuels': [
            # ENHANCED: Focus on true alternative fuels, not CNG/LNG
            'biodiesel', 'renewable diesel', 'biogas', 'rng', 'renewable natural gas', 
            'sustainable aviation fuel', 'saf', 'biofuel', 'bio-diesel', 'bio-gas',
            'alternative fuel', 'renewable fuel', 'b20', 'b5', 'r99', 'neste',
            'ground diesel', 'biodiesel blend', 'renewable fuel standard',
            # Additional variations
            'biofuels', 'bio fuel', 'renewable fuels', 'clean fuel', 'green fuel',
            'sustainable fuel', 'alternative energy', 'renewable energy', 'clean energy',
            'bio-based fuel', 'low-carbon fuel', 'carbon-neutral fuel'
        ],
        'clean_energy_partner': [
            # Core terms
            'partnership', 'agreement', 'clean energy', 'trillium', 'renewable energy',
            # ENHANCED: Modern SAF and renewable energy providers
            'neste', 'world energy', 'bp', 'shell', 'chevron renewable', 'renewable diesel',
            'sustainable aviation fuel', 'saf', 'brightdrop', 'gm envolve', 'tesla',
            'renewable natural gas', 'clean energy fuels', 'bp pulse', 'shell recharge',
            'electrify america', 'chargepoint', 'evgo', 'renewable fuel', 'biofuel partnership',
            # Additional partnership terms
            'partner', 'collaboration', 'alliance', 'joint venture', 'supplier', 'vendor',
            'fuel supplier', 'energy supplier', 'fuel provider', 'energy provider',
            'fuel partnership', 'energy partnership', 'strategic partnership'
        ],
        'regulatory': [
            # ENHANCED: Focus on compliance/participation, not violations
            'smartway', 'carb', 'epa program', 'compliance', 'certified', 'participate',
            'regulatory compliance', 'environmental compliance', 'subject to regulations',
            'operates under', 'governed by', 'sec filing', '10-k', 'regulated industry',
            'freight regulations', 'transportation regulations', 'environmental standards',
            # Additional regulatory terms
            'regulation', 'regulations', 'regulatory', 'compliant', 'certification',
            'environmental standards', 'industry standards', 'federal regulations',
            'state regulations', 'dot regulations', 'fmcsa', 'transportation standards'
        ]
    }
    
    # Check if text contains any relevant keywords
    relevant_keywords = set()
    for criterion in needed:
        relevant_keywords.update(criteria_keywords[criterion])
    
    # OPTIMIZATION: Keyword-first batching - only process relevant paragraphs
    # Split text into paragraphs and filter by keyword relevance
    paragraphs = analysis_text.split('\n')
    relevant_paragraphs = []
    
    # IMPROVED: More conservative filtering with context preservation
    for i, paragraph in enumerate(paragraphs):
        para_lower = paragraph.lower()
        should_include = False
        
        # Rule 1: Keep paragraphs with relevant keywords
        if any(keyword in para_lower for keyword in relevant_keywords):
            should_include = True
            
        # Rule 2: Keep short lines for context (headers, etc.)
        elif len(paragraph.strip()) < 100:
            should_include = True
            
        # Rule 3: Keep paragraphs with numbers (often contain fleet sizes, scores, etc.)
        elif any(char.isdigit() for char in paragraph) and len(paragraph.strip()) > 20:
            should_include = True
            
        # Rule 4: Keep paragraphs mentioning the company (company-specific context)
        elif company.lower() in para_lower and len(paragraph.strip()) > 30:
            should_include = True
            
        # Rule 5: Context preservation - keep paragraphs around keyword matches
        elif i > 0 and i < len(paragraphs) - 1:
            prev_para = paragraphs[i-1].lower()
            next_para = paragraphs[i+1].lower()
            # If previous or next paragraph has keywords, keep this one too
            if (any(keyword in prev_para for keyword in relevant_keywords) or 
                any(keyword in next_para for keyword in relevant_keywords)):
                should_include = True
        
        if should_include:
            relevant_paragraphs.append(paragraph)
    
    # Rebuild text from relevant paragraphs only
    if relevant_paragraphs:
        analysis_text = '\n'.join(relevant_paragraphs)
        reduction_pct = 100 - int(100 * len(analysis_text) / len(text))
        logger.debug(f"Keyword filtering reduced text from {len(text)} to {len(analysis_text)} chars (~{reduction_pct}% reduction)")
        
        # IMPROVED: More intelligent fallback with multiple recovery strategies
        if reduction_pct > 90 and len(analysis_text) < 1000:
            logger.warning(f"Keyword filtering too aggressive ({reduction_pct}% reduction), using intelligent fallback")
            
            # Strategy 1: Add company-specific paragraphs
            company_paragraphs = [p for p in paragraphs if company.lower() in p.lower() and len(p.strip()) > 20]
            
            # Strategy 2: Add paragraphs with numbers (likely contain metrics)
            numeric_paragraphs = [p for p in paragraphs if any(char.isdigit() for char in p) and len(p.strip()) > 30]
            
            # Strategy 3: Add first chunk for context
            first_chunk = text[:first_chunk_chars] if len(text) > first_chunk_chars else text
            
            # Combine strategies
            fallback_content = []
            fallback_content.extend(relevant_paragraphs)  # Keep what we found
            fallback_content.extend(company_paragraphs[:5])  # Add up to 5 company paragraphs
            fallback_content.extend(numeric_paragraphs[:3])  # Add up to 3 numeric paragraphs
            
            # If still too small, add first chunk
            combined_fallback = '\n'.join(set(fallback_content))  # Remove duplicates
            if len(combined_fallback) < 2000:
                analysis_text = first_chunk + "\n\n" + combined_fallback
                logger.debug(f"Used first chunk + targeted content = {len(analysis_text)} chars")
            else:
                analysis_text = combined_fallback
                logger.debug(f"Used targeted fallback content = {len(analysis_text)} chars")
                
        # IMPROVED: Also check if we have enough content for meaningful analysis
        elif len(analysis_text.strip()) < 500:  # Too little content overall
            logger.warning(f"Filtered content too small ({len(analysis_text)} chars), adding safety content")
            # Add first 10 paragraphs as safety net
            safety_paragraphs = paragraphs[:10]
            analysis_text = '\n'.join(set(relevant_paragraphs + safety_paragraphs))
            logger.debug(f"Added safety content, total: {len(analysis_text)} chars")
    else:
        # Fallback: if no keywords found, use intelligent sampling instead of just first chunk
        if len(text) > first_chunk_chars:
            # Sample from beginning, middle, and end
            chunk_size = first_chunk_chars // 3
            beginning = text[:chunk_size]
            middle_start = len(text) // 2 - chunk_size // 2
            middle = text[middle_start:middle_start + chunk_size]
            end = text[-chunk_size:]
            
            analysis_text = beginning + "\n\n[...MIDDLE SECTION...]\n\n" + middle + "\n\n[...END SECTION...]\n\n" + end
            logger.debug(f"No keyword matches, using intelligent sampling: {len(analysis_text)} chars")
        else:
            analysis_text = text
            logger.debug(f"No keyword matches, using full text ({len(text)} chars)")
    
    # Batch the filtered text with overlap to prevent sentence splitting
    batches = batch_text_with_overlap(analysis_text, max_length=8000, overlap=500)  # 500 char overlap
    logger.debug(f"Created {len(batches)} batches from {len(analysis_text)} chars for {url}")
    
    # MONITORING: Track filtering effectiveness for continuous improvement
    original_batches = len(batch_text_with_overlap(text, max_length=8000, overlap=500))
    filtered_batches = len(batches)
    if original_batches > 0:
        batch_reduction = 100 - int(100 * filtered_batches / original_batches)
        logger.debug(f"Batch reduction: {original_batches} → {filtered_batches} batches ({batch_reduction}% reduction)")
        
        # Log when filtering might be too aggressive for review
        if batch_reduction > 80 and len(needed) <= 3:  # High reduction with few criteria
            logger.info(f"High filtering efficiency: {batch_reduction}% batch reduction for {len(needed)} criteria - monitor for missed evidence")
    
    # Process all batches regardless of source type - quality over artificial cost savings
    max_batches = len(batches)  # Process all content to avoid missing valuable information
    
    for i in range(max_batches):
        batch = batches[i]
        
        # MODIFIED: Continue searching for better evidence instead of early exit  
        remaining_criteria = needed - findings.keys()
        if not remaining_criteria:  # All criteria found? Check if quality is good enough
            # Calculate average evidence quality for found criteria
            total_score = sum(evidence.score for evidence in findings.values())
            avg_score = total_score / len(findings) if findings else 0
            quality_threshold = 2.0  # Target average score of 2.0/3.0
            
            if avg_score >= quality_threshold:
                logger.info(f"All {len(needed)} criteria found with high quality (avg score: {avg_score:.2f})! Stopping analysis early at batch {i+1}")
                break
            else:
                logger.info(f"All {len(needed)} criteria found but continuing search for better evidence (avg score: {avg_score:.2f})")
                # Continue processing to find better evidence
        
        logger.debug(f"Processing batch {i+1}/{max_batches}, still need: {list(remaining_criteria)}")
        
        # Note: Keyword filtering already done at paragraph level, so all batches should be relevant
        
        try:
            # EFFICIENCY: Multi-criteria analysis in single call
            # FIXED: Always pass ALL needed criteria to each batch so multi-criteria evidence can be found
            logger.debug(f"Making OpenAI API call for batch {i+1}/{max_batches} with {len(needed)} criteria")
            multi_result = call_openai_multi_criteria(batch, needed, company)
            
            # Process results for each criterion
            for criterion in needed:
                # FIXED: Don't skip criteria that were found in previous batches - allow better evidence to replace worse
                criterion_result = multi_result.get(criterion, {})
                if criterion_result.get("criteria_found", False):
                    quote = criterion_result.get("quote", "")
                    # Use validated score from AI (already clamped to 0-3 in JSON validation)
                    evidence_score = criterion_result.get("score", 0)
                    
                    # Special handling for CNG fleet size with confidence flagging
                    if criterion == "cng_fleet_size":
                        confidence = int(criterion_result.get("confidence", 0))
                        potential_issues = criterion_result.get("potential_issues", "")
                        
                        # Flag only very low confidence CNG fleet size results
                        if confidence < 40:  # Reduced from 70 to 40
                            logger.warning(f"Low confidence CNG fleet size result ({confidence}%): {criterion_result.get('quote', '')[:100]}")
                            if potential_issues:
                                logger.warning(f"Potential issues: {potential_issues}")
                        
                        # Additional validation for common mistakes - but less aggressive
                        quote_lower = criterion_result.get("quote", "").lower()
                        if "alternative fuel" in quote_lower and "cng" not in quote_lower and confidence > 50:
                            logger.warning(f"Potential alternative fuel confusion in CNG fleet size: {quote_lower[:100]}")
                            evidence_score = min(evidence_score, 1)  # Reduce score for potential confusion (0-3 scale)
                    
                    evidence = CriteriaEvidence(
                        criterion=criterion,
                        found=True,
                        score=evidence_score,
                        evidence_text=quote,
                        justification=criterion_result.get("justification", ""),
                        url=url,
                        source_type=source_type,
                        verified=True,  # Trust GPT-4o-mini for direct text extraction
                        full_context=batch,  # Store the full batch text for verification
                        confidence=criterion_result.get("confidence", 0),
                        potential_issues=criterion_result.get("potential_issues", ""),
                        # NEW: Use AI-extracted numeric data directly
                        extracted_number=criterion_result.get("extracted_number"),
                        extracted_unit=criterion_result.get("extracted_unit"),
                        numeric_range=tuple(criterion_result["numeric_range"]) if "numeric_range" in criterion_result and criterion_result["numeric_range"] is not None and isinstance(criterion_result["numeric_range"], list) else None
                    )
                    
                                        # Continue processing if score > 0 (trust AI scoring with detailed rubrics)
                    if evidence_score > 0:
                        # # ACCURACY IMPROVEMENT: Reduce scores for old sources and planning/order evidence
                        # # Check for old sources (pre-2023)
                        # year_match = re.search(r'(202[0-9]|201[0-9])', url + quote)
                        # if year_match:
                        #     source_year = int(year_match.group(1))
                        #     if source_year < 2023:
                        #         evidence_score = max(1, evidence_score - 1)  # Reduce by 1, minimum 1
                        #         logger.info(f"Reduced {criterion} score for old source ({source_year})")
                    
                        # # Check for planning/ordering vs operational language
                        # quote_lower = quote.lower()
                        # planning_words = ['order', 'ordered', 'plan', 'planning', 'will', 'announce', 'target', 'goal', 'intend']
                        # operational_words = ['operate', 'operates', 'currently', 'deployed', 'fleet includes', 'has', 'using', 'runs']
                        
                        # has_planning = any(word in quote_lower for word in planning_words)
                        # has_operational = any(word in quote_lower for word in operational_words)
                        
                        # # Reduce score if it's clearly about plans/orders, not current operations
                        # if has_planning and not has_operational and criterion in ['cng_fleet', 'cng_fleet_size', 'total_truck_fleet_size', 'alt_fuels']:
                        #     evidence_score = max(1, evidence_score - 1)  # Reduce by 1, minimum 1
                        #     logger.info(f"Reduced {criterion} score for planning/order evidence")
                        
                        # # Update evidence with revised score
                        # evidence.score = evidence_score
                        
                        # # ENHANCED: Apply additional validation from ai_scorecard_integration
                        # try:
                        #     from .ai_scorecard_integration import validate_evidence_against_rubric
                        #     evidence = validate_evidence_against_rubric(evidence)
                        #     # Check if validation marked evidence as invalid
                        #     if not evidence.found:
                        #         continue  # Skip to next criterion if validation failed
                        # except ImportError:
                        #     logger.debug("Enhanced validation not available")
                        # except Exception as e:
                        #     logger.warning(f"Validation failed for {criterion}: {e}, using original evidence")
                        #     # Continue with original evidence if validation fails
                        
                        # Only update if this is better evidence than what we already have
                        if criterion not in findings or evidence.score > findings[criterion].score:
                            findings[criterion] = evidence
                            logger.info(f"Found {criterion} evidence (batch {i+1}) - BATCHED ANALYSIS")
            
        except Exception as e:
            logger.warning(f"Batched AI analysis failed for batch {i+1}: {e}")
            continue
    
    return findings

def call_openai_multi_criteria(text: str, criteria: Set[str], company_name: str) -> Dict[str, Dict]:
    """
    ENHANCED: Analyze multiple criteria in single API call with better evidence validation.
    Now includes specific guidance to distinguish fuel consumption vs fleet size, violations vs compliance.
    """
    if not criteria:
        return {}
    
    # Enhanced criterion descriptions with validation rules
    criterion_descriptions = {
        'total_truck_fleet_size': """
        Total Truck Fleet Size (Score 0-3):
        0 = No fleet size information
        1 = Vague fleet references ("large fleet") OR small fleets (1-999 vehicles)
        2 = Approximate numbers ("approximately 30,000") OR medium fleets (1,000-9,999 vehicles)
        3 = Specific exact numbers with operational context OR large fleets (10,000+ vehicles)
        CRITICAL: Must be TOTAL/OVERALL vehicle count for ALL vehicle types, not just one fuel type.
        Accept: "operates 30,000 trucks", "fleet of 50,000 vehicles", "maintains 15,000 tractors"


        
        **EXTRACTION REQUIRED**: When found, extract the specific number into "extracted_number" field.
        Examples: "30,000 trucks" → extracted_number: 30000, extracted_unit: "vehicles"
        Handle: "15K vehicles" → 15000, "2.5 million trucks" → 2500000, "approximately 45,000" → 45000
        """,
        
        'cng_fleet_size': """
        CNG Fleet Size (Score 0-3):
        0 = No CNG fleet size (exploring/planning doesn't count)
        1 = Small CNG fleet (1-10 vehicles)
        2 = Medium CNG fleet (11-50 vehicles)
        3 = Large CNG fleet (51+ vehicles)
        
        CRITICAL: Must be NUMBER OF CNG VEHICLES specifically, not fuel consumption.
        
        ⚠️ IMPORTANT DISTINCTION: "Alternative fuel" vs "CNG-only" vehicles
        ACCEPT: "operates 200 CNG trucks", "4,400 CNGs on the road", "fleet of 500 natural gas vehicles"
        ACCEPT: "has 1,200 CNG tractors", "compressed natural gas fleet of 800 vehicles"
        ACCEPT: "18,000 alternative fuel vehicles including 3,200 CNG trucks" (extract the CNG portion)
        
        REJECT: "5,238 gallons of CNG consumed", "CNG fuel consumption data", "natural gas delivered"
        REJECT: "18,000 alternative fuel vehicles" (without CNG breakdown - flag as uncertain)
        REJECT: Numbers that refer to ALL fuel types combined without CNG breakdown
        
        ⚠️ GUIDANCE: If text mentions both "alternative fuel" numbers AND specific CNG numbers,
        prioritize the CNG-specific numbers. If only alternative fuel totals are given without
        CNG breakdown, set confidence to 30-50% rather than rejecting entirely.
        
        REJECT: Fuel volume/gallons/consumption statistics - these are NOT vehicle counts
        REJECT: Product pages, e-commerce sites, marketing materials unless fleet operations context
        REJECT: Third-party analysis unless from SEC, company reports, or trusted industry sources
        
        **EXTRACTION REQUIRED**: When found, extract the CNG-specific number into "extracted_number" field.
        Examples: "3,500 CNG vehicles" → extracted_number: 3500, extracted_unit: "vehicles"
        Handle: "6K CNG trucks" → 6000, "approximately 1,200 CNGs" → 1200
        For ranges: "5,000-10,000 CNG vehicles" → numeric_range: [5000, 10000]
        """,
        
        'cng_fleet': """
        CNG Fleet (Score 0-1):
        0 = No current CNG fleet operations
        1 = Currently operates CNG vehicles
        Must show CURRENT operations, not just fuel availability or planning.
        """,
        
        'emission_reporting': """
        Emission Reporting (Score 0-1):
        0 = No evidence of publishing emissions/sustainability reports
        1 = Publishes emissions/sustainability reports
        Look for: "publishes sustainability report", "discloses emissions data"
        """,
        
        'emission_goals': """
        Emission Goals (Score 0-2):
        0 = No emission reduction goals
        1 = Basic emission reduction goal or net-zero commitment
        2 = Detailed targets with timeline AND interim milestones
        """,
        
        'alt_fuels': """
        Alternative Fuels (Score 0-1):
        0 = No alternative fuels
        1 = Uses biodiesel, RNG, SAF, or renewable fuels
        CRITICAL: Look for BIODIESEL, RENEWABLE NATURAL GAS (RNG), SAF, BIOFUELS.
        REJECT: Regular CNG/LNG alone (not considered "alternative" for this criterion)
        Accept: "biodiesel blends", "renewable diesel", "sustainable aviation fuel"
        """,
        
        'clean_energy_partner': """
        Clean Energy Partner (Score 0-1):
        0 = No partnerships
        1 = Has partnerships with external clean energy/fuel providers
        CRITICAL: Must be EXTERNAL partnerships with specific providers or OEMs, not on-site generation
        
        ACCEPT - RNG/CNG Infrastructure Providers:
        - Clean Energy Fuels (Corp), Trillium CNG, Shell CNG, BP Natural Gas
        - Chevron Renewable Energy Group, Neste, World Energy
        - RNG suppliers: Brightmark, Archaea Energy, Vanguard Renewables
        
        ACCEPT - OEMs and Technology Partners:
        - Cummins (X15N CNG engines, natural gas engines)
        - Westport Fuel Systems, IVECO natural gas vehicles
        - Volvo/Mack CNG trucks, Tesla (charging infrastructure)
        - BrightDrop (GM), Rivian partnerships
        
        ACCEPT - Charging/Energy Infrastructure:
        - Electrify America, ChargePoint, EVgo partnerships
        - Solar/wind PPAs with Orsted, EDF Renewables, NextEra
        
        Look for: named external suppliers, PPAs, fuel providers, infrastructure partners, OEM agreements
        """,
        
        'regulatory': """
        Regulatory (Score 0-1):
        Question: Are they operating in sectors under high regulatory pressure (e.g., waste, freight, transit)?
        0 = Not operating in high regulatory pressure sectors
        1 = Operating in high regulatory pressure sectors (waste, freight, transit)
        
        HIGH REGULATORY PRESSURE SECTORS:
        - Freight/Trucking: Interstate commerce, DOT regulations, emission standards
        - Waste Management: EPA regulations, hazardous waste compliance, environmental permits
        - Public Transit: FTA regulations, safety standards, accessibility requirements
        
        ACCEPT: Evidence of operations in freight/logistics, waste collection/disposal, public transportation
        ACCEPT: Interstate trucking, long-haul freight, LTL/FTL operations
        ACCEPT: Waste hauling, landfill operations, recycling services
        ACCEPT: Bus transit, rail operations, municipal transportation services
        
        Look for: Industry sector identification, business operations descriptions, regulatory compliance mentions
        """
    }
    
    # Build criteria list for prompt
    criteria_list = []
    for criterion in criteria:
        if criterion in criterion_descriptions:
            criteria_list.append(f"- {criterion}: {criterion_descriptions[criterion]}")
    
    criteria_text = "\n".join(criteria_list)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},  # Force JSON-only response
            messages=[
                {"role": "system", "content": f"""You are a sustainability data analyst. Analyze text for specific sustainability criteria for {company_name}.

CRITICAL VALIDATION RULES:
1. Fleet Size: Must be VEHICLE COUNT, not fuel consumption or containers
2. CNG Fleet Size: Must be NUMBER OF CNG VEHICLES specifically, prefer CNG-only data but allow alternative fuel context with CNG breakdown
3. CNG vs Alternative Fuel: "18,000 alternative fuel vehicles" needs CNG breakdown, but don't reject entirely
4. Regulatory: Must show COMPLIANCE/PARTICIPATION, not technology rollout or violations
5. Alt Fuels: Must be BIODIESEL/RNG/SAF, not regular CNG/LNG
6. Evidence must be about CURRENT operations, not plans/orders/targets

⚠️ BALANCED APPROACH: Companies often report "total alternative fuel fleet" (includes electric, hybrid, propane, CNG, etc.) 
Look for CNG-specific breakdowns when possible, but if only total numbers exist, set lower confidence (30-50%) rather than rejecting entirely.

Be precise and only score what clearly meets the criteria. Provide comprehensive justifications (3-4 sentences) explaining your analysis, including context about industry practices, operational significance, and strategic implications."""},
                
                {"role": "user", "content": f"""
Analyze this text for {company_name} against these criteria:

{criteria_text}

Text to analyze:
{text[:6000]}

Return JSON with this exact structure using the EXACT criterion names provided above:
{{
    "total_truck_fleet_size": {{
        "criteria_found": true/false,
        "score": 0-3 (based on scoring rules above),
        "confidence": 0-100 (confidence in this finding),
        "quote": "comprehensive quote from text (50-200 words for detailed context)",
        "justification": "detailed 3-4 sentence justification explaining why this evidence meets/doesn't meet the specific criterion rules, including operational context and strategic significance",
        "potential_issues": "any concerns about data quality, source reliability, or interpretation uncertainty",
        "extracted_number": null or integer (REQUIRED for fleet size criteria: extract the specific number of vehicles, e.g., 3500),
        "extracted_unit": null or string (REQUIRED for fleet size criteria: extract the unit, e.g., "vehicles", "trucks"),
        "numeric_range": null or [min, max] (for ranges like "5,000-10,000 vehicles", return as [5000, 10000])
    }},
    "cng_fleet": {{ ... same structure ... }},
    "etc": "for each criterion requested"
}}

**CRITICAL**: Use EXACT criterion names as provided in the criteria list above. Do not modify, abbreviate, or paraphrase the criterion names.

**IMPORTANT**: For total_truck_fleet_size and cng_fleet_size criteria:
- ALWAYS extract numbers when found (convert "15K" → 15000, "2.5 million" → 2500000)
- Set extracted_unit to "vehicles" for consistency
- For ranges, use numeric_range field: "5,000-10,000 vehicles" → numeric_range: [5000, 10000]
- If no numbers found, set extracted_number: null, extracted_unit: null

Only include entries for criteria where you find evidence (criteria_found: true). Omit criteria where no evidence is found - the system will handle missing entries automatically. Provide thorough analysis with industry context for found criteria.
"""}
            ],
            temperature=0.1,
            max_tokens=2000,
            timeout=25
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.debug(f"Multi-criteria API response: {result_text[:200]}...")
        
        # Parse JSON response (simplified since response_format ensures clean JSON)
        try:
            result = json.loads(result_text)
            
            # Validate and clean up the response
            validated_result = {}
            for criterion in criteria:
                if criterion in result:
                    criterion_data = result[criterion]
                    # Extract all fields once to avoid repeated .get() calls
                    fields = {
                        'criteria_found': criterion_data.get('criteria_found', False),
                        'score': criterion_data.get('score', 0),
                        'confidence': criterion_data.get('confidence', 0),
                        'quote': criterion_data.get('quote', ''),
                        'justification': criterion_data.get('justification', ''),
                        'potential_issues': criterion_data.get('potential_issues', ''),
                        'extracted_number': criterion_data.get('extracted_number'),
                        'extracted_unit': criterion_data.get('extracted_unit'),
                        'numeric_range': criterion_data.get('numeric_range')
                    }
                    
                    # Validate and clean all fields
                    validated_result[criterion] = {
                        'criteria_found': bool(fields['criteria_found']),
                        'score': _safe_int(fields['score'], 0, min_val=0, max_val=3),
                        'confidence': _safe_int(fields['confidence'], 0, min_val=0, max_val=100),
                        'quote': _safe_str(fields['quote']),
                        'justification': _safe_str(fields['justification']),
                        'potential_issues': _safe_str(fields['potential_issues']),
                        # Numeric fields with validation
                        'extracted_number': _safe_int(fields['extracted_number']) if fields['extracted_number'] is not None else None,
                        'extracted_unit': _safe_str(fields['extracted_unit']) if fields['extracted_unit'] is not None else None,
                        'numeric_range': _validate_range(fields['numeric_range'])
                    }
                else:
                    # Add missing criteria as not found
                    validated_result[criterion] = {
                        'criteria_found': False,
                        'score': 0,
                        'confidence': 0,
                        'quote': '',
                        'justification': 'Not found in text',
                        'potential_issues': '',
                        'extracted_number': None,
                        'extracted_unit': None,
                        'numeric_range': None
                    }
            
            return validated_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse multi-criteria JSON response: {e}")
            logger.error(f"Error occurred at line {getattr(e, 'lineno', 'unknown')}, column {getattr(e, 'colno', 'unknown')}, position {getattr(e, 'pos', 'unknown')}")
            logger.error(f"Response length: {len(result_text)} characters")
            logger.error(f"Response was: {result_text}")
            
            # Try to show the problematic area
            if hasattr(e, 'pos') and e.pos:
                start = max(0, e.pos - 50)
                end = min(len(result_text), e.pos + 50)
                logger.error(f"Context around error position: '{result_text[start:end]}'")
            
            # Fallback: return empty results for all criteria
            return {criterion: {
                'criteria_found': False,
                'score': 0,
                'confidence': 0,
                'quote': '',
                'justification': 'JSON parsing failed',
                'potential_issues': '',
                'extracted_number': None,
                'extracted_unit': None,
                'numeric_range': None
            } for criterion in criteria}
            
    except Exception as e:
        logger.error(f"Multi-criteria OpenAI call failed: {e}")
        return {criterion: {
            'criteria_found': False,
            'score': 0,
            'confidence': 0,
            'quote': '',
            'justification': f'API call failed: {str(e)[:50]}',
            'potential_issues': '',
            'extracted_number': None,
            'extracted_unit': None,
            'numeric_range': None
        } for criterion in criteria}

# Replace the old single-criterion function with the batched version
def analyze_text_with_ai(text: str, url: str, needed: Set[str], company: str) -> Dict[str, CriteriaEvidence]:
    """
    OPTIMIZED: Use batched multi-criteria analysis for better efficiency.
    """
    return analyze_text_with_ai_batched(text, url, needed, company)

def verify_quote_flexible(text: str, quote: str, criterion: str) -> bool:
    """
    OPTIMIZED: Enhanced quote verification with linear-time matching (was O(n²)).
    Uses fuzz.partial_ratio for efficient fuzzy matching on large documents.
    """
    if not quote or not text:
        return False
    
    text_lower = text.lower().strip()
    quote_lower = quote.lower().strip()
    
    # For fleet size criteria, allow number-focused substring matching
    if 'fleet' in criterion:
        # Extract numbers from both text and quote
        import re
        text_numbers = re.findall(r'\b\d{1,3}[,.]?\d{0,3}[,.]?\d{0,3}\b', text)
        quote_numbers = re.findall(r'\b\d{1,3}[,.]?\d{0,3}[,.]?\d{0,3}\b', quote)
        
        # If quote contains numbers that exist in text, consider it verified
        for q_num in quote_numbers:
            clean_q_num = q_num.replace(',', '').replace('.', '')
            for t_num in text_numbers:
                clean_t_num = t_num.replace(',', '').replace('.', '')
                if len(clean_q_num) > 2 and clean_q_num == clean_t_num:
                    return True
    
    # OPTIMIZED: Use linear-time partial_ratio instead of sliding window
    # This is much faster on large PDFs (120k chars)
    from fuzzywuzzy import fuzz
    similarity = fuzz.partial_ratio(quote_lower, text_lower)
    
    # Criteria-specific thresholds (slightly lowered for efficiency)
    threshold_map = {
        'total_truck_fleet_size': 55,  # Lower for number-heavy content
        'cng_fleet_size': 55,          # Lower for number-heavy content  
        'regulatory': 60,              # Slightly lower for regulatory text
        'clean_energy_partner': 65,    # Standard for partnership text
        'alt_fuels': 65,              # Standard for fuel types
        'emission_goals': 70,         # Higher for goal statements
        'emission_reporting': 70,      # Higher for reporting statements
        'cng_fleet': 65               # Standard for CNG presence
    }
    
    threshold = threshold_map.get(criterion, 65)
    return similarity >= threshold

def should_replace_evidence_ai(new_evidence: CriteriaEvidence, existing_evidence: CriteriaEvidence) -> bool:
    """
    Determine if new AI evidence should replace existing evidence.
    """
    # Higher score wins (0-3 scale)
    if new_evidence.score > existing_evidence.score:
        return True
    
    # If scores are equal, prefer company domains
    if new_evidence.score == existing_evidence.score:
        # Simple domain preference - check if URL contains company name
        company_in_new_url = any(part in new_evidence.url.lower() for part in new_evidence.criterion.split())
        company_in_existing_url = any(part in existing_evidence.url.lower() for part in existing_evidence.criterion.split())
        
        if company_in_new_url and not company_in_existing_url:
            return True
    
    return False

def is_company_mentioned_simple(text: str, company: str, url: Optional[str] = None) -> bool:
    """
    Simple company mention check for AI analysis filtering.
    Since AI will handle context understanding, this can be more lenient.
    """
    if not text or not company:
        return False
    
    text_lower = text.lower()
    company_lower = company.lower()
    
    # Simple direct mention check
    if company_lower in text_lower:
        return True
    
    # Check for company without common suffixes
    company_clean = company_lower.replace(' inc', '').replace(' corp', '').replace(' llc', '').strip()
    if len(company_clean) > 3 and company_clean in text_lower:
        return True
    
    # If it's from a company domain, accept regardless
    if url:
        company_variations = [
            company_lower.replace(' ', ''),
            company_lower.replace(' ', '-'),
        ]
        for variation in company_variations:
            if len(variation) > 3 and variation in url.lower():
                return True
    
    return False

def _safe_int(value, default=0, min_val=None, max_val=None):
    """Safely convert value to int with bounds checking"""
    try:
        result = int(value) if value is not None else default
        if min_val is not None:
            result = max(min_val, result)
        if max_val is not None:
            result = min(max_val, result)
        return result
    except (ValueError, TypeError):
        return default

def _safe_str(value, default='', max_length=None):
    """Safely convert value to string with length limits"""
    try:
        result = str(value) if value is not None else default
        if max_length and len(result) > max_length:
            result = result[:max_length]
        return result
    except Exception:
        return default

def _validate_range(value):
    """Validate numeric range field"""
    if value is None:
        return None
    if isinstance(value, list) and len(value) == 2:
        try:
            return [int(value[0]), int(value[1])]
        except (ValueError, TypeError):
            return None
    return None

