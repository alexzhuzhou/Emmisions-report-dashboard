# Google Search Module

A Python module for searching company-related news articles using Google Custom Search API. This module is designed to help find sustainability and environmental news about companies.

## Setup

1. **Install Required Packages**
```bash
pip install requests python-dotenv
```

2. **Set Up Google Custom Search API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Custom Search API
   - Create API credentials
   - Create a Custom Search Engine at [Google Programmable Search](https://programmablesearchengine.google.com/)

3. **Environment Variables**
   Create a `.env` file in your project root with:
   ```
   GOOGLE_CSE_API_KEY=your_api_key_here
   GOOGLE_CSE_ID=your_cse_id_here
   ```

## Usage

### Basic Search
```python
from google_search import search_google

# Simple search for a company
links = search_google("Chevron")
print(f"Found {len(links)} links about Chevron's sustainability efforts")
```

### Multiple Custom Queries
```python
from google_search import search_google

company = "Chevron"
queries = [
    f'"{company}" renewable energy projects',
    f'"{company}" carbon capture technology',
    f'"{company}" environmental initiatives'
]

# Search with multiple custom queries
links = search_google(company, queries=queries)
```

### Excluding Terms
```python
from google_search import search_google

# Search but exclude certain terms
exclude_terms = ["job", "career", "employment"]
links = search_google(
    "Chevron",
    exclude_terms=exclude_terms
)
```

### Getting Limited Results
```python
from google_search import get_urls

# Get just the top 5 most relevant links
top_links = get_urls("Chevron", max_results=5)
```

### Sustainability Scorecard Search
The module includes a specialized function for sustainability scorecard research that searches across multiple criteria:

```python
from google_search import get_company_sustainability_data

# Get sustainability data organized by criterion
sustainability_data = get_company_sustainability_data("Chevron")

# Access links for a specific criterion
cng_fleet_links = sustainability_data["cng_fleet_presence"]
print(f"Found {len(cng_fleet_links)} links about CNG fleet presence")

# Access all unique links across all criteria
all_links = sustainability_data["all_unique_links"]
print(f"Found {len(all_links)} unique links total")
```

The function searches across 7 sustainability criteria:
1. CNG Fleet Presence
2. CNG Fleet Size
3. Emission Reporting
4. Emission Reduction Goals
5. Alternative Fuels
6. Clean Energy Partnerships
7. Regulatory Pressure

#### Deduplication
Links are automatically deduplicated across criteria. Each link appears only in its first/most relevant category, preventing the same URL from appearing in multiple criteria.

#### Controlling API Usage
```python
# Reduce API calls by limiting pages per query (default: 2)
sustainability_data = get_company_sustainability_data("Chevron", max_pages=1)

# Get more comprehensive results (costs more API calls)
comprehensive_data = get_company_sustainability_data("Chevron", max_pages=3)
```

## Testing the Module

A test script is included to demonstrate the module's functionality:

### Running the Test Script

```bash
# Navigate to the search module directory
cd backend/src/search

# Run with a specific company name
python test_search.py "Amazon"

# Or run and enter a company name when prompted
python test_search.py
```

### What the Test Shows

The test script demonstrates:

1. **Basic search**: Shows results from a simple company sustainability search
2. **Sustainability scorecard search**: Shows categorized results for all 7 criteria
3. **Summary statistics**: Counts of links found for each criterion
4. **Sample links**: Shows example URLs from each category

### Example Output

```
=== Basic search for 'Waste Management' ===
Found 28 links
1. https://www.wm.com/us/en/inside-wm/sustainability
2. https://sustainability.wm.com/
3. https://www.wm.com/us/en/inside-wm/sustainability/sustainability-report
4. https://www.wm.com/content/dam/wm/documents/reports/sustainability/2022_WM_SustainabilityReport.pdf
5. https://www.wastemanagement.com/sustainability
... and 23 more links

=== Sustainability scorecard search for 'Waste Management' ===

SUMMARY BY CRITERION:
--------------------------------------------------
Cng Fleet Presence: 12 links
Cng Fleet Size: 8 links
Emission Reporting: 10 links
Emission Reduction Goals: 6 links
Alternative Fuels: 5 links
Energy Partnerships: 4 links
Regulatory Pressure: 3 links

Total unique links: 48

SAMPLE LINKS BY CRITERION:
--------------------------------------------------

Cng Fleet Presence:
1. https://www.wm.com/us/en/inside-wm/sustainability/operations/fleet
2. https://www.act-news.com/news/waste-management-cng-fleet/
... and 10 more links
```

### Saving API Calls During Testing

To minimize API usage while testing, the test script uses `max_pages=1`. You can modify this value in the script if you need more comprehensive results.

## API Reference

### search_google(company, queries=None, exclude_terms=None, max_pages=3)
Main search function that returns a list of unique URLs.

**Parameters:**
- `company` (str): Company name to search for
- `queries` (List[str], optional): List of custom queries to use. If None, uses default query
- `exclude_terms` (List[str], optional): Terms to exclude from search results
- `max_pages` (int): Maximum number of result pages to fetch per query (default: 3)

**Returns:**
- List[str]: List of unique URLs from search results

### get_urls(company, queries=None, max_results=5)
Helper function that returns a limited number of URLs.

**Parameters:**
- `company` (str): Company name to search for
- `queries` (List[str], optional): List of custom queries to use
- `max_results` (int): Maximum number of results to return (default: 5)

**Returns:**
- List[str]: List of URLs from search results

### get_company_sustainability_data(company_name, max_pages=2)
Comprehensive search across sustainability criteria with deduplication.

**Parameters:**
- `company_name` (str): Company name to search for
- `max_pages` (int): Maximum number of pages per query (default: 2)

**Returns:**
- Dict: Dictionary with links organized by criterion and a consolidated list of all unique links

## API Usage and Pricing

The module uses Google Custom Search API which has the following limits:
- Free tier: 100 queries per day
- Each page of results (10 results) counts as one query
- Maximum of 100 queries per second
- Maximum of 10,000 queries per day

**Cost Optimization Tips:**
1. Use `max_pages=1` if you only need the most relevant results
2. Use `get_urls()` when you only need a few results
3. Reduce `max_pages` in `get_company_sustainability_data()` to save API calls
4. Combine related terms into single queries to reduce API calls

## Error Handling

The module handles common errors:
- Invalid API credentials
- Network issues
- Rate limiting
- Invalid responses

Errors are printed to console but don't crash the program.

Please reach out to me through Slack if you have any problems running this module.