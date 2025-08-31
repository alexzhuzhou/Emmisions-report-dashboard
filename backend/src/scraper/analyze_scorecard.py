import os
import re
import json
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import concurrent.futures
from dataclasses import dataclass, asdict
from tqdm import tqdm
from rapidfuzz import fuzz
import string
import argparse
from .utils.strings import safe_filename_for_output_path


# Load OpenAI key from project root
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
   raise ValueError("OPENAI_API_KEY not found in .env file or environment variables.")
client = OpenAI(api_key=OPENAI_API_KEY)


# --- Constants and Configurations ---
CRITERIA_KEYWORDS = { # (Your existing keywords - ensure they are effective)
   "cng_fleet": {
       "primary": ["cng", "cngs", "compressed natural gas"],
       "secondary": ["natural gas vehicle", "cng truck", "natural gas fleet"], "exclude": []
   },
   "cng_fleet_size": {
       "primary": ["cng", "cngs", "compressed natural gas"],
       "secondary": ["fleet of", "number of cng", "cng vehicles", "cng trucks"],
       "exclude": ["electric", "ev", "battery"]
   },
   "total_truck_fleet_size": { # Crucially important: this is about *TRUCKS*
       "primary": ["total fleet", "total trucks", "fleet size", "number of trucks", "our truck fleet"],
       "secondary": ["fleet consists of", "fleet includes", "our vehicles", "company-owned trucks"],
       "exclude": ["ocean fleet", "teu", "vessel", "trailers", "customer fleet", "managed fleet"] # Exclude non-truck/non-owned
   },
   "emission_reporting": {
       "primary": ["report", "csrd", "gri", "sasb", "tcfd"],
       "secondary": ["sustainability disclosure", "emissions disclosure", "ghg report", "scopes 1 2 3"], "exclude": []
   },
   "emission_goals": {
       "primary": ["net-zero", "carbon-neutral", "ghg-reduction", "sbti"],
       "secondary": ["emissions reduction", "climate target", "decarbonization", "1.5-degree"], "exclude": []
   },
   "alt_fuels": {
       "primary": ["biogas", "biodiesel", "rng", "biofuel", "bio-fuel", "bio methanol"],
       "secondary": ["renewable diesel", "sustainable fuel", "hydrogen", "electric vehicle"], "exclude": []
   },
   "clean_energy_partner": {
       "primary": ["partner", "partnership", "collaboration", "agreement"],
       "secondary": ["clean-energy", "trillium", "cummins", "x15n", "primark", "lower-emission fuels"], "exclude": []
   },
   "regulatory": {
       "primary": ["compliance", "mandate", "regulation", "imo", "eu ets", "fuelEU", "fit for 55"],
       "secondary": ["waste", "freight", "transit", "logistics", "maritime", "legislation", "geopolitical"], "exclude": []
   }
}


# Defines the *final integer score/category* for the database
# This might be derived from extracted numbers or be a direct assessment.
CRITERIA_DB_MAPPING_SCORES = {
   "cng_fleet": (0, 1), # Boolean essentially (0=No, 1=Yes)
   "cng_fleet_size_range": (0, 3), # 0=None, 1=1-10, 2=11-50, 3=51+
   "total_truck_fleet_size_score": (0, 3), # Placeholder for a categorical score if needed, actual number is separate
   "emission_reporting": (0, 1), # Boolean
   "emission_goals": (0, 2), # 0=No, 1=Mentioned, 2=Timeline/SBTi
   "alt_fuels": (0, 1), # Boolean
   "clean_energy_partner": (0, 1), # Boolean
   "regulatory": (0, 1) # Boolean
}
PAGE_SPLIT_REGEX = re.compile(r"--- Page (\d+) End ---")


# New mapping to link script's criteria to SustainabilityMetrics table columns
# and define how to extract their values.
DB_METRICS_MAPPING = {
   # SustainabilityMetrics Column_Name: {criterion_key_in_script, value_source_from_finding_object, default_value}
   "owns_cng_fleet": {"criterion_key": "cng_fleet", "value_source": "criteria_found", "default": False},
   "cng_fleet_size_range": {"criterion_key": "cng_fleet_size", "value_source": "score", "default": 0},
   "cng_fleet_size_actual": {"criterion_key": "cng_fleet_size", "value_source": "cng_fleet_size_actual", "default": 0},
   "total_fleet_size": {"criterion_key": "total_truck_fleet_size", "value_source": "total_truck_fleet_size_actual", "default": 0},
   "emission_report": {"criterion_key": "emission_reporting", "value_source": "criteria_found", "default": False},
   "emission_goals": {"criterion_key": "emission_goals", "value_source": "score", "default": 0},
   "alt_fuels": {"criterion_key": "alt_fuels", "value_source": "criteria_found", "default": False},
   "clean_energy_partners": {"criterion_key": "clean_energy_partner", "value_source": "criteria_found", "default": False},
   "regulatory_pressure": {"criterion_key": "regulatory", "value_source": "criteria_found", "default": False},
   # NEW: Added for clarity, though the score is calculated and added manually.
   "cng_adopt_score": {"criterion_key": "COMPOSITE_SCORE", "value_source": "calculated", "default": 0},
}


@dataclass
class CriterionFinding: # Renamed for clarity
   criteria_found: bool
   score: int # This will be the DB-mappable score (e.g., range for cng_fleet_size_range)
   quote: str
   justification: str
   original_passage: str
   verified: bool = False
   evidence: str = ""
   # NEW: Specific extracted values
   cng_fleet_size_actual: Optional[int] = None
   total_truck_fleet_size_actual: Optional[int] = None
   # We can add more specific extracted fields here if needed for other criteria


# --- Helper Functions ---
def split_text_by_page(text: str) -> List[str]:
   if not text: return []
   pages = []
   last_idx = 0
   for match in PAGE_SPLIT_REGEX.finditer(text):
       pages.append(text[last_idx:match.end()])
       last_idx = match.end()
   if last_idx < len(text):
       pages.append(text[last_idx:])
   if not pages and text.strip():
       return [text]
   return [p for p in pages if p.strip()]


def verify_quote(text: str, quote: str, threshold: int = 85) -> bool:
   if not quote or not text: return False
   normalized_text = re.sub(r'\s+', ' ', text.lower())
   normalized_quote = re.sub(r'\s+', ' ', quote.lower())
   if not normalized_quote: return False
   if normalized_quote in normalized_text: return True
   quote_len = len(normalized_quote)
   text_len = len(normalized_text)
   if text_len < quote_len: return False
   for i in range(0, text_len - quote_len + 1):
       window_end = min(i + quote_len + 20, text_len)
       window = normalized_text[i:window_end]
       score = fuzz.WRatio(normalized_quote, window)
       if score >= threshold: return True
   return False


def batch_text(text: str, max_length: int = 3800) -> List[str]:
   sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z#"“])', text)
   batches = []
   current_batch_list = []
   current_length = 0
   for sentence in sentences:
       sentence_length = len(sentence)
       if current_length + sentence_length + (1 if current_batch_list else 0) > max_length and current_batch_list:
           batches.append(' '.join(current_batch_list))
           current_batch_list = [sentence]
           current_length = sentence_length
       else:
           current_batch_list.append(sentence)
           current_length += sentence_length + (1 if len(current_batch_list) > 1 else 0)
   if current_batch_list:
       batches.append(' '.join(current_batch_list))
   return [b for b in batches if b.strip()]


def find_relevant_sentences(text: str, keywords: dict, window: int = 1, criterion: Optional[str] = None) -> Tuple[str, str]:
   if not text: return "", ""
   sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z#"“])', text)
   normalized_sentences = [re.sub(r'\s+', ' ', s).strip() for s in sentences if s.strip()]
   if not normalized_sentences: return "", ""
  
   relevant_matches_ordered = []
   original_passage_found = ""
   indices_added = set()


   primary_kw_list = keywords.get("primary", [])
   secondary_kw_list = keywords.get("secondary", [])


   def add_match_context(idx, kw_list_type):
       nonlocal original_passage_found
       start_idx = max(0, idx - window)
       end_idx = min(len(normalized_sentences), idx + window + 1)
       context_sentences_for_this_match = []
       current_original_passage_candidate = ' '.join(normalized_sentences[start_idx:end_idx])


       for k_idx in range(start_idx, end_idx):
           if k_idx not in indices_added:
               context_sentences_for_this_match.append(normalized_sentences[k_idx])
               indices_added.add(k_idx)
      
       if context_sentences_for_this_match:
           relevant_matches_ordered.extend(context_sentences_for_this_match)
           if not original_passage_found:
               original_passage_found = current_original_passage_candidate
       return len(relevant_matches_ordered) >= 6 * (2 * window + 1) # Limit context size slightly


   for i, sent in enumerate(normalized_sentences):
       if any(re.search(rf'\b{re.escape(kw.lower())}\b', sent.lower()) for kw in primary_kw_list):
           if add_match_context(i, "primary"): break
  
   if not relevant_matches_ordered or len(relevant_matches_ordered) < (2*window+1) : # If primary not enough
       for i, sent in enumerate(normalized_sentences):
           if any(re.search(rf'\b{re.escape(kw.lower())}\b', sent.lower()) for kw in secondary_kw_list):
               if add_match_context(i, "secondary"): break
  
   if criterion == "cng_fleet_size" and "exclude" in keywords and keywords["exclude"]:
       exclude_terms = keywords["exclude"]
       relevant_matches_ordered = [
           s for s in relevant_matches_ordered
           if not any(re.search(rf'\b{re.escape(kw.lower())}\b', s.lower()) for kw in exclude_terms)
       ]
   if criterion == "total_truck_fleet_size" and "exclude" in keywords and keywords["exclude"]:
       exclude_terms = keywords["exclude"]
       relevant_matches_ordered = [
           s for s in relevant_matches_ordered
           if not any(re.search(rf'\b{re.escape(kw.lower())}\b', s.lower()) for kw in exclude_terms)
       ]
  
   final_unique_relevant_sentences = []
   seen_sentences_for_final = set()
   for sent_text in relevant_matches_ordered:
       if sent_text not in seen_sentences_for_final:
           final_unique_relevant_sentences.append(sent_text)
           seen_sentences_for_final.add(sent_text)
  
   return '\n'.join(final_unique_relevant_sentences), original_passage_found


# --- NEW: Function to Calculate CNG Adoption Score ---
def calculate_cng_adoption_score(detailed_results: Dict[str, Dict]) -> int:
    """
    Calculates the final CNG adoption score based on a weighted average of individual criteria scores.
    The formula normalizes each criterion's raw score against its maximum possible score,
    multiplies it by its weight, and sums the results to get a score out of 100.
    """
    # Weights from the provided image (sum to 100)
    weights = {
        "cng_fleet": 10,
        "cng_fleet_size": 25,
        "emission_reporting": 10,
        "emission_goals": 15,
        "alt_fuels": 15,
        "clean_energy_partner": 15,
        "regulatory": 10,
    }

    # Maximum possible raw score for each criterion based on its Score Range in the image
    max_scores = {
        "cng_fleet": 1,
        "cng_fleet_size": 3,
        "emission_reporting": 1,
        "emission_goals": 2,
        "alt_fuels": 1,
        "clean_energy_partner": 1,
        "regulatory": 1,
    }
    
    total_score = 0.0

    # Map script criterion keys to the user-facing criteria names from the image
    criteria_name_map = {
        "cng_fleet": "CNG Fleet Presence",
        "cng_fleet_size": "CNG Fleet Size",
        "emission_reporting": "Emission Reporting",
        "emission_goals": "Emission Reduction Goals",
        "alt_fuels": "Alternative Fuels Mentioned",
        "clean_energy_partner": "Clean Energy Partnerships",
        "regulatory": "Regulatory Pressure",
    }

    print("\n--- CNG Adoption Score Calculation ---")
    for criterion_key, weight in weights.items():
        component_score = 0.0
        if criterion_key in detailed_results:
            result_data = detailed_results[criterion_key]
            raw_score = result_data.get("score", 0)
            max_score = max_scores.get(criterion_key, 1)

            if max_score > 0:
                normalized_score = raw_score / max_score
                component_score = normalized_score * weight
                total_score += component_score
            
            print(f"- {criteria_name_map.get(criterion_key, criterion_key):<30}: "
                  f"Raw Score = {raw_score}/{max_score}, Weight = {weight}%, "
                  f"Contribution = {component_score:.2f}")
        else:
            print(f"- {criteria_name_map.get(criterion_key, criterion_key):<30}: Not analyzed. Contribution = 0.00")
    
    final_score = round(total_score)
    print(f"--- Total Score: {total_score:.2f}, Rounded to: {final_score} ---")
    return final_score


# --- Modified OpenAI Call for Criteria ---
def _get_llm_response_for_criterion(context: str, criterion: str, is_retry: bool = False) -> Dict:
   """
   Makes an LLM call to analyze context for a given criterion.
   The prompt will now also ask for specific numerical values where applicable.
   """
   base_prompt_fields = """
Return your answer *only* as a single, valid JSON object with the following structure:
{{
   "criteria_found": true/false, // Boolean: Is there any relevant information?
   "score": 0, // Placeholder, will be determined by specific logic later
   "quote": "The most direct and concise quote...",
   "justification": "Brief explanation...",
   "cng_fleet_size_actual": null, // Integer or null
   "total_truck_fleet_size_actual": null // Integer or null
}}
"""
   criterion_specific_instructions = {
       "cng_fleet": "Does the company explicitly state it owns or operates a CNG fleet? (Yes/No answer reflected in 'criteria_found')",
       "cng_fleet_size": """What is the specific number of CNG trucks or vehicles the company operates or owns?
If a number is found, provide it for 'cng_fleet_size_actual'.
If a range is given (e.g., "50-60 CNG trucks"), extract the lower or average number.
If only partnerships are mentioned without specific numbers for *their* fleet, 'cng_fleet_size_actual' should be null.""",
       "total_truck_fleet_size": """What is the total number of *trucks* (not trailers, not TEU, not ocean vessels, not assets managed for others) in the company's *directly owned or operated* fleet?
If a number is found, provide it for 'total_truck_fleet_size_actual'.
If the text mentions "Ocean fleet size ... TEUm" or "number of vessels", this is NOT the truck fleet size; 'total_truck_fleet_size_actual' should be null.
If the text mentions "X trucks and Y trailers", only extract X for trucks.
IMPORTANT: Focus solely on the count of *trucks*. If "vehicles" is mentioned, try to confirm they are trucks.""",
       "emission_reporting": "Does the company publish emission reports (e.g., CSRD, TCFD, GRI, SASB) or detailed emissions data (Scopes 1, 2, 3)? (Yes/No reflected in 'criteria_found')",
       "emission_goals": """Does the company have public GHG reduction goals?
If yes, are they SBTi-validated or net-zero by a specific year with interim targets?
(The 'score' for this will be determined later based on this qualitative finding).""",
       "alt_fuels": "Does the company mention the use of alternative fuels like biogas, biodiesel, biomethanol, RNG, hydrogen, or battery-electric vehicles in their operations? (Yes/No reflected in 'criteria_found')",
       "clean_energy_partner": "Does the company mention partnerships, collaborations, or agreements related to clean energy, alternative fuels, or lower-emission technologies? (Yes/No reflected in 'criteria_found')",
       "regulatory": "Does the company discuss specific environmental/sustainability regulations impacting their operations (e.g., IMO, EU ETS) or operate in a clearly high-regulation sector with relevant context provided? (Yes/No reflected in 'criteria_found')"
   }


   instructions = criterion_specific_instructions.get(criterion, "Analyze the context for this criterion.")
  
   full_prompt = f"""
You are an expert sustainability analyst. Given the following context from a company's report, extract information for the criterion: "{criterion.replace('_', ' ').title()}".


Specific Instructions for "{criterion.replace('_', ' ').title()}":
{instructions}


Context:
\"\"\"
{context}
\"\"\"


{base_prompt_fields}


Important general rules:
1. If 'criteria_found' is false, all other values (except justification explaining why it's false) should ideally be null or default (e.g., empty string for quote).
2. For 'cng_fleet_size_actual' and 'total_truck_fleet_size_actual', if no specific number is found, return null for that field. Only return an integer if a number is explicitly stated for the correct item (CNG trucks or total *trucks*).
3. Be very careful with 'total_truck_fleet_size_actual': Do NOT confuse it with ocean fleet capacity (TEU), number of vessels, trailers, or general vehicle counts unless specified as trucks. If "4.3m TEU" is found, 'total_truck_fleet_size_actual' must be null.
"""
   if is_retry:
       full_prompt += "\nThis is a retry. Please re-examine the context carefully.\n"


   try:
       response = client.chat.completions.create(
           model="gpt-4o-mini",
           response_format={"type": "json_object"},
           messages=[{"role": "user", "content": full_prompt}],
           temperature=0.0
       )
       response_content = response.choices[0].message.content
       if response_content:
           clean_response_content = response_content.strip()
           if clean_response_content.startswith("```json"): clean_response_content = clean_response_content[7:]
           if clean_response_content.endswith("```"): clean_response_content = clean_response_content[:-3]
           
           clean_response_content = clean_response_content.strip()
           
           # NEW: Extract just the JSON portion if there's extra content
           json_start = clean_response_content.find('{')
           json_end = clean_response_content.rfind('}')
           
           if json_start != -1 and json_end != -1 and json_end > json_start:
               # Extract just the JSON portion
               json_portion = clean_response_content[json_start:json_end + 1]
               try:
                   parsed_json = json.loads(json_portion)
                   if json_portion != clean_response_content:
                       print(f"[WARN] Extracted JSON from response with extra content. Original length: {len(clean_response_content)}, JSON portion: {len(json_portion)}")
               except json.JSONDecodeError:
                   # If JSON portion fails, try the full cleaned text
                   print(f"[WARN] JSON portion extraction failed, trying full cleaned text")
                   parsed_json = json.loads(clean_response_content)
           else:
               # No clear JSON boundaries found, try parsing as-is
               parsed_json = json.loads(clean_response_content)
           required_keys = ["criteria_found", "quote", "justification", "cng_fleet_size_actual", "total_truck_fleet_size_actual"]
           if not all(k in parsed_json for k in required_keys):
               raise ValueError(f"LLM JSON response missing one or more required keys. Got: {parsed_json.keys()}")
          
           for key_actual in ["cng_fleet_size_actual", "total_truck_fleet_size_actual"]:
               if parsed_json[key_actual] is not None:
                   try:
                       parsed_json[key_actual] = int(parsed_json[key_actual])
                   except (ValueError, TypeError):
                       print(f"[WARN] LLM returned non-integer for {key_actual}: {parsed_json[key_actual]}. Setting to null.")
                       parsed_json[key_actual] = None
           return parsed_json
       else:
           return {
               "criteria_found": False, "score": 0, "quote": "",
               "justification": "OpenAI returned empty content.",
               "cng_fleet_size_actual": None, "total_truck_fleet_size_actual": None
           }
   except json.JSONDecodeError as e_json:
       print(f"[ERROR] JSONDecodeError for '{criterion}': Error: {e_json}")
       print(f"[ERROR] Error occurred at line {getattr(e_json, 'lineno', 'unknown')}, column {getattr(e_json, 'colno', 'unknown')}, position {getattr(e_json, 'pos', 'unknown')}")
       response_content = response.choices[0].message.content
       print(f"[ERROR] Response length: {len(response_content)} characters")
       print(f"[ERROR] Response was: '{response_content[:300]}...'")
       
       # Try to show the problematic area
       if hasattr(e_json, 'pos') and e_json.pos:
           start = max(0, e_json.pos - 50)
           end = min(len(response_content), e_json.pos + 50)
           print(f"[ERROR] Context around error position: '{response_content[start:end]}'")
       
       return {
           "criteria_found": False, "score": 0, "quote": "",
           "justification": f"Invalid JSON from OpenAI: {str(e_json)}",
           "cng_fleet_size_actual": None, "total_truck_fleet_size_actual": None
       }
   except Exception as e_api:
       print(f"[ERROR] OpenAI API call error for '{criterion}': {str(e_api)}")
       return {
           "criteria_found": False, "score": 0, "quote": "",
           "justification": f"OpenAI API error: {str(e_api)}",
           "cng_fleet_size_actual": None, "total_truck_fleet_size_actual": None
       }


def _process_llm_result_into_criterion_finding(llm_data: Dict, criterion: str, original_context: str, full_text:str) -> CriterionFinding:
   """
   Processes the LLM's JSON output, determines the final score, verifies quotes,
   and populates the CriterionFinding object.
   """
   criteria_found = llm_data.get("criteria_found", False)
   quote = llm_data.get("quote", "")
   justification = llm_data.get("justification", "No justification from LLM.")
  
   cng_actual = llm_data.get("cng_fleet_size_actual")
   total_truck_actual = llm_data.get("total_truck_fleet_size_actual")


   final_score = 0
   if criteria_found:
       if criterion == "cng_fleet":
           final_score = 1
       elif criterion == "cng_fleet_size":
           if cng_actual is not None:
               if 1 <= cng_actual <= 10: final_score = 1
               elif 11 <= cng_actual <= 50: final_score = 2
               elif cng_actual >= 51: final_score = 3
               else: final_score = 0
           else: final_score = 0
       elif criterion == "total_truck_fleet_size":
           if total_truck_actual is not None:
                if 1 <= total_truck_actual <= 100: final_score = 1
                elif 101 <= total_truck_actual <= 500: final_score = 2
                elif total_truck_actual > 500: final_score = 3
                else: final_score = 0
           else: final_score = 0
       elif criterion == "emission_reporting":
           final_score = 1
       elif criterion == "emission_goals":
           text_for_goal_score = (quote + " " + justification).lower()
           if ("sbti" in text_for_goal_score or "science based targets" in text_for_goal_score or \
               (("net-zero" in text_for_goal_score or "net zero" in text_for_goal_score) and \
                re.search(r'\b(2030|2035|2040|2045|2050)\b', text_for_goal_score))):
               final_score = 2
           else:
               final_score = 1
       elif criterion == "alt_fuels":
           final_score = 1
       elif criterion == "clean_energy_partner":
           final_score = 1
       elif criterion == "regulatory":
           final_score = 1
   else:
       if criterion == "cng_fleet_size" and cng_actual is not None and cng_actual == 0 :
            criteria_found = True
            final_score = 0
            justification = f"Explicitly found as 0 CNG trucks. LLM: {justification}"


   is_verified = False
   evidence_str = ""
   if criteria_found and quote:
       individual_quotes = [q.strip() for q in quote.split(" | ") if q.strip()]
       verified_quotes_list = []
       for single_q in individual_quotes:
           if verify_quote(original_context, single_q) or verify_quote(full_text, single_q):
               verified_quotes_list.append(single_q)
       if verified_quotes_list:
           is_verified = True
           evidence_str = " | ".join(verified_quotes_list)
           quote = evidence_str
       else:
           evidence_str = ""


   return CriterionFinding(
       criteria_found=criteria_found,
       score=final_score,
       quote=quote,
       justification=justification,
       original_passage=original_context[:1500],
       verified=is_verified,
       evidence=evidence_str,
       cng_fleet_size_actual=cng_actual,
       total_truck_fleet_size_actual=total_truck_actual
   )


def call_llm_for_criterion_analysis(context: str, criterion: str, full_text:str, max_retries: int = 1) -> CriterionFinding:
   MAX_CONTEXT_LEN_FOR_SINGLE_CALL = 100000
  
   if len(context) > MAX_CONTEXT_LEN_FOR_SINGLE_CALL:
       print(f"[INFO] Context for '{criterion}' too large ({len(context)} chars). Truncating.")
       context_to_send = context[:MAX_CONTEXT_LEN_FOR_SINGLE_CALL]
   else:
       context_to_send = context


   for attempt in range(max_retries + 1):
       is_retry = attempt > 0
       llm_json_output = _get_llm_response_for_criterion(context_to_send, criterion, is_retry=is_retry)
       processed_finding = _process_llm_result_into_criterion_finding(llm_json_output, criterion, context_to_send, full_text)
      
       if processed_finding.criteria_found or attempt == max_retries:
           return processed_finding
      
       print(f"[INFO] Attempt {attempt+1} for '{criterion}' did not find criteria. Retrying...")
  
   return CriterionFinding(criteria_found=False, score=0, quote="", justification="Max retries reached, not found.", original_passage=context_to_send[:500])




# --- analyze_criterion_main ---
def analyze_criterion_main(criterion: str, keywords: dict, text_content: str, pages: List[str], file_name: Optional[str] = None) -> CriterionFinding:
   print(f"\n[INFO] Processing criterion: {criterion}")


   all_relevant_snippets = []
   first_original_passage_candidate = ""


   for page_idx, page_content in enumerate(pages):
       if not page_content.strip(): continue
       snippets, passage_candidate = find_relevant_sentences(page_content, keywords, window=3, criterion=criterion)
       if snippets:
           all_relevant_snippets.append(snippets)
           if not first_original_passage_candidate and passage_candidate:
               first_original_passage_candidate = passage_candidate
  
   context_for_llm = "\n\n".join(filter(None, all_relevant_snippets))


   if not context_for_llm.strip():
       logger.debug(f"No keyword-relevant snippets for '{criterion}'. Using first ~10k chars of doc.")
       context_for_llm = text_content[:10000]
       if not first_original_passage_candidate:
           first_original_passage_candidate = text_content[:1000]


   finding_object = call_llm_for_criterion_analysis(context_for_llm, criterion, text_content)
  
   if first_original_passage_candidate and finding_object.quote and verify_quote(first_original_passage_candidate, finding_object.quote):
       finding_object.original_passage = first_original_passage_candidate[:1500]
   else:
       finding_object.original_passage = context_for_llm[:1500]


   if criterion == "total_truck_fleet_size":
       pass


   logger.info(f"[RESULT] Criterion: {criterion}, Found: {finding_object.criteria_found}, Score: {finding_object.score}, "
         f"CNG Actual: {finding_object.cng_fleet_size_actual}, Trucks Actual: {finding_object.total_truck_fleet_size_actual}")
   return finding_object




# --- Summarization Logic ---
SUMMARY_SECTION_CONFIG = {
   "cng_fleet_presence_summary": {
       "title": "CNG Fleet Presence",
       "criteria_keys_for_context": ["cng_fleet"],
       "prompt_template": """
       Based *only* on the following findings for {company_name}, write a 2-3 sentence summary about their Compressed Natural Gas (CNG) fleet *presence*.
       State clearly if the findings indicate they operate CNG vehicles or if no such information was found.
      
       Relevant Findings:
       {findings_context}


       Summary (2-3 concise sentences):
       """
   },
   "cng_fleet_size_summary": {
       "title": "CNG Fleet Size",
       "criteria_keys_for_context": ["cng_fleet_size"],
       "prompt_template": """
       Based *only* on the following findings for {company_name} regarding its CNG fleet size (actual number: {cng_fleet_size_actual_val}), write a 1-2 sentence summary.
       If an actual number was found, state it. If no size was found (actual is None or 0), state that.
      
       Additional Contextual Findings:
       {findings_context}


       Summary (2-3 concise sentences):
       """
   },
   "emission_reporting_summary": {
       "title": "Emission Reporting Practices",
       "criteria_keys_for_context": ["emission_reporting"],
       "prompt_template": """
       Based on the provided findings for {company_name}, summarize their emission reporting practices.
       Specifically, state whether the company explicitly mentions publishing emissions or sustainability reports.


       Findings Context:
       {findings_context}


       Summary (2-3 concise sentences):
       """
   },
   "alternative_fuels_summary": {
       "title": "Alternative Fuels Strategy & Usage",
       "criteria_keys_for_context": ["alt_fuels", "cng_fleet"],
       "prompt_template": """
       Based on the provided findings for {company_name}, describe their strategy and reported usage of alternative fuels.
       Mention any specific alternative fuels they report using (e.g., biogas, biodiesel, RNG, CNG). If no specific alternative fuels are mentioned as being used, state that.


       Findings Context:
       {findings_context}


       Summary (2-3 concise sentences):
       """
   },
   "clean_energy_initiatives_summary": {
       "title": "Clean Energy Initiatives & Partnerships",
       "criteria_keys_for_context": ["clean_energy_partner", "alt_fuels"],
       "prompt_template": """
       Based on the provided findings for {company_name}, outline their clean energy initiatives, particularly focusing on any partnerships or agreements.
       Mention collaborations with RNG/CNG providers, infrastructure companies (e.g., Trillium), engine manufacturers (e.g., Cummins X15N), or use of specific clean fuels. If no such initiatives or partnerships are explicitly mentioned, state that.


       Findings Context:
       {findings_context}


       Summary (2-3 concise sentences):
       """
   },
   "regulatory_pressure_summary": {
       "title": "Regulatory Environment & Pressure",
       "criteria_keys_for_context": ["regulatory"],
       "prompt_template": """
       Based on the provided findings for {company_name}, summarize the regulatory environment or pressures they operate under, particularly concerning their fleet or environmental compliance.
       Mention if they operate in sectors known for high regulatory pressure (e.g., waste, freight, transit) or if specific regulations impacting them are discussed.


       Findings Context:
       {findings_context}


       Summary (2-3 concise sentences):
       """
   },
   "emission_reduction_goals_summary": {
       "title": "Emission Reduction Goals",
       "criteria_keys_for_context": ["emission_goals"],
       "prompt_template": """
       Based on the provided findings for {company_name}, summarize their stated emission reduction goals.
       Specify if they have set public GHG reduction or net-zero targets, and if a timeline is provided. If no specific goals are mentioned, state that.


       Findings Context:
       {findings_context}


       Summary (2-3 concise sentences):
       """
   }
}


def _call_openai_for_summary(prompt_text: str, section_title_log: str, model: str = "gpt-3.5-turbo") -> str:
   try:
       response = client.chat.completions.create(
           model=model,
           messages=[
               {"role": "system", "content": "You are an expert sustainability analyst. Write a concise, factual narrative summary (1-2 sentences) for a company's sustainability profile section. Base your summary *only* on the provided findings. If findings indicate 'not found' or are insufficient, reflect that accurately."},
               {"role": "user", "content": prompt_text}
           ],
           temperature=0.1, max_tokens=150
       )
       return response.choices[0].message.content.strip()
   except Exception as e:
       print(f"[ERROR] OpenAI API call for summary '{section_title_log}' failed: {e}")
       return f"Error generating summary."


def generate_company_section_summaries(
   detailed_criteria_results: Dict[str, Dict],
   company_name_str: str
) -> Dict[str, Dict[str, str]]:
   all_section_summaries_output = {}
   print("\n[INFO] Generating company section summaries...")


   flat_findings = detailed_criteria_results


   executor = None
   try:
       executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(3, len(SUMMARY_SECTION_CONFIG)))
       future_to_summary_id = {}
       
       for summary_id, config in SUMMARY_SECTION_CONFIG.items():
           title = config["title"]
           criteria_keys_for_context = config["criteria_keys_for_context"]
           prompt_template = config["prompt_template"]


           findings_context_str = ""
           cng_actual_val_for_prompt = "N/A"


           for crit_key in criteria_keys_for_context:
               if crit_key in flat_findings:
                   data = flat_findings[crit_key]
                   findings_context_str += f"\nFinding for '{crit_key.replace('_', ' ').title()}':\n"
                   findings_context_str += f"  - Found: {'Yes' if data.get('criteria_found') else 'No'}\n"
                   if data.get('criteria_found'):
                       findings_context_str += f"  - Score (category): {data.get('score')}\n"
                       if crit_key == "cng_fleet_size" and 'cng_fleet_size_actual' in data:
                           cng_actual_val_for_prompt = str(data.get('cng_fleet_size_actual', "N/A"))
                           findings_context_str += f"  - Actual CNG Fleet Size: {cng_actual_val_for_prompt}\n"
                       if crit_key == "total_truck_fleet_size" and 'total_truck_fleet_size_actual' in data:
                            findings_context_str += f"  - Actual Total Truck Fleet Size: {data.get('total_truck_fleet_size_actual', 'N/A')}\n"
                       if data.get('evidence'):
                           findings_context_str += f"  - Evidence: \"{data.get('evidence')}\"\n"
                       elif data.get('quote'):
                            findings_context_str += f"  - Quote: \"{data.get('quote')}\"\n"
                       findings_context_str += f"  - Justification: {data.get('justification')}\n"
               else:
                   findings_context_str += f"\nFinding for '{crit_key.replace('_', ' ').title()}': Not analyzed or result missing.\n"
          
           final_summary_prompt = prompt_template.format(
               company_name=company_name_str,
               findings_context=findings_context_str,
               cng_fleet_size_actual_val=cng_actual_val_for_prompt
           )
          
           future_to_summary_id[executor.submit(_call_openai_for_summary, final_summary_prompt, title)] = (summary_id, title)

       # Process results with timeout
       try:
           for future in tqdm(concurrent.futures.as_completed(future_to_summary_id, timeout=300), total=len(future_to_summary_id), desc="Generating Summaries"):
               summary_id, title = future_to_summary_id[future]
               try:
                   summary_text = future.result(timeout=60)  # 60 second timeout per summary
                   all_section_summaries_output[summary_id] = {"title": title, "summary_text": summary_text}
               except concurrent.futures.TimeoutError:
                   print(f"[ERROR] Summary generation timed out for {title}")
                   all_section_summaries_output[summary_id] = {"title": title, "summary_text": "Generation timed out."}
                   future.cancel()  # Cancel the timed out future
               except Exception as e_summary_thread:
                   print(f"[ERROR] Error generating summary for {title}: {e_summary_thread}")
                   all_section_summaries_output[summary_id] = {"title": title, "summary_text": "Failed to generate."}
       except concurrent.futures.TimeoutError:
           print("[ERROR] Overall summary generation timed out")
           # Cancel all remaining futures
           for future in future_to_summary_id.keys():
               if not future.done():
                   future.cancel()
                   
   finally:
       # Ensure proper cleanup of thread pool
       if executor:
           try:
               # Cancel any remaining futures
               for future in future_to_summary_id.keys():
                   if not future.done():
                       future.cancel()
               
               # Shutdown thread pool with timeout
               executor.shutdown(wait=True)
               print("[INFO] Summary generation thread pool shut down successfully")
           except Exception as cleanup_error:
               print(f"[WARNING] Error during thread pool cleanup: {cleanup_error}")
               # Force shutdown if graceful shutdown fails
               try:
                   executor.shutdown(wait=False)
               except Exception:
                   pass
   return all_section_summaries_output




# --- Main Orchestrator (MODIFIED) ---
def analyze_scorecard_and_extract_values(
   text_path: str,
   company_name: str,
   out_dir: Optional[str] = None,
   source_info: Optional[Dict] = None,
   selected_criteria_list: Optional[List[str]] = None
):
   print(f"\n--- Starting Full Scorecard Analysis for: {company_name} ---")
   try:
       with open(text_path, "r", encoding="utf-8") as f: text_content = f.read()
   except FileNotFoundError: print(f"[ERROR] Text file not found: {text_path}"); return None
   if not text_content.strip(): print(f"[ERROR] Text file {text_path} is empty."); return None
      
   pages_from_text = split_text_by_page(text_content)
   if not pages_from_text and text_content.strip(): pages_from_text = [text_content]
   elif not pages_from_text: print(f"[ERROR] No pages derived from {text_path}."); return None


   detailed_criteria_output_for_json = {}
   file_basename = os.path.basename(text_path)
  
   # MODIFIED: Determine which criteria to process based on selection or scorecard weights
   scorecard_criteria = list(calculate_cng_adoption_score.__defaults__[0] if calculate_cng_adoption_score.__defaults__ else {}) # Hack to get default dict keys
   scorecard_criteria = ["cng_fleet", "cng_fleet_size", "emission_reporting", "emission_goals", "alt_fuels", "clean_energy_partner", "regulatory"]

   if selected_criteria_list:
       criteria_to_process_keys = selected_criteria_list
   else:
       # Default to all criteria needed for the score + other important ones
       criteria_to_process_keys = list(CRITERIA_KEYWORDS.keys())
   
   criteria_to_process_map = {
       k: v for k, v in CRITERIA_KEYWORDS.items() if k in criteria_to_process_keys
   }


   print(f"\nStep 1: Analyzing {len(criteria_to_process_map)} detailed criteria for findings and numerical values...")
   
   criteria_executor = None
   try:
       criteria_executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(3, len(criteria_to_process_map)))
       future_to_criterion = {
           criteria_executor.submit(analyze_criterion_main, crit_key, kw_conf, text_content, pages_from_text, file_basename): crit_key
           for crit_key, kw_conf in criteria_to_process_map.items()
       }
       
       try:
           for future in tqdm(concurrent.futures.as_completed(future_to_criterion, timeout=600),
                                  total=len(future_to_criterion),
                                  desc="Analyzing criteria"):
               criterion_key = future_to_criterion[future]
               try:
                   result_finding_obj = future.result(timeout=120)  # 2 minute timeout per criterion
                  
                   criterion_data_for_json = {
                       "criteria_found": result_finding_obj.criteria_found,
                       "score": result_finding_obj.score,
                       "quote": result_finding_obj.quote,
                       "justification": result_finding_obj.justification,
                       "original_passage": result_finding_obj.original_passage,
                       "verified": result_finding_obj.verified,
                       "evidence": result_finding_obj.evidence,
                   }
                   if result_finding_obj.cng_fleet_size_actual is not None:
                       criterion_data_for_json["cng_fleet_size_actual"] = result_finding_obj.cng_fleet_size_actual
                   if result_finding_obj.total_truck_fleet_size_actual is not None:
                        criterion_data_for_json["total_truck_fleet_size_actual"] = result_finding_obj.total_truck_fleet_size_actual
                  
                   detailed_criteria_output_for_json[criterion_key] = criterion_data_for_json

               except concurrent.futures.TimeoutError:
                   print(f"[ERROR] Criterion analysis timed out for {criterion_key}")
                   detailed_criteria_output_for_json[criterion_key] = {
                       "criteria_found": False, "score": 0, "quote": "",
                       "justification": "Analysis timed out",
                       "original_passage": "", "verified": False, "evidence": ""
                   }
                   future.cancel()  # Cancel the timed out future
               except Exception as e_thread:
                   print(f"[ERROR] Error processing criterion {criterion_key} in thread: {str(e_thread)}")
                   detailed_criteria_output_for_json[criterion_key] = {
                       "criteria_found": False, "score": 0, "quote": "",
                       "justification": f"Error during analysis: {str(e_thread)}",
                       "original_passage": "", "verified": False, "evidence": ""
                   }
       except concurrent.futures.TimeoutError:
           print("[ERROR] Overall criteria analysis timed out")
           # Cancel all remaining futures
           for future in future_to_criterion.keys():
               if not future.done():
                   future.cancel()
                   
   finally:
       # Ensure proper cleanup of criteria thread pool
       if criteria_executor:
           try:
               # Cancel any remaining futures
               for future in future_to_criterion.keys():
                   if not future.done():
                       future.cancel()
               
               # Shutdown thread pool with timeout
               criteria_executor.shutdown(wait=True)
               print("[INFO] Criteria analysis thread pool shut down successfully")
           except Exception as cleanup_error:
               print(f"[WARNING] Error during criteria thread pool cleanup: {cleanup_error}")
               # Force shutdown if graceful shutdown fails
               try:
                   criteria_executor.shutdown(wait=False)
               except Exception:
                   pass
   print("Detailed criteria analysis and numerical extraction complete.")

   # --- NEW: Calculate the CNG Adoption Score ---
   cng_adoption_score = calculate_cng_adoption_score(detailed_criteria_output_for_json)


   company_summaries_output = generate_company_section_summaries(
       detailed_criteria_results=detailed_criteria_output_for_json,
       company_name_str=company_name
   )


   sustainability_metrics_payload = {}
   print("\nGenerating SustainabilityMetrics payload...")
   for db_metric_name, mapping_info in DB_METRICS_MAPPING.items():
       criterion_key_in_script = mapping_info["criterion_key"]
       # Skip the composite score here; it will be added manually
       if criterion_key_in_script == "COMPOSITE_SCORE":
           continue

       value_source_key = mapping_info["value_source"]
       default_value = mapping_info["default"]
       metric_value = default_value


       if criterion_key_in_script in detailed_criteria_output_for_json:
           criterion_data = detailed_criteria_output_for_json[criterion_key_in_script]
           if value_source_key == "criteria_found":
               metric_value = criterion_data.get("criteria_found", default_value)
           else:
               if criterion_data.get("criteria_found") or value_source_key in ["cng_fleet_size_actual", "total_truck_fleet_size_actual"]:
                   raw_value = criterion_data.get(value_source_key)
                   if raw_value is not None:
                       metric_value = raw_value
                   elif value_source_key in ["cng_fleet_size_actual", "total_truck_fleet_size_actual"] and raw_value is None:
                        metric_value = default_value
       sustainability_metrics_payload[db_metric_name] = metric_value

   # --- NEW: Manually add the calculated adoption score to the payload ---
   sustainability_metrics_payload['cng_adopt_score'] = cng_adoption_score

   metric_sources_payload = []
   print("\nGenerating MetricSources payload...")
   doc_url = "UNKNOWN_SOURCE_URL"
   if source_info:
       doc_url = source_info.get("url", source_info.get("source_url", source_info.get("link", "UNKNOWN_SOURCE_URL")))


   for db_metric_name, mapping_info in DB_METRICS_MAPPING.items():
       criterion_key_in_script = mapping_info["criterion_key"]
       if criterion_key_in_script in detailed_criteria_output_for_json:
           criterion_data = detailed_criteria_output_for_json[criterion_key_in_script]
           if criterion_data.get("criteria_found", False):
               contribution_text = criterion_data.get("evidence", "").strip()
               if not contribution_text:
                   contribution_text = criterion_data.get("quote", "").strip()
              
               if contribution_text:
                   metric_sources_payload.append({
                       "metric_name": db_metric_name,
                       "source_url": doc_url,
                       "contribution_text": contribution_text
                   })
   print("Payload generation for DB complete.")


   final_json_payload = {
       "company_name": company_name,
       "sustainability_metrics_payload": sustainability_metrics_payload,
       "metric_sources_payload": metric_sources_payload,            
       "detailed_criteria_findings": detailed_criteria_output_for_json,
       "company_section_summaries": company_summaries_output
   }
   if source_info:
       final_json_payload["source_document_info"] = source_info


   if not out_dir:
       safe_co_name = safe_filename_for_output_path(company_name)
       base_out_dir = os.path.join("data", "final_scorecards_numerical")
       os.makedirs(base_out_dir, exist_ok=True)
       out_dir_company = os.path.join(base_out_dir, safe_co_name)
       os.makedirs(out_dir_company, exist_ok=True)
       out_dir = out_dir_company
   else:
       os.makedirs(out_dir, exist_ok=True)
  
   output_filename = f"{safe_filename_for_output_path(company_name)}_scorecard_numerical.json"
   out_path_final = os.path.join(out_dir, output_filename)
  
   try:
       with open(out_path_final, "w", encoding="utf-8") as f_out:
           json.dump(final_json_payload, f_out, indent=2, ensure_ascii=False)
       print(f"\n[SUCCESS] Full scorecard with numerical values and DB payloads saved to: {out_path_final}")
   except Exception as e_save:
       print(f"[ERROR] Failed to save final JSON output: {e_save}")
       return None
   return out_path_final





# --- Main execution ---
if __name__ == "__main__":
   parser = argparse.ArgumentParser(description="Analyze sustainability text, extract numerical values, generate scorecard JSON.")
   parser.add_argument("text_path", type=str, help="Path to the input text file.")
   parser.add_argument("company_name", type=str, help="Name of the company.")
   parser.add_argument("--out_dir", type=str, default=None, help="Output directory.")
   parser.add_argument("--criteria", type=str, default=None, help="Comma-separated criteria keys (e.g., cng_fleet,total_truck_fleet_size). Default: all.")
   parser.add_argument("--source_info_json", type=str, default=None, help='Optional: JSON string for source doc info. E.g., \'{"url": "...", "title": "..."}\'')
  
   args = parser.parse_args()
   selected_criteria = [c.strip() for c in args.criteria.split(',')] if args.criteria else None
   doc_source_info = None
   if args.source_info_json:
       try:
           doc_source_info = json.loads(args.source_info_json)
       except json.JSONDecodeError as e:
           print(f"[WARN] Invalid JSON string for --source_info_json: {e}. Proceeding without source info.")




   analyze_scorecard_and_extract_values(
       text_path=args.text_path,
       company_name=args.company_name,
       out_dir=args.out_dir,
       source_info=doc_source_info,
       selected_criteria_list=selected_criteria
   )