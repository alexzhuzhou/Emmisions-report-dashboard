# Crawler Module - Intelligent Web Crawling

This module contains the web crawling logic that decides which URLs to visit and how to safely retrieve content for sustainability analysis.

## Overview

The `crawler/` module provides:

- **Smart URL filtering** - Only crawls relevant, high-quality sources
- **Safe content retrieval** - Handles timeouts, errors, and malicious sites
- **Domain validation** - Ensures sources are trustworthy and authoritative
- **Crawling optimization** - Efficient resource usage and respectful crawling

## Files & Components

### `fetch.py` - Web Crawling Engine

**Purpose**: Intelligent web crawling with quality filtering and safe content retrieval

## Key Functions

### URL Filtering Functions

#### `should_crawl(url: str, needed_criteria: Set[str], company: str) -> bool`

**What it does**: Determines if a URL is worth crawling based on relevance and quality
**Parameters**:

- `url`: The URL to evaluate
- `needed_criteria`: Set of sustainability criteria still needed
- `company`: Target company name for relevance checking

**Returns**: True if URL should be crawled, False if it should be skipped

**Example usage**:

```python
from backend.src.scraper.crawler.fetch import should_crawl

# Check if URL is worth crawling
url = "https://company.com/sustainability-report"
criteria = {"cng_fleet", "emission_goals"}
company = "Company Name"

if should_crawl(url, criteria, company):
    print("URL is relevant - proceed with crawling")
    # Extract content from URL
else:
    print("URL not relevant - skip to save resources")
```

**What it filters out**:

- Product pages and e-commerce listings
- Social media posts and user-generated content
- Marketing and promotional pages
- Irrelevant news articles
- Broken or suspicious URLs
- Non-sustainability related content

**What it prioritizes**:

- Official company sustainability reports
- News articles about company sustainability initiatives
- Regulatory filings and compliance documents
- Industry reports mentioning the company
- Academic research and case studies

#### `should_crawl_pdf(pdf_url: str, company: str) -> bool`

**What it does**: Specialized filtering for PDF documents
**Parameters**:

- `pdf_url`: URL of the PDF to evaluate
- `company`: Target company name

**Returns**: True if PDF should be downloaded and analyzed

**PDF-specific filtering**:

- Prioritizes sustainability and ESG reports
- Accepts annual reports and 10-K filings
- Rejects product catalogs and marketing brochures
- Validates file size and accessibility

### Content Retrieval Functions

#### `safe_get_page_content(url: str, page=None) -> str`

**What it does**: Safely retrieves web page content with error handling and timeouts
**Parameters**:

- `url`: URL to retrieve content from
- `page`: Optional Playwright page object for JavaScript-heavy sites

**Returns**: Clean text content from the page, or empty string if retrieval fails

**Example usage**:

```python
from backend.src.scraper.crawler.fetch import safe_get_page_content

# Retrieve content safely
content = safe_get_page_content("https://company.com/sustainability")
if content:
    print(f"Retrieved {len(content)} characters")
    # Process content with AI
else:
    print("Failed to retrieve content")
```

**Safety features**:

- **Timeout protection**: Prevents hanging on slow/broken sites
- **Error recovery**: Graceful handling of network errors
- **Content validation**: Ensures retrieved content is meaningful
- **Resource limits**: Prevents excessive memory usage
- **Rate limiting**: Respectful crawling practices

### Domain Validation Functions

#### `is_trusted_domain_ai(url: str, company: str) -> bool`

**What it does**: Validates that a domain is trustworthy for sustainability information
**Parameters**:

- `url`: URL to validate
- `company`: Target company for relevance checking

**Returns**: True if domain is considered trustworthy

**Trusted domain categories**:

- **Official company domains** (company.com, sustainability.company.com)
- **Government sites** (epa.gov, sec.gov, carb.ca.gov)
- **Industry organizations** (smartway.gov, trucking.org)
- **Reputable news sources** (reuters.com, bloomberg.com)
- **Academic institutions** (.edu domains)
- **Professional services** (consulting firms, law firms with sustainability practice)

**Rejected domain categories**:

- Social media platforms
- User-generated content sites
- Marketing and advertising domains
- Suspicious or unknown domains
- Sites with poor reputation scores

## Crawling Strategy

### Prioritization Algorithm

The crawler uses a sophisticated scoring system to prioritize URLs:

```python
def score_url(url: str, criteria: Set[str], company: str) -> int:
    """Calculate relevance score for URL (higher = better)"""
    score = 0

    # Domain authority (0-30 points)
    if is_company_domain(url, company):
        score += 30  # Official company domain
    elif is_government_domain(url):
        score += 25  # Government source
    elif is_news_domain(url):
        score += 15  # News source

    # Content relevance (0-25 points)
    url_lower = url.lower()
    if "sustainability" in url_lower:
        score += 25
    elif "environment" in url_lower:
        score += 20
    elif "fleet" in url_lower:
        score += 15

    # File type bonus (0-10 points)
    if url.endswith('.pdf'):
        score += 10  # PDFs often contain detailed information

    return score
```

### Crawling Phases

#### Phase 1: Seed URL Discovery

- Start with official company website
- Search for sustainability-related pages
- Identify high-value PDF reports
- Build initial URL queue with priorities

#### Phase 2: Targeted Crawling

- Process URLs in priority order
- Extract content and analyze with AI
- Discover additional relevant URLs
- Stop when all criteria found or limits reached

#### Phase 3: Deep Crawling (Optional)

- Follow links from high-quality pages
- Explore company subdomains
- Check industry reports and case studies
- Used only when comprehensive analysis needed

## Configuration and Limits

### Crawling Limits (Configurable)

```python
# Maximum pages to crawl per analysis
MAX_CRAWL_PAGES = 8

# Maximum time per page (seconds)
PAGE_TIMEOUT = 8

# Maximum PDF size to download (MB)
MAX_PDF_SIZE = 50

# Maximum depth from seed URLs
MAX_CRAWL_DEPTH = 3
```

### Respectful Crawling

- **Rate limiting**: Minimum delay between requests
- **robots.txt compliance**: Respects site crawling preferences
- **User agent identification**: Properly identifies as research crawler
- **Resource limits**: Doesn't overwhelm target servers

## Error Handling

### Common Issues and Responses

- **Network timeouts**: Retry with exponential backoff
- **403 Forbidden**: Skip URL and log for manual review
- **404 Not Found**: Remove from queue, try related URLs
- **Large files**: Stream processing or skip if too large
- **Malformed content**: Extract what's possible, continue analysis

### Fallback Strategies

- **JavaScript sites**: Use Playwright for dynamic content
- **PDF extraction failures**: Try multiple extraction methods
- **Encoding issues**: Automatic encoding detection and conversion
- **Blocked crawlers**: Switch to search-based content discovery

## Integration with Main System

### Crawling Pipeline

```python
# 1. Get target URLs for missing criteria
target_urls = get_enhanced_missing_criteria_seeds(company, missing_criteria)

# 2. Filter and prioritize URLs
relevant_urls = [url for url in target_urls if should_crawl(url, missing_criteria, company)]
relevant_urls.sort(key=lambda url: score_url(url, missing_criteria, company), reverse=True)

# 3. Crawl top URLs with limits
for url in relevant_urls[:MAX_CRAWL_PAGES]:
    content = safe_get_page_content(url)
    if content:
        # Analyze content with AI
        evidence = analyze_text_with_ai(content, url, missing_criteria, company)
        # Store any evidence found
        update_evidence_store(evidence)
```

### Quality Assurance

- **Content validation**: Ensure extracted content is relevant
- **Source verification**: Confirm URLs actually contain claimed content
- **Duplicate detection**: Avoid analyzing same content multiple times
- **Progress tracking**: Monitor crawling efficiency and success rates

## Performance Optimization

### Efficiency Features

- **Parallel processing**: Multiple URLs crawled simultaneously
- **Intelligent caching**: Avoid re-crawling same content
- **Early termination**: Stop when sufficient evidence found
- **Resource pooling**: Reuse HTTP connections and browser instances

### Memory Management

- **Streaming processing**: Handle large documents without loading entirely
- **Garbage collection**: Clean up resources after each page
- **Connection limits**: Prevent resource exhaustion
- **Content size limits**: Skip extremely large or small pages

## Usage Examples

### Basic URL Filtering

```python
from backend.src.scraper.crawler.fetch import should_crawl

urls_to_check = [
    "https://company.com/sustainability-report",  # Good
    "https://company.com/products/widget",        # Skip
    "https://news.com/company-green-initiative",  # Good
    "https://spam-site.com/company-mention"       # Skip
]

for url in urls_to_check:
    if should_crawl(url, {"emission_goals"}, "Company"):
        print(f"✓ {url}")
    else:
        print(f"✗ {url}")
```

### Safe Content Retrieval

```python
from backend.src.scraper.crawler.fetch import safe_get_page_content

urls = ["https://company.com/sustainability", "https://broken-site.com"]

for url in urls:
    content = safe_get_page_content(url)
    if content:
        print(f"Retrieved {len(content)} chars from {url}")
    else:
        print(f"Failed to retrieve content from {url}")
```

The crawler module ensures efficient, respectful, and high-quality web content acquisition for sustainability analysis.
