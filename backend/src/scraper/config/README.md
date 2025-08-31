# Configuration Module - System Settings and Patterns

This directory contains YAML configuration files that control various aspects of the scraper's behavior, including URL scoring, domain validation, and criteria ranges.

## Overview

The `config/` module provides:

- **PDF URL scoring patterns** - Rules for prioritizing PDF documents
- **Trusted domain lists** - Authoritative sources for sustainability data
- **Criteria scoring ranges** - Database mapping and score ranges for each metric
- **Flexible configuration** - Easy to modify without code changes

## Configuration Files

### `pdf_patterns.yaml` - PDF URL Scoring Configuration

**Purpose**: Defines patterns for scoring PDF URLs to prioritize high-quality sustainability documents

**Structure**:

```yaml
# High-value PDF patterns (sustainability reports, ESG documents)
high_priority_patterns:
  - sustainability
  - esg-report
  - environmental
  - csr-report
  - climate

# Medium-value PDF patterns (annual reports, regulatory filings)
medium_priority_patterns:
  - annual-report
  - 10-k
  - proxy
  - impact

# Low-value PDF patterns (general content)
low_priority_patterns:
  - newsletter
  - presentation
  - brochure

# Patterns to avoid (marketing, product content)
exclude_patterns:
  - product
  - catalog
  - marketing
  - advertisement
```

**How it's used**:

```python
def score_pdf_url(url: str) -> int:
    """Score PDF URLs based on patterns (higher = better priority)"""
    url_lower = url.lower()

    # Check high-priority patterns (+30 points)
    if any(pattern in url_lower for pattern in config['high_priority_patterns']):
        return 30

    # Check medium-priority patterns (+20 points)
    elif any(pattern in url_lower for pattern in config['medium_priority_patterns']):
        return 20

    # Check low-priority patterns (+10 points)
    elif any(pattern in url_lower for pattern in config['low_priority_patterns']):
        return 10

    # Check exclude patterns (0 points)
    elif any(pattern in url_lower for pattern in config['exclude_patterns']):
        return 0

    return 5  # Default score for unknown PDFs
```

**Example URLs and scoring**:

- `https://company.com/sustainability-report-2023.pdf` → 30 points (high priority)
- `https://company.com/annual-report-2023.pdf` → 20 points (medium priority)
- `https://company.com/quarterly-newsletter.pdf` → 10 points (low priority)
- `https://company.com/product-catalog.pdf` → 0 points (excluded)

### `trusted_domains.yaml` - Authoritative Source Validation

**Purpose**: Defines domains that are considered trustworthy sources for sustainability information

**Structure**:

```yaml
# Government and regulatory domains
government_domains:
  - epa.gov
  - sec.gov
  - carb.ca.gov
  - smartway.gov
  - energy.gov

# Industry organizations and standards bodies
industry_domains:
  - trucking.org
  - sustainable-trucking.org
  - freightwaves.com
  - fleet-central.com

# Reputable news and analysis sources
news_domains:
  - reuters.com
  - bloomberg.com
  - wsj.com
  - greenbiz.com
  - sustainablebrands.com

# Academic and research institutions
academic_domains:
  - .edu
  - mit.edu
  - stanford.edu
  - research.org

# Professional services (consulting, legal)
professional_domains:
  - mckinsey.com
  - deloitte.com
  - pwc.com
  - ey.com

# Company-specific patterns (automatically trusted for that company)
company_domain_patterns:
  - "{company}.com"
  - "sustainability.{company}.com"
  - "investor.{company}.com"
  - "about.{company}.com"
```

**How it's used**:

```python
def is_trusted_domain(url: str, company: str) -> bool:
    """Check if domain is in trusted list"""
    domain = extract_domain(url)

    # Check government domains
    if domain in config['government_domains']:
        return True

    # Check industry domains
    if domain in config['industry_domains']:
        return True

    # Check if it's company's own domain
    company_domains = [pattern.format(company=company.lower())
                      for pattern in config['company_domain_patterns']]
    if any(company_domain in domain for company_domain in company_domains):
        return True

    return False
```

### `number_ranges.yaml` - Criteria Scoring and Database Mapping

**Purpose**: Defines score ranges for each sustainability criterion and maps them to database fields

**Structure**:

```yaml
# Fleet size criteria
total_truck_fleet_size:
  score_range: [0, 3]
  database_field: "total_fleet_size"
  ranges:
    0: "No fleet information"
    1: "Small fleet (<1,000 vehicles)"
    2: "Medium fleet (1,000-10,000 vehicles)"
    3: "Large fleet (>10,000 vehicles)"

cng_fleet_size:
  score_range: [0, 3]
  database_field: "cng_fleet_size_range"
  ranges:
    0: "No CNG fleet"
    1: "Small CNG fleet (<500 vehicles)"
    2: "Medium CNG fleet (500-1,000 vehicles)"
    3: "Large CNG fleet (>1,000 vehicles)"

# Boolean criteria
cng_fleet:
  score_range: [0, 1]
  database_field: "owns_cng_fleet"
  ranges:
    0: false
    1: true

emission_reporting:
  score_range: [0, 1]
  database_field: "emission_report"
  ranges:
    0: false
    1: true

# Multi-level criteria
emission_goals:
  score_range: [0, 2]
  database_field: "emission_goals"
  ranges:
    0: "No emission goals"
    1: "Basic emission reduction goals"
    2: "Detailed goals with timeline and targets"

# Other boolean criteria
alt_fuels:
  score_range: [0, 1]
  database_field: "alt_fuels"
  ranges:
    0: false
    1: true

clean_energy_partner:
  score_range: [0, 1]
  database_field: "clean_energy_partners"
  ranges:
    0: false
    1: true

regulatory:
  score_range: [0, 1]
  database_field: "regulatory_pressure"
  ranges:
    0: false
    1: true
```

**How it's used**:

```python
def get_score_range(criterion: str) -> Tuple[int, int]:
    """Get valid score range for a criterion"""
    config_data = load_config('number_ranges.yaml')
    criterion_config = config_data.get(criterion, {})
    return tuple(criterion_config.get('score_range', [0, 1]))

def map_to_database_field(criterion: str) -> str:
    """Get database field name for criterion"""
    config_data = load_config('number_ranges.yaml')
    criterion_config = config_data.get(criterion, {})
    return criterion_config.get('database_field', criterion)

def get_range_description(criterion: str, score: int) -> str:
    """Get human-readable description for score"""
    config_data = load_config('number_ranges.yaml')
    criterion_config = config_data.get(criterion, {})
    ranges = criterion_config.get('ranges', {})
    return ranges.get(score, f"Score {score}")
```

## Configuration Loading and Usage

### Configuration Loader

```python
import yaml
from pathlib import Path

def load_config(config_file: str) -> dict:
    """Load configuration from YAML file"""
    config_path = Path(__file__).parent / config_file
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Usage examples
pdf_config = load_config('pdf_patterns.yaml')
domain_config = load_config('trusted_domains.yaml')
ranges_config = load_config('number_ranges.yaml')
```

### Dynamic Configuration Updates

```python
# Add new trusted domain without code changes
def add_trusted_domain(domain: str, category: str):
    """Add domain to trusted list"""
    config = load_config('trusted_domains.yaml')
    if category in config:
        config[category].append(domain)
        save_config('trusted_domains.yaml', config)

# Update PDF scoring patterns
def add_pdf_pattern(pattern: str, priority: str):
    """Add new PDF scoring pattern"""
    config = load_config('pdf_patterns.yaml')
    priority_key = f"{priority}_priority_patterns"
    if priority_key in config:
        config[priority_key].append(pattern)
        save_config('pdf_patterns.yaml', config)
```

## Customization Examples

### Adding New Trusted Domains

```yaml
# trusted_domains.yaml - Add new industry sources
industry_domains:
  - trucking.org
  - fleet-central.com
  - clean-energy-fuels.com # Add new domain
  - sustainable-logistics.org # Add new domain
```

### Modifying PDF Scoring

```yaml
# pdf_patterns.yaml - Add new high-priority patterns
high_priority_patterns:
  - sustainability
  - esg-report
  - carbon-report # Add new pattern
  - climate-action # Add new pattern
```

### Adjusting Score Ranges

```yaml
# number_ranges.yaml - Modify CNG fleet size ranges
cng_fleet_size:
  score_range: [0, 4] # Extend range to 4 levels
  database_field: "cng_fleet_size_range"
  ranges:
    0: "No CNG fleet"
    1: "Small CNG fleet (<100 vehicles)"
    2: "Medium CNG fleet (100-500 vehicles)"
    3: "Large CNG fleet (500-1,000 vehicles)"
    4: "Very large CNG fleet (>1,000 vehicles)" # New level
```

## Environment-Specific Configuration

### Development vs. Production

```python
# Load environment-specific config
import os

env = os.getenv('ENVIRONMENT', 'development')
config_file = f'trusted_domains_{env}.yaml'

if env == 'development':
    # More permissive in development
    config = load_config('trusted_domains_dev.yaml')
else:
    # Stricter in production
    config = load_config('trusted_domains_prod.yaml')
```

### Company-Specific Overrides

```python
# Load company-specific configuration if available
def load_company_config(company: str, base_config: str) -> dict:
    """Load company-specific config with fallback to base config"""
    company_config_file = f"{base_config.replace('.yaml', '')}_{company.lower()}.yaml"

    try:
        return load_config(company_config_file)
    except FileNotFoundError:
        return load_config(base_config)

# Usage
pdf_config = load_company_config("Amazon", "pdf_patterns.yaml")
```

## Benefits of Configuration-Based Approach

### Maintainability

- **No code changes**: Modify behavior without touching source code
- **Version control**: Track configuration changes separately
- **Easy rollback**: Revert configuration changes quickly
- **Environment consistency**: Same code, different configurations

### Flexibility

- **Rapid iteration**: Test new patterns and domains quickly
- **A/B testing**: Compare different configuration approaches
- **Customer customization**: Company-specific configurations
- **Operational tuning**: Adjust thresholds based on performance

### Quality Control

- **Centralized rules**: All scoring logic in one place
- **Consistent application**: Same rules applied everywhere
- **Easy auditing**: Review all configuration decisions
- **Documentation**: Configuration files serve as documentation

The configuration system provides a flexible, maintainable way to control scraper behavior without requiring code changes.
