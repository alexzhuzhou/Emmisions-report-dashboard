# Utils Module - Helper Functions

This directory contains utility functions used throughout the scraper system. These are pure functions that handle specific data processing tasks without side effects.

## Overview

The `utils/` module provides three main categories of helper functions:

- **PDF Processing** (`pdf.py`) - Extract and process PDF documents
- **HTML Processing** (`html.py`) - Clean and extract text from web pages
- **String Processing** (`strings.py`) - Text normalization and filename handling

## Files & Functions

### `pdf.py` - PDF Processing and Chunking

**Purpose**: Handle PDF download, text extraction, and intelligent text chunking for AI analysis

#### Key Functions

##### `extract_pdf_content(pdf_url: str, company_name: str) -> str`

**What it does**: Downloads a PDF from a URL and extracts clean text content
**Parameters**:

- `pdf_url`: URL of the PDF to download
- `company_name`: Company name for validation (ensures PDF belongs to target company)

**Returns**: Clean text content of the PDF, or empty string if extraction fails

**Example usage**:

```python
from backend.src.scraper.utils.pdf import extract_pdf_content

text = extract_pdf_content(
    "https://company.com/sustainability-report.pdf",
    "Company Name"
)
print(f"Extracted {len(text)} characters")
```

**What it handles**:

- Downloads PDF files safely with timeout protection
- Validates PDF ownership (prevents analyzing third-party PDFs about the company)
- Extracts text using multiple fallback methods
- Returns clean, readable text suitable for AI analysis

##### `intelligent_chunk_text(text: str, max_chunk_size: int) -> List[str]`

**What it does**: Splits large text into smaller, meaningful chunks for efficient AI processing
**Parameters**:

- `text`: Large text content to split
- `max_chunk_size`: Maximum characters per chunk

**Returns**: List of text chunks, each under the size limit

**Why this is needed**:

- AI models have token limits (e.g., GPT-4 has ~8k token limit)
- Large PDFs can be 100k+ characters
- Simple truncation loses important information
- Intelligent chunking preserves context and finds complete sentences

**Example usage**:

```python
from backend.src.scraper.utils.pdf import intelligent_chunk_text

large_text = "..." # 50,000 character PDF content
chunks = intelligent_chunk_text(large_text, 8000)
print(f"Split into {len(chunks)} chunks")
# Each chunk is ~8000 characters and ends at sentence boundaries
```

**How it works**:

1. First tries to split at paragraph boundaries (`\n\n`)
2. If paragraphs are too large, splits at sentence boundaries
3. If sentences are too large, splits at word boundaries
4. Preserves context by ensuring clean breaks

---

### `html.py` - HTML Processing

**Purpose**: Extract clean, readable text from HTML web pages

#### Key Functions

##### `html_to_clean_text(html_content: str) -> str`

**What it does**: Converts HTML content to clean, readable text suitable for AI analysis
**Parameters**:

- `html_content`: Raw HTML from a web page

**Returns**: Clean text with HTML tags removed and formatting normalized

**Example usage**:

```python
from backend.src.scraper.utils.html import html_to_clean_text

html = "<h1>Company News</h1><p>We operate 5,000 trucks...</p>"
clean_text = html_to_clean_text(html)
print(clean_text)
# Output: "Company News\n\nWe operate 5,000 trucks..."
```

**What it does**:

- Removes all HTML tags (`<div>`, `<span>`, etc.)
- Preserves meaningful structure (headers, paragraphs)
- Removes navigation menus, footers, and other noise
- Normalizes whitespace and line breaks
- Handles special characters and encoding issues

**Why this is important**:

- Raw HTML contains lots of markup that confuses AI analysis
- Navigation menus and ads add irrelevant content
- Clean text focuses AI analysis on actual content
- Proper formatting helps AI understand document structure

---

### `strings.py` - String Processing

**Purpose**: Text normalization and safe filename generation

#### Key Functions

##### `normalize_text(text: str) -> str`

**What it does**: Standardizes text format for consistent processing
**Parameters**:

- `text`: Raw text that may have inconsistent formatting

**Returns**: Normalized text with consistent formatting

**Example usage**:

```python
from backend.src.scraper.utils.strings import normalize_text

messy_text = "  Company   operates\n\n5,000\tvehicles  "
clean_text = normalize_text(messy_text)
print(clean_text)
# Output: "Company operates 5,000 vehicles"
```

**What it normalizes**:

- Removes extra whitespace and tabs
- Normalizes line breaks
- Standardizes number formatting
- Handles Unicode characters consistently
- Removes leading/trailing whitespace

##### `safe_filename_for_output_path(company_name: str, suffix: str = "") -> str`

**What it does**: Generates safe filenames for saving analysis results
**Parameters**:

- `company_name`: Company name that may contain special characters
- `suffix`: Optional suffix for the filename

**Returns**: Safe filename that works on all operating systems

**Example usage**:

```python
from backend.src.scraper.utils.strings import safe_filename_for_output_path

filename = safe_filename_for_output_path("AT&T Corp.", "_results.json")
print(filename)
# Output: "att_corp_results.json"
```

**Why this is needed**:

- Company names often contain special characters (`&`, `/`, `.`, etc.)
- These characters can break file systems or cause security issues
- Safe filenames ensure results are saved properly
- Consistent naming helps with file organization

**What it handles**:

- Removes or replaces special characters
- Converts to lowercase for consistency
- Replaces spaces with underscores
- Ensures filename length limits
- Prevents reserved filename conflicts

## When to Use Each Module

### Use `pdf.py` when:

- Downloading and extracting PDF sustainability reports
- Processing large documents that need to be split for AI analysis
- Validating that PDFs belong to the target company

### Use `html.py` when:

- Scraping web pages for sustainability information
- Converting HTML content for AI analysis
- Removing navigation and advertising content

### Use `strings.py` when:

- Normalizing text before comparison or analysis
- Generating safe filenames for output files
- Standardizing text format across different sources

## Common Patterns

### PDF Processing Pipeline

```python
# 1. Extract PDF content
pdf_text = extract_pdf_content(pdf_url, company_name)

# 2. Normalize the text
clean_text = normalize_text(pdf_text)

# 3. Split into chunks if needed
if len(clean_text) > 8000:
    chunks = intelligent_chunk_text(clean_text, 8000)
else:
    chunks = [clean_text]

# 4. Process each chunk
for chunk in chunks:
    # Send to AI for analysis
    results = analyze_with_ai(chunk)
```

### Web Scraping Pipeline

```python
# 1. Get HTML from web page
html_content = fetch_web_page(url)

# 2. Extract clean text
clean_text = html_to_clean_text(html_content)

# 3. Normalize for analysis
normalized_text = normalize_text(clean_text)

# 4. Analyze with AI
results = analyze_with_ai(normalized_text)
```

### File Output Pipeline

```python
# 1. Generate safe filename
filename = safe_filename_for_output_path(company_name, "_sustainability.json")

# 2. Save results
with open(filename, 'w') as f:
    json.dump(results, f)
```

## Error Handling

All utility functions include robust error handling:

- **PDF extraction**: Handles corrupted PDFs, network timeouts, access denied
- **HTML processing**: Handles malformed HTML, encoding issues, empty content
- **String processing**: Handles Unicode issues, extremely long strings, None values

If any function encounters an error, it:

1. Logs the error with details
2. Returns a sensible default (empty string, empty list, etc.)
3. Doesn't crash the entire analysis process

## Performance Considerations

- **PDF processing**: Large PDFs are processed in chunks to manage memory usage
- **HTML processing**: Uses efficient parsing libraries (BeautifulSoup)
- **String processing**: Optimized for large text documents
- **Caching**: Results are not cached (intentionally) to ensure fresh data

These utilities are designed to be reliable, efficient, and maintainable for long-term use in the sustainability analysis system.
