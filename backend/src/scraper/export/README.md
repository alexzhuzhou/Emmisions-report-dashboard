# Export Module - Database-Ready Output

This module converts raw analysis results into structured, database-ready JSON format suitable for PostgreSQL storage and business intelligence systems.

## Overview

The export system takes evidence found during scraper analysis and transforms it into a standardized format with:

- **Business logic corrections** (automatic consistency fixes)
- **Database-compatible structure** (PostgreSQL JSON field types)
- **Audit trails** (complete source tracking for compliance)
- **Human-readable summaries** (for dashboards and reports)

## Core Functionality

### `json_exporter.py` - The Main Export Engine

**Purpose**: Transform AI analysis results into business-ready, database-compatible JSON

## Key Classes

### `SustainabilityDataExporter`

**What it does**: Central class that orchestrates the entire export process
**Why it exists**: Provides a clean interface for converting complex evidence data into structured business format

#### Core Methods

##### `set_company_info(company_name: str)`

**Purpose**: Initialize the exporter with basic company information
**Parameters**:

- `company_name`: The company being analyzed

**Example**:

```python
from backend.src.scraper.export.json_exporter import SustainabilityDataExporter

exporter = SustainabilityDataExporter()
exporter.set_company_info("Amazon")
```

##### `process_criteria_evidence(evidence_details: Dict, company_name: str)`

**Purpose**: Process raw evidence into structured metrics and sources
**Parameters**:

- `evidence_details`: Dictionary of CriteriaEvidence objects from AI analysis
- `company_name`: Company name for validation

**What it does**:

1. Converts AI evidence into database-compatible metrics
2. Applies business logic corrections for consistency
3. Creates audit trail linking metrics to source evidence
4. Generates human-readable summaries

**Example**:

```python
# After running AI analysis
evidence = {
    'cng_fleet_size': CriteriaEvidence(
        criterion='cng_fleet_size',
        found=True,
        score=3,
        evidence_text='Amazon operates 4,400 CNG vehicles',
        url='https://sustainability.amazon.com/report.pdf'
    )
}

exporter.process_criteria_evidence(evidence, "Amazon")
```

##### `export_to_json() -> Dict`

**Purpose**: Generate the final JSON structure ready for database storage
**Returns**: Complete JSON object with all data and metadata

## Business Logic Corrections

The exporter includes intelligent business logic to ensure data consistency:

### Automatic Fleet Consistency

```python
# BEFORE: Inconsistent data
{
    "owns_cng_fleet": null,           # Unknown
    "cng_fleet_size_actual": 4400     # But we have a size!
}

# AFTER: Auto-corrected by business logic
{
    "owns_cng_fleet": True,           # Auto-set to True
    "cng_fleet_size_actual": 4400
}
```

### Size Range Mapping

```python
# BEFORE: Raw numbers
{
    "cng_fleet_size_actual": 4400
}

# AFTER: Adds categorical range
{
    "cng_fleet_size_actual": 4400,
    "cng_fleet_size_range": 3        # 3 = "Large fleet (1000+)"
}
```

### Summary Generation

```python
# BEFORE: Raw evidence
{
    "cng_fleet_size_actual": 4400,
    "owns_cng_fleet": True
}

# AFTER: Adds human-readable summary
{
    "cng_fleet_size_actual": 4400,
    "owns_cng_fleet": True,
    "summaries": {
        "fleet_summary": {
            "summary_text": "The company operates a CNG fleet of 4400 vehicles."
        }
    }
}
```

## Output Structure Explained

### Complete JSON Schema

```json
{
  "company": {
    "company_name": "Amazon", // Primary identifier
    "company_summary": "Amazon is a logistics...", // AI-generated overview
    "website_url": "https://amazon.com", // Official website
    "industry": "E-commerce & Logistics", // Industry classification
    "cso_linkedin_url": "" // Chief Sustainability Officer LinkedIn
  },

  "sustainability_metrics": {
    // FLEET METRICS
    "owns_cng_fleet": true, // Boolean: Has CNG vehicles
    "cng_fleet_size_range": 3, // 0-3 scale (0=None, 1=Small, 2=Medium, 3=Large)
    "cng_fleet_size_actual": 4400, // Exact vehicle count if known
    "total_fleet_size": 50000, // Total vehicles across all fuel types

    // REPORTING METRICS
    "emission_report": true, // Boolean: Publishes emissions reports
    "emission_goals": 2, // 0-2 scale (0=None, 1=Basic, 2=Detailed)

    // FUEL & ENERGY METRICS
    "alt_fuels": true, // Boolean: Uses biodiesel/RNG/SAF
    "clean_energy_partners": true, // Boolean: External clean energy partnerships

    // REGULATORY METRICS
    "regulatory_pressure": true // Boolean: Subject to freight regulations
  },

  "metric_sources": [
    // Complete audit trail
    {
      "metric_name": ["cng_fleet_size", "owns_cng_fleet"], // Which metrics this supports
      "source_url": "https://sustainability.amazon.com/report.pdf",
      "contribution_text": "Amazon operates 4,400 CNG vehicles globally", // Exact quote
      "source_type": "pdf_content", // pdf_content, web_content, search_snippet
      "verified": true, // Whether quote was verified in source
      "confidence_score": 3 // AI confidence (0-3)
    }
  ],

  "summaries": {
    // Human-readable summaries
    "fleet_summary": {
      "summary_text": "The company operates a CNG fleet of 4400 vehicles."
    },
    "emission_summary": {
      "summary_text": "Company publishes annual sustainability reports with emission reduction goals."
    },
    "fuel_summary": {
      "summary_text": "Uses alternative fuels including renewable natural gas and biodiesel."
    },
    "partnership_summary": {
      "summary_text": "Partners with Clean Energy Fuels and other renewable energy providers."
    },
    "regulatory_summary": {
      "summary_text": "Subject to EPA SmartWay and CARB regulations."
    }
  },

  "metadata": {
    // Analysis metadata
    "analysis_timestamp": "2024-01-15T10:30:00Z",
    "scraper_version": "2.1.0",
    "criteria_analyzed": 8,
    "criteria_found": 7,
    "total_sources": 12,
    "pdf_sources": 3,
    "web_sources": 9
  }
}
```

## Database Integration

### PostgreSQL Storage

The JSON output is designed for PostgreSQL JSONB fields:

```sql
CREATE TABLE company_sustainability (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    analysis_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert analysis results
INSERT INTO company_sustainability (company_name, analysis_data)
VALUES ('Amazon', '{"company": {"company_name": "Amazon", ...}}');

-- Query specific metrics
SELECT
    company_name,
    analysis_data->'sustainability_metrics'->>'owns_cng_fleet' as has_cng,
    analysis_data->'sustainability_metrics'->>'cng_fleet_size_actual' as fleet_size
FROM company_sustainability;
```

### Business Intelligence Queries

```sql
-- Companies with large CNG fleets
SELECT company_name,
       analysis_data->'sustainability_metrics'->>'cng_fleet_size_actual' as fleet_size
FROM company_sustainability
WHERE analysis_data->'sustainability_metrics'->>'cng_fleet_size_range' = '3';

-- Emission reporting compliance
SELECT company_name,
       analysis_data->'sustainability_metrics'->>'emission_report' as reports_emissions
FROM company_sustainability
WHERE analysis_data->'sustainability_metrics'->>'emission_report' = 'true';
```

## Error Handling & Data Quality

### Missing Data Handling

```python
# If no evidence found for a criterion
{
    "owns_cng_fleet": null,        # null = no evidence found
    "cng_fleet_size_actual": null
}

# vs. explicit negative evidence
{
    "owns_cng_fleet": false,       # false = explicitly stated they don't have CNG
    "cng_fleet_size_actual": 0
}
```

### Data Validation

The exporter validates:

- **Logical consistency** (fleet size > 0 means owns_fleet = true)
- **Data types** (numbers are numeric, booleans are boolean)
- **Required fields** (company name, timestamp always present)
- **Source integrity** (all metrics have corresponding sources)

### Quality Indicators

```json
{
  "metadata": {
    "quality_score": 0.85, // 0-1 overall data quality
    "source_reliability": "high", // high/medium/low based on source types
    "evidence_coverage": 0.875 // % of criteria with evidence (7/8 = 0.875)
  }
}
```

## Usage Examples

### Basic Export

```python
from backend.src.scraper.export.json_exporter import SustainabilityDataExporter

# Create exporter
exporter = SustainabilityDataExporter()
exporter.set_company_info("UPS")

# Process AI analysis results
exporter.process_criteria_evidence(evidence_dict, "UPS")

# Export to JSON
json_data = exporter.export_to_json()

# Save to file
import json
with open("ups_sustainability.json", "w") as f:
    json.dump(json_data, f, indent=2)
```

### Programmatic Access

```python
# Get specific metrics
metrics = json_data["sustainability_metrics"]
has_cng = metrics["owns_cng_fleet"]
fleet_size = metrics["cng_fleet_size_actual"]

# Get audit trail
sources = json_data["metric_sources"]
for source in sources:
    print(f"Found {source['metric_name']} from {source['source_url']}")

# Get summaries
summaries = json_data["summaries"]
fleet_summary = summaries["fleet_summary"]["summary_text"]
```

### Integration with Main Scraper

```python
from backend.src.scraper.main_ai_scraper import analyze_company_sustainability

# Run analysis
results = analyze_company_sustainability("FedEx")

# JSON export is automatically included
json_output = results["json_export"]        # JSON string
filename = results["json_filename"]         # Output filename

# Access structured data
import json
structured_data = json.loads(json_output)
```

## Business Logic Details

### Fleet Size Range Mapping

```python
def map_fleet_size_to_range(actual_size: int) -> int:
    """Map actual fleet size to categorical range"""
    if actual_size == 0:
        return 0  # No fleet
    elif actual_size <= 500:
        return 1  # Small fleet
    elif actual_size <= 1000:
        return 2  # Medium fleet
    else:
        return 3  # Large fleet
```

### Emission Goals Scoring

```python
def score_emission_goals(evidence_text: str) -> int:
    """Score emission goals based on detail level"""
    if "net zero" in evidence_text and any(year in evidence_text for year in ["2030", "2040", "2050"]):
        return 2  # Detailed goals with timeline
    elif any(goal in evidence_text for goal in ["reduce", "carbon neutral", "emission"]):
        return 1  # Basic goals
    else:
        return 0  # No goals
```

## Performance & Scalability

### Efficiency Features

- **Single-pass processing**: Each evidence item processed once
- **Lazy evaluation**: Summaries generated only when needed
- **Memory efficient**: Streaming JSON generation for large datasets
- **Database optimized**: Output structure matches database schema

### Batch Processing

```python
# Process multiple companies
companies = ["Amazon", "UPS", "FedEx", "DHL"]
all_results = []

for company in companies:
    results = analyze_company_sustainability(company)
    all_results.append(json.loads(results["json_export"]))

# Bulk database insert
insert_bulk_sustainability_data(all_results)
```

The export system is designed for production use with enterprise-grade data quality, audit compliance, and business intelligence integration.
