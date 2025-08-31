# Simple Test Runner for AI Sustainability Scraper

## Overview

The `simple_test.py` file is a **quick testing utility** that allows you to run the AI-powered sustainability scraper with a single command. It's designed to test the complete pipeline and verify that all components are working correctly.

## What It Does

This test runner:
- ✅ Tests the complete `analyze_company_sustainability` function
- ✅ Validates the new comprehensive output structure
- ✅ Shows detailed results in a readable format
- ✅ Helps debug any issues with the scraper pipeline
- ✅ Serves as a quick way to test changes to the scraper

## Quick Start

### Prerequisites

1. **Install Dependencies**
   ```bash
   # From project root
   pip install -r backend/src/scraper/requirements.txt
   ```

2. **Set Environment Variables**
   Create a `.env` file in the project root with:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_CSE_API_KEY=your_google_cse_api_key_here
   GOOGLE_CSE_ID=your_google_cse_id_here
   ```

### Running the Test

```bash
# From project root directory
python simple_test.py
```

## Expected Output

The test will run a comprehensive analysis of **UPS** and output:

```
🧪 Testing analyze_company_sustainability function...
==================================================
AI SUSTAINABILITY ANALYSIS: UPS
==================================================
Analyzing 8 criteria using PURE AI logic
Standardized limits: Search=5, Web=UNLIMITED (all URLs), PDFs=Full analysis
==================================================

Phase 0: PDF Sustainability Reports (PRIORITY)
----------------------------------------
  Analyzing sustainability PDFs first - highest quality evidence
  Getting sustainability PDF reports...
  Found 3 sustainability PDFs
  Analyzing PDF 1/3: https://example.com/sustainability-report.pdf
    PDF 1: 45,230 characters extracted
    Found cng_fleet in PDF (score: 3)
    Found emission_goals in PDF (score: 2)
    ...

Phase 1: Enhanced Search Analysis
----------------------------------------
  Analyzing search results for 6 missing criteria: ['alt_fuels', 'regulatory', ...]
  Getting enhanced targeted search results...
    cng_fleet_size: Found 4 search results
    Found cng_fleet_size in targeted search (score: 2, confidence: 85%)
    ...

Phase 3: Smart Web Scraping (FINAL FALLBACK - UNLIMITED)
----------------------------------------
  Scraping ALL collected URLs for 2 missing criteria: ['alt_fuels', 'regulatory']
  Found 12 targeted URLs to scrape
  Scraping page 1/12: https://ups.com/sustainability
    Getting COMPLETE website content...
    Clean HTML text: 15,430 characters
    Analyzing COMPLETE content from https://ups.com/sustainability (15,430 chars)
    Web scraping found alt_fuels (score: 1)
    ...

==================================================
✅ SUCCESS! Function completed successfully
==================================================
📋 FUNCTION RETURN VALUE:
==================================================
{
  "company": "UPS",
  "criteria_analyzed": ["total_truck_fleet_size", "cng_fleet", ...],
  "evidence_details": {
    "cng_fleet": {
      "criterion": "cng_fleet",
      "found": true,
      "score": 3,
      "confidence": 95,
      "evidence_text": "UPS operates a fleet of over 125,000 vehicles including 6,100 CNG vehicles...",
      "justification": "Clear evidence of CNG fleet operation with specific vehicle count",
      "source_type": "pdf_content",
      "url": "https://example.com/sustainability-report.pdf",
      "verified": true,
      ...
    },
    ...
  },
  "total_criteria": 8,
  "found_criteria": 7,
  "analysis_time": 127.45,
  "timestamp": 1703123456.789,
  "analysis_summary": {
    "criteria_found": ["cng_fleet", "cng_fleet_size", ...],
    "criteria_not_found": ["regulatory"],
    "sources_analyzed": {
      "pdfs_checked": ["https://example.com/sustainability-report.pdf", ...],
      "web_pages_scraped": ["https://ups.com/sustainability", ...],
      "search_queries_executed": ["UPS CNG fleet size", ...],
      "total_sources_count": 15,
      "successful_sources_count": 12
    },
    "phases_completed": ["Phase 0: PDF Analysis Complete (3 criteria found)", ...],
    "processing_errors": []
  },
  "evidence_quality": {
    "high_confidence": ["cng_fleet", "emission_reporting"],
    "medium_confidence": ["cng_fleet_size", "emission_goals"],
    "low_confidence": ["alt_fuels"],
    "source_breakdown": {
      "pdf_evidence": ["cng_fleet", "emission_reporting"],
      "web_evidence": ["alt_fuels", "clean_energy_partner"],
      "search_evidence": ["cng_fleet_size"]
    }
  },
  "performance_metrics": {
    "total_analysis_time": 127.45,
    "phase_breakdown": {
      "Phase 0: PDF Analysis": 45.2,
      "Phase 1: Enhanced Search": 32.1,
      "Phase 3: Web Scraping": 50.15
    },
    "efficiency_score": 5.5,
    "sources_per_criterion": 1.875,
    "success_rate": 80.0
  }
}

🎉 Test completed successfully!
```

## New Pipeline Structure

### 🏗️ Architecture Overview

The scraper now uses a **3-phase analysis pipeline** with enhanced output structure:

```
┌─────────────────────────────────────────────────────────────┐
│                    NEW COMPREHENSIVE OUTPUT                 │
├─────────────────────────────────────────────────────────────┤
│ 📊 Basic Results:                                           │
│   • company, criteria_analyzed, evidence_details           │
│   • total_criteria, found_criteria, analysis_time          │
│                                                             │
│ 📈 Analysis Summary:                                        │
│   • criteria_found/not_found                               │
│   • sources_analyzed (PDFs, web pages, search queries)     │
│   • phases_completed, processing_errors                    │
│                                                             │
│ 🎯 Evidence Quality:                                        │
│   • high/medium/low confidence breakdown                   │
│   • source breakdown (PDF, web, search)                    │
│                                                             │
│ ⚡ Performance Metrics:                                     │
│   • total_analysis_time, phase_breakdown                   │
│   • efficiency_score, sources_per_criterion, success_rate  │
└─────────────────────────────────────────────────────────────┘
```

### 🔄 3-Phase Analysis Process

#### Phase 0: PDF Analysis (Highest Quality)
- **Purpose**: Extract evidence from official company sustainability reports
- **Method**: Downloads and analyzes PDFs using AI
- **Quality**: Highest confidence evidence (95%+ accuracy)
- **Output**: Direct quotes from company documents

#### Phase 1: Enhanced Search Analysis
- **Purpose**: Find missing criteria through targeted Google searches
- **Method**: Performs criterion-specific searches and analyzes snippets
- **Quality**: Medium confidence evidence (70-90% accuracy)
- **Output**: Validated search result evidence

#### Phase 3: Web Scraping (Final Fallback)
- **Purpose**: Comprehensive web page analysis for remaining criteria
- **Method**: Scrapes relevant URLs with enhanced content extraction
- **Quality**: Variable confidence (50-85% accuracy)
- **Output**: Full website content analysis

### 🆕 Enhanced Content Extraction

The new pipeline includes **multiple content extraction methods**:

```python
# Method 1: Enhanced HTML to text conversion
clean_text = html_to_clean_text(html_content, url)

# Method 2: Simple innerText extraction
body_text = page.evaluate("() => document.body ? document.body.innerText : ''")

# Method 3: Content-specific selectors
selector_text = page.evaluate("() => { const el = document.querySelector('main'); return el ? el.innerText : ''; }")

# Method 4: Table extraction (important for fleet data)
table_text = page.evaluate("() => { /* extract table data */ }")

# Method 5: Fallback paragraph extraction
fallback_text = page.evaluate("() => { /* extract all paragraphs */ }")
```

### 🛡️ JavaScript Filtering

New `is_mostly_javascript()` function filters out:
- JavaScript code and syntax
- Analytics and tracking scripts
- Minified code
- Common JS libraries and frameworks
- Marketing pixels and tracking code

## Configuration Options

### Test Parameters

You can modify `simple_test.py` to test different scenarios:

```python
# Test with different company
results = analyze_company_sustainability(
    company_name='FedEx',  # Change company
    criteria={'cng_fleet', 'emission_goals'},  # Test specific criteria
    max_search_pages=5,    # Limit search depth
    max_pdf_reports=3,     # Limit PDF analysis
    max_web_pages=10,      # Limit web scraping
    verbose=True           # Show detailed output
)
```

### Available Criteria

```python
ALL_CRITERIA = {
    'total_truck_fleet_size',  # Total fleet size
    'cng_fleet',              # CNG fleet presence
    'cng_fleet_size',         # CNG fleet size
    'emission_reporting',     # Sustainability reports
    'emission_goals',         # Carbon reduction goals
    'alt_fuels',              # Alternative fuels
    'clean_energy_partner',   # Clean energy partnerships
    'regulatory'              # Regulatory compliance
}
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the project root
   cd /path/to/Chevron-SQ
   python simple_test.py
   ```

2. **API Key Errors**
   ```bash
   # Check your .env file
   cat .env
   # Should contain: OPENAI_API_KEY, GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID
   ```

3. **Timeout Errors**
   ```python
   # Reduce analysis depth in simple_test.py
   max_search_pages=2,    # Reduce from 20
   max_pdf_reports=2,     # Reduce from 7
   max_web_pages=5,       # Reduce from 15
   ```

4. **No Results Found**
   ```python
   # Try a different company
   company_name='Amazon'  # Instead of 'UPS'
   ```

### Debug Mode

The test runs with `verbose=True` by default, showing:
- Detailed progress through each phase
- Content extraction methods used
- AI analysis results
- Performance metrics

## Integration with ScraperService

The `simple_test.py` tests the raw `analyze_company_sustainability` function. For production use, consider using the `ScraperService`:

```python
from backend.src.scraper.scraper_service import analyze_company_structured

# Get structured results with overall scoring
results = analyze_company_structured("UPS")

# Access structured data
company_info = results["company"]
metrics = results["sustainability_metrics"]
overall_score = results["overall_score"]
```

## Performance Expectations

### Typical Runtime
- **Small company**: 2-3 minutes
- **Large company**: 3-5 minutes
- **Company with limited info**: 4-6 minutes

### Success Rates
- **Companies with good sustainability reporting**: 7-8/8 criteria found
- **Average companies**: 5-7/8 criteria found
- **Companies with limited info**: 3-5/8 criteria found

## Next Steps

After running `simple_test.py` successfully:

1. **Test with different companies** to validate the pipeline
2. **Use ScraperService** for production integration
3. **Integrate with FastAPI routes** for web API
4. **Customize criteria** for specific use cases
5. **Monitor performance metrics** to optimize analysis

## File Structure

```
Chevron-SQ/
├── simple_test.py                    # 🧪 This test file
├── backend/src/scraper/
│   ├── main_ai_scraper.py           # 🎯 Main analysis function
│   ├── scraper_service.py           # 🆕 Service layer
│   ├── ai_criteria_analyzer.py      # 🧠 AI analysis
│   ├── export/json_exporter.py      # 📊 JSON export
│   └── utils/                       # 🔧 Utilities
└── .env                             # 🔑 Environment variables
```

This test file provides a quick way to validate the entire scraper pipeline and understand the new comprehensive output structure. 