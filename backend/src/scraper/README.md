# AI-Powered Sustainability Data Scraper

## What This System Does

This is an intelligent web scraping system that **automatically analyzes companies for sustainability practices**. It searches the internet, reads PDF reports, and uses AI to extract specific sustainability metrics, then exports the results in a database-ready format.

**Input**: Company name (e.g. "Amazon", "UPS", "FedEx")  
**Output**: Structured JSON with 8 sustainability metrics ready for database storage

## Quick Start

### 🚀 Option 1: Using the Scraper Service (Recommended for Integration)

```python
from backend.src.scraper.scraper_service import analyze_company_structured

# Analyze a company and get structured results with overall score
results = analyze_company_structured("Amazon")

# Access the results
company_info = results["company"]
metrics = results["sustainability_metrics"] 
sources = results["metric_sources"]
summaries = results["summaries"]
overall_score = results["overall_score"]

# Overall sustainability score (0-100%)
score_percentage = overall_score["overall_score_percentage"]  # e.g., 73.5
criteria_breakdown = overall_score["criteria_breakdown"]      # Detailed breakdown

print(f"Overall Sustainability Score: {score_percentage}%")
```

### 🖥️ Option 2: Using the CLI Interface

```bash
# Basic analysis
python -m backend.src.scraper.main_ai_scraper "Amazon"

# Results saved to: amazon_sustainability_results.json
```

### 🔧 Option 3: Using from FastAPI Routes

```python
# In FastAPI routes
from backend.src.scraper.scraper_service import analyze_company_structured

structured_results = await run_async_wrapper(
    analyze_company_structured,
    company_name=company_name,
    verbose=False
)
```

## What It Analyzes (The 8 Criteria)

1. **Total Truck Fleet Size** - How many trucks/vehicles does the company operate?
2. **CNG Fleet Presence** - Does the company use compressed natural gas vehicles?
3. **CNG Fleet Size** - How many CNG vehicles do they have?
4. **Emission Reporting** - Do they publish sustainability/environmental reports?
5. **Emission Goals** - Do they have carbon reduction targets (like net-zero by 2040)?
6. **Alternative Fuels** - Do they use biodiesel, renewable fuels, sustainable aviation fuel?
7. **Clean Energy Partners** - Do they partner with external clean energy providers?
8. **Regulatory Compliance** - Are they subject to trucking/freight regulations?

## How It Works (3-Phase Analysis)

### Phase 1: PDF Analysis (Highest Quality)

- Searches for official company sustainability reports
- Downloads and analyzes PDFs using AI
- Extracts direct evidence from company documents

### Phase 2: Search Analysis

- Performs targeted Google searches for missing criteria
- Analyzes search result snippets with AI
- Validates sources to prevent false information

### Phase 3: Web Scraping (Final Fallback)

- Scrapes relevant web pages for remaining missing data
- Applies final AI analysis to web content
- Ensures comprehensive coverage

## 🔄 Migration Guide: CLI → Service Layer

### Before (CLI Method):
```python
# Old way - using CLI or main_ai_scraper directly
import subprocess
result = subprocess.run([
    "python", "-m", "backend.src.scraper.main_ai_scraper", "Amazon"
], capture_output=True, text=True)

# Parse JSON file manually
import json
with open("amazon_sustainability_results.json") as f:
    data = json.load(f)
```

### After (Service Layer Method):
```python
# New way - using scraper service
from backend.src.scraper.scraper_service import analyze_company_structured

# One line to get everything including overall score
results = analyze_company_structured("Amazon")

# Data is ready to use immediately
overall_score = results["overall_score"]["overall_score_percentage"]
```

### Benefits of Migration:
- ✅ **No file I/O** - Results returned directly in memory
- ✅ **Built-in scoring** - Overall score calculated automatically  
- ✅ **Better error handling** - Proper exceptions instead of subprocess errors
- ✅ **Cleaner code** - One function call instead of subprocess + file parsing
- ✅ **Type safety** - Direct Python objects instead of parsed JSON strings

## 🆕 NEW: Scraper Service & Overall Scoring System

### 🎯 ScraperService Class

The `scraper_service.py` module provides a **clean, service-layer interface** to the AI scraper with built-in overall scoring calculation.

#### Key Features:
- **Structured JSON output** matching CLI format
- **Weighted overall sustainability score** (0-100%)
- **Detailed criteria breakdown** with individual contributions
- **Environment validation** for API keys
- **Service layer architecture** for better code organization

#### How the Overall Score Works:

The system calculates a **weighted percentage score** based on 7 sustainability criteria:

| Criterion | Weight | Max Score | Description |
|-----------|--------|-----------|-------------|
| CNG Fleet Presence | 10% | 1 | Does company operate CNG vehicles? |
| CNG Fleet Size | 25% | 3 | Size range: 0=None, 1=1-10, 2=11-50, 3=51+ |
| Emission Reporting | 10% | 1 | Do they publish sustainability reports? |
| Emission Reduction Goals | 15% | 2 | 0=No, 1=Goals mentioned, 2=Timeline/SBTi |
| Alternative Fuels Mentioned | 15% | 1 | Use of biodiesel, RNG, sustainable fuels? |
| Clean Energy Partnerships | 15% | 1 | Partnerships with clean energy providers? |
| Regulatory Pressure | 10% | 1 | Operating in regulated sectors? |

#### Score Calculation Formula:
```
Overall Score = Sum of (Normalized Score × Weight) / Sum of All Weights × 100

Where Normalized Score = (Raw Score / Max Possible Score) × 100
```

#### Example Overall Score Response:
```json
{
  "overall_score": {
    "overall_score_percentage": 73.5,
    "total_weighted_score": 73.5,
    "total_possible_score": 100.0,
    "criteria_breakdown": {
      "cng_fleet": {
        "name": "CNG Fleet Presence",
        "raw_score": 1,
        "max_score": 1,
        "normalized_score": 100.0,
        "weight_percentage": 10,
        "weighted_contribution": 10.0,
        "possible_contribution": 10
      },
      "cng_fleet_size": {
        "name": "CNG Fleet Size",
        "raw_score": 2,
        "max_score": 3,
        "normalized_score": 66.7,
        "weight_percentage": 25,
        "weighted_contribution": 16.7,
        "possible_contribution": 25
      }
      // ... other criteria
    },
    "score_calculation": {
      "description": "Overall score calculated as weighted average of all criteria",
      "formula": "Sum of (normalized_score * weight) / Sum of all weights * 100",
      "total_criteria_evaluated": 7
    }
  }
}
```

#### Using the ScraperService Class:

```python
from backend.src.scraper.scraper_service import ScraperService

# Initialize service (validates environment variables)
service = ScraperService()

# Analyze company with custom parameters
results = service.analyze_company(
    company_name="FedEx",
    criteria=None,  # Analyze all criteria (optional: provide specific set)
    max_search_pages=2,
    max_pdf_reports=3,
    max_web_pages=3,
    verbose=True,
    use_crawler=False
)

# Access overall score
overall_score = results["overall_score"]["overall_score_percentage"]
print(f"FedEx Sustainability Score: {overall_score}%")

# Get detailed breakdown
for criterion, details in results["overall_score"]["criteria_breakdown"].items():
    print(f"{details['name']}: {details['normalized_score']}% (Weight: {details['weight_percentage']}%)")
```

## Directory Structure & File Purposes

```
📁 backend/src/scraper/
├── 🎯 main_ai_scraper.py          # MAIN ENTRY POINT - orchestrates everything
├── 🆕 scraper_service.py          # SERVICE LAYER - clean interface with overall scoring
├── 🧠 ai_criteria_analyzer.py     # AI BRAIN - analyzes text for evidence
├── 📊 ai_scorecard_integration.py # SCORING SYSTEM - validates and scores evidence
├── 📋 analyze_scorecard.py        # LEGACY SCORING - criteria mapping and ranges
├── 📄 pdf_parser.py              # PDF READER - extracts text from PDF documents
├── 📄 extract_pdf.py             # PDF HELPER - basic PDF extraction utilities
├── 📁 utils/                     # UTILITY FUNCTIONS
│   ├── pdf.py                   # PDF processing and chunking
│   ├── html.py                  # HTML cleaning and text extraction
│   └── strings.py               # Text normalization utilities
├── 📁 crawler/                   # WEB CRAWLING
│   └── fetch.py                 # URL filtering and content retrieval
├── 📁 analysis/                  # ANALYSIS HELPERS
│   └── company.py               # Company-specific validation
├── 📁 scorecard/                 # EVIDENCE VALIDATION
│   └── validation.py            # Evidence quality checks
├── 📁 export/                    # DATA OUTPUT
│   └── json_exporter.py         # Database-ready JSON generation
├── 📁 config/                    # CONFIGURATION FILES
│   ├── pdf_patterns.yaml       # PDF URL scoring patterns
│   ├── trusted_domains.yaml    # Whitelisted domains
│   └── number_ranges.yaml      # Scoring ranges
└── 📁 logs/                      # LOG FILES (auto-generated)
```

## File-by-File Detailed Explanation

### 🎯 `main_ai_scraper.py` - The Orchestrator (START HERE)

**Purpose**: Main entry point that coordinates the entire analysis process
**What it does**:

- Takes a company name and runs the 3-phase analysis
- Coordinates PDF analysis, search analysis, and web scraping
- Formats results into tables and exports JSON
- Provides command-line interface

**Key functions you'll use**:

- `analyze_company_sustainability(company_name)` - Main analysis function
- `main()` - Command-line interface entry point

**When to modify**:

- Adding new analysis phases
- Changing the overall flow
- Modifying command-line options
- Adjusting how results are displayed

### 🆕 `scraper_service.py` - The Service Layer (RECOMMENDED FOR INTEGRATION)

**Purpose**: Clean, modern interface to the scraper with built-in overall scoring
**What it does**:

- Provides `ScraperService` class for object-oriented usage
- Validates environment variables (API keys) on initialization
- Calculates weighted overall sustainability scores automatically
- Returns structured JSON format identical to CLI but with added scoring
- Handles async/sync integration for FastAPI routes

**Key functions you'll use**:

- `analyze_company_structured(company_name)` - Convenience function (recommended)
- `ScraperService.analyze_company()` - Object-oriented interface
- `ScraperService.calculate_overall_score()` - Scoring calculation
- `ScraperService.get_supported_criteria()` - List available criteria

**Key features**:

- **Environment validation**: Checks for required API keys on startup
- **Weighted scoring**: Automatic overall score calculation (0-100%)
- **Criteria breakdown**: Detailed contribution analysis per criterion
- **Service pattern**: Clean separation of concerns for better architecture
- **Async support**: Works seamlessly with FastAPI async routes

**When to use**:

- ✅ **Integrating with FastAPI routes** (recommended)
- ✅ **Building applications** that need structured data
- ✅ **When you need overall scores** and detailed breakdowns
- ✅ **Production environments** requiring proper error handling

**When to modify**:

- Adding new scoring criteria or changing weights
- Modifying overall score calculation logic
- Adding new service-level features
- Changing JSON output structure

### 🧠 `ai_criteria_analyzer.py` - The AI Brain

**Purpose**: Communicates with OpenAI GPT-4 to analyze text for sustainability evidence
**What it does**:

- Sends text chunks to OpenAI with specific prompts for each criterion
- Processes AI responses and extracts evidence
- Validates that quoted evidence actually exists in the source text
- Optimizes API calls by analyzing multiple criteria at once

**Key functions**:

- `analyze_text_with_ai_batched()` - Main function to analyze text for evidence
- `call_openai_multi_criteria()` - Efficient batched API calls to OpenAI
- `verify_quote_flexible()` - Verify evidence quotes exist in source

**When to modify**:

- Changing AI prompts or instructions
- Adding new sustainability criteria
- Modifying evidence validation rules
- Adjusting AI model parameters

### 📊 `ai_scorecard_integration.py` - The Scoring System

**Purpose**: Advanced evidence validation, scoring, and quality assessment
**What it does**:

- Validates evidence quality using sophisticated rules
- Decides when new evidence should replace existing evidence
- Converts modern evidence format to legacy format for compatibility
- Applies scoring rubrics and normalization

**Key functions**:

- `should_replace_evidence()` - Decide if new evidence is better
- `convert_scorecard_results_to_legacy_format()` - Format conversion
- Evidence quality validation functions

**When to modify**:

- Changing how evidence quality is assessed
- Modifying scoring algorithms
- Adding new evidence replacement rules

### 📋 `analyze_scorecard.py` - Legacy Scoring System

**Purpose**: Contains legacy scoring logic and criteria mapping (kept for compatibility)
**What it does**:

- Maps criteria to database fields
- Defines score ranges for each criterion
- Contains original scoring logic (now mostly replaced by AI system)

**When to modify**:

- Adding new criteria to database mapping
- Changing score ranges
- Updating legacy compatibility functions

### 📄 `pdf_parser.py` & `extract_pdf.py` - PDF Processing

**Purpose**: Extract text content from PDF documents
**What they do**:

- Download PDFs from URLs
- Extract readable text from PDF files
- Handle progress tracking for large documents
- Error handling for corrupted or inaccessible PDFs

**When to modify**:

- Improving PDF text extraction quality
- Adding support for new PDF formats
- Changing how large PDFs are processed

### 🛠️ `utils/` Directory - Helper Functions

#### `utils/pdf.py` - Advanced PDF Processing

**Purpose**: Advanced PDF processing and intelligent text chunking
**Key functions**:

- `extract_pdf_content()` - Download and extract PDF text with validation
- `intelligent_chunk_text()` - Split large text into manageable pieces for AI

#### `utils/html.py` - HTML Processing

**Purpose**: Clean HTML content and extract readable text
**Key functions**:

- `html_to_clean_text()` - Remove HTML tags and extract clean text

#### `utils/strings.py` - Text Processing

**Purpose**: Text normalization and filename utilities
**Key functions**:

- `normalize_text()` - Standardize text format
- `safe_filename_for_output_path()` - Generate safe filenames

### 🕷️ `crawler/fetch.py` - Web Crawling Logic

**Purpose**: Decide which URLs to crawl and how to retrieve content
**What it does**:

- Filters URLs based on relevance to sustainability criteria
- Validates domain trustworthiness
- Safely retrieves web page content
- Prevents crawling of irrelevant or harmful sites

**Key functions**:

- `should_crawl()` - Decide if a URL is worth crawling
- `safe_get_page_content()` - Safely get web page content
- `is_trusted_domain_ai()` - Check if domain is trustworthy

### 🔍 `analysis/company.py` - Company-Specific Logic

**Purpose**: Company-specific validation and analysis adjustments
**What it does**:

- Validates that PDFs actually belong to the target company
- Adjusts analysis depth based on company size and progress
- Prevents false evidence from third-party sources

**Key functions**:

- `validate_pdf_ownership()` - Ensure PDFs belong to target company
- `get_dynamic_page_limit()` - Adjust analysis depth dynamically

### ✅ `scorecard/validation.py` - Evidence Quality Control

**Purpose**: Validate evidence quality and manage evidence data structures
**What it does**:

- Defines the `CriteriaEvidence` class that stores evidence data
- Validates evidence quality
- Manages evidence metadata

### 📤 `export/json_exporter.py` - Database Export

**Purpose**: Convert analysis results into database-ready JSON format
**What it does**:

- Takes raw evidence and converts to structured database format
- Applies business logic corrections (e.g., "if you have fleet size, you have a fleet")
- Creates audit trails linking evidence to sources
- Generates human-readable summaries

**Key features**:

- Automatic corrections for logical consistency
- Database-compatible field mapping
- Source aggregation for audit trails

### ⚙️ `config/` Directory - Configuration Files

- **`pdf_patterns.yaml`** - Patterns for scoring PDF URLs by relevance
- **`trusted_domains.yaml`** - List of domains considered trustworthy sources
- **`number_ranges.yaml`** - Scoring ranges for numeric criteria

## Data Flow Walkthrough

```
1. User runs: python -m backend.src.scraper.main_ai_scraper "Amazon"
         ↓
2. main_ai_scraper.py starts 3-phase analysis
         ↓
3. PHASE 1: PDF Analysis
   - Search Google for "Amazon sustainability report filetype:pdf"
   - utils/pdf.py downloads and extracts PDF text
   - ai_criteria_analyzer.py analyzes text with OpenAI
   - Find evidence like "Amazon operates 4,400 CNG vehicles"
         ↓
4. PHASE 2: Search Analysis (for missing criteria)
   - Search Google for specific missing criteria
   - ai_criteria_analyzer.py analyzes search snippets
   - Validate sources using crawler/fetch.py
         ↓
5. PHASE 3: Web Scraping (final fallback)
   - crawler/fetch.py selects relevant URLs
   - utils/html.py extracts clean text from web pages
   - ai_criteria_analyzer.py does final analysis
         ↓
6. Results Processing
   - ai_scorecard_integration.py validates and scores all evidence
   - export/json_exporter.py converts to database format
   - main_ai_scraper.py saves JSON file and displays results
```

## Example Output Explained

```json
{
  "company": {
    "company_name": "Amazon", // The company analyzed
    "company_summary": "Amazon operates...", // AI-generated summary
    "website_url": "", // Company website (if found)
    "industry": "", // Industry classification
    "cso_linkedin_url": "" // CSO LinkedIn (if found)
  },
  "sustainability_metrics": {
    "owns_cng_fleet": true, // Boolean: Does company have CNG vehicles?
    "cng_fleet_size_range": 3, // Range 0-3: Size category of CNG fleet
    "cng_fleet_size_actual": 4400, // Exact number: Actual CNG fleet size
    "total_fleet_size": null, // Total vehicle count (if found)
    "emission_report": true, // Boolean: Publishes emissions reports?
    "emission_goals": 2, // Range 0-2: Quality of emission goals
    "alt_fuels": true, // Boolean: Uses alternative fuels?
    "clean_energy_partners": true, // Boolean: Has clean energy partnerships?
    "regulatory_pressure": true // Boolean: Subject to regulations?
  },
  "metric_sources": [
    // Audit trail of all evidence
    {
      "metric_name": ["cng_fleet_size"], // Which criteria this evidence supports
      "source_url": "https://...", // Where evidence was found
      "contribution_text": "Amazon operates..." // Exact quote that supports the criteria
    }
  ],
  "summaries": {
    // Human-readable summaries
    "fleet_summary": {
      "summary_text": "The company operates a CNG fleet of 4400 vehicles."
    }
    // ... other summaries
  }
}
```

## Configuration and Setup

### Required Environment Variables

```bash
export OPENAI_API_KEY="sk-your-openai-api-key"
export SERPER_API_KEY="your-google-search-api-key"
```

### Installation

```bash
pip install -r requirements.txt
playwright install  # For web scraping
```

## Common Use Cases & Examples

### 1. Basic Analysis

```bash
python -m backend.src.scraper.main_ai_scraper "UPS"
```

Analyzes UPS across all 8 criteria, saves to `ups_sustainability_results.json`

### 2. Analyze Specific Criteria Only

```bash
python -m backend.src.scraper.main_ai_scraper "FedEx" --criteria cng_fleet emission_goals
```

Only looks for CNG fleet info and emission goals for FedEx

### 3. Adjust Analysis Depth

```bash
python -m backend.src.scraper.main_ai_scraper "DHL" --max-pdf-reports 5 --max-web-pages 3
```

Analyze more PDFs and web pages for thorough analysis

### 4. Programmatic Usage

```python
from backend.src.scraper.main_ai_scraper import analyze_company_sustainability

# Analyze a company programmatically
results = analyze_company_sustainability(
    company_name="Target Corporation",
    criteria={'cng_fleet', 'emission_goals', 'alt_fuels'},
    max_pdf_reports=3,
    verbose=True
)

# Access the results
evidence_found = results['evidence_found']
json_export = results['json_export']
```

## Performance Characteristics

### Typical Runtime

- **Small company**: 2-3 minutes, usually finds 6-8/8 criteria
- **Large company with good sustainability reporting**: 1-2 minutes, finds 7-8/8 criteria
- **Company with limited sustainability info**: 3-5 minutes, finds 4-6/8 criteria

### Built-in Optimizations

- **Batched AI Analysis**: Analyzes multiple criteria per OpenAI API call (70% fewer API calls)
- **Keyword Pre-filtering**: Skips irrelevant content before expensive AI analysis (80% processing reduction)
- **Smart Source Prioritization**: Official company PDFs analyzed first for highest quality evidence
- **Early Exit**: Stops analysis when all criteria are found
- **Dynamic Limits**: Adjusts scraping depth based on how many criteria are still missing

## Troubleshooting Common Issues

### "API Key Error"

- Make sure OpenAI and Serper API keys are set as environment variables
- Check that keys are valid and have sufficient credits

### "No Results Found"

- Some companies may not have much sustainability information online
- Try reducing the number of criteria with `--criteria flag`
- Check if the company name is spelled correctly

### "Timeout Errors"

- Reduce analysis depth: `--max-pdf-reports 2 --max-web-pages 1`
- Some PDFs may be very large or inaccessible

### Import Errors

- Always run from the project root directory
- Make sure all dependencies are installed: `pip install -r requirements.txt`

### Debug Mode

```bash
python -m backend.src.scraper.main_ai_scraper "Company" --verbose
```

Shows detailed progress and helps identify where issues occur

## Customization & Development

### Adding a New Sustainability Criterion

1. **Add to main criteria list**: Add to `ALL_CRITERIA` set in `main_ai_scraper.py`
2. **Define AI analysis**: Add criterion description and scoring rules in `ai_criteria_analyzer.py`
3. **Database mapping**: Add field mapping in `analyze_scorecard.py`
4. **JSON export**: Update export logic in `export/json_exporter.py`

### Modifying AI Behavior

- **Change prompts**: Edit the criterion descriptions in `ai_criteria_analyzer.py`
- **Adjust scoring**: Modify scoring thresholds in AI prompts
- **Update validation**: Change evidence validation rules in `scorecard/validation.py`

### Adding New Data Sources

- **New extraction methods**: Add to appropriate utility module (`utils/`, `crawler/`)
- **URL patterns**: Update configuration files in `config/`
- **Source prioritization**: Modify scoring logic to prioritize new sources

## Data Quality & Security

### Data Quality Controls

- **Source Validation**: Only accepts evidence from trusted domains and company-owned documents
- **Quote Verification**: All evidence quotes are verified to actually exist in the source text
- **Bias Detection**: Automatically filters out product pages, marketing content, and irrelevant sources
- **Recency Preference**: Prefers recent sources over outdated information

### Security Features

- **No Permanent Storage**: Company data is not stored permanently anywhere
- **API Rate Limiting**: Respects OpenAI and Google Search API rate limits
- **Error Isolation**: Failures in one component don't crash the entire system
- **Safe Crawling**: Only crawls trusted domains and validates content

## System Architecture Philosophy

This system is designed with these principles:

- **Reliability**: Graceful error handling, never crashes on bad data
- **Efficiency**: Smart optimizations reduce API costs and runtime
- **Accuracy**: Multiple validation layers ensure high-quality results
- **Maintainability**: Clear separation of concerns, well-documented interfaces
- **Scalability**: Easy to add new criteria, data sources, or analysis methods

The modular design means you can modify individual components (like adding a new PDF extraction method) without affecting the rest of the system.
