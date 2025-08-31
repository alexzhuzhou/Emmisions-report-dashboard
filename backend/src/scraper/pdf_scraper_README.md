# NEEDS TO BE REDONE THIS IS STILL REFERENCING SERP API(HAVE NOT USED IN WEEKS)

A Python-based tool for scraping and analyzing sustainability reports from company PDFs. This tool helps identify and analyze key sustainability metrics, particularly focusing on CNG fleet information and environmental reporting.

## Prerequisites

- Python 3.8+
- Required Python packages (install via `pip install -r requirements.txt`):


## Environment Setup

1. Create a `.env` file in the project root with the following variables:
```env
SERPAPI_API_KEY=your_serpapi_key
OPENAI_API_KEY=your_openai_key
```

## Module Usage

### 1. PDF Search (Standalone Script)

A standalone script for searching and downloading PDFs using SerpAPI.

```bash
python pdf_scraper/scripts/search_pdfs.py "Company Name" [--year YEAR] [--num-results N] [--download] [--output-dir DIR]
```

Arguments:
- `company_name`: Name of the company to search for (required)
- `--year`: Year to filter by (optional)
- `--num-results`: Number of results to return (default: 10)
- `--download`: Download the most relevant PDF (optional)
- `--output-dir`: Custom output directory for downloads (optional)

Example:
```bash
# Search only
python pdf_scraper/scripts/search_pdfs.py "Chevron" --year 2023

# Search and download
python pdf_scraper/scripts/search_pdfs.py "Chevron" --year 2023 --download --output-dir data/pdfs/chevron
```

### 2. PDF Text Extraction

#### Command Line Usage
```bash
python pdf_scraper/utils/extract_pdf.py <path_to_pdf>
```

Example:
```bash
python pdf_scraper/utils/extract_pdf.py data/pdfs/company_report.pdf
```

#### Python Import Usage
```python
from pdf_scraper.utils.extract_pdf import extract_pdf_content

# Extract text and images from PDF
text_path = extract_pdf_content(
    pdf_path="path/to/report.pdf",
    output_dir="path/to/output"
)
```

### 3. PDF Analysis

#### Command Line Usage
```bash
python pdf_scraper/utils/analyze_scorecard.py <text_path> <company_name> [--out_dir OUTPUT_DIR] [--criteria CRITERIA_LIST]
```

Arguments:
- `text_path`: Path to the extracted text file
- `company_name`: Name of the company being analyzed
- `--out_dir`: (Optional) Custom output directory for results
- `--criteria`: (Optional) Comma-separated list of criteria to analyze

Example:
```bash
python pdf_scraper/utils/analyze_scorecard.py data/extracted/company_report_extracted/extracted_text.txt "Company Name" --criteria cng_fleet,emission_goals
```

#### Python Import Usage
```python
from pdf_scraper.utils.analyze_scorecard import analyze_scorecard

# Analyze extracted text
scorecard_path = analyze_scorecard(
    text_path="path/to/extracted_text.txt",
    company_name="Company Name",
    out_dir="path/to/output"
)
```

### 4. PDF Download

#### Python Import Usage
```python
from pdf_scraper.utils.file_utils import download_pdf

# Download PDF
pdf_path = download_pdf(
    url="https://example.com/report.pdf",
    dest_folder="data/pdfs/company_name",
    filename="custom_name.pdf"  # optional
)
```

### 5. SERP API Search

#### Python Import Usage
```python
from pdf_scraper.services.serp_service import SerpService

# Initialize service
serp = SerpService()

# Search for PDFs
results = serp.search_pdfs(
    company_name="Company Name",
    num_results=10,  # optional, defaults to MAX_SEARCH_RESULTS
    year="2023"      # optional
)

# Get most relevant PDF
best_result = serp.get_most_relevant_pdf(
    company_name="Company Name",
    year="2023",     # optional
    debug_top_n=5    # optional, number of results to print
)
```

## Main Module Usage

The main module provides an end-to-end solution for finding, downloading, and analyzing sustainability reports.

### Basic Usage

```bash
python -m pdf_scraper.main "Company Name"
```

### Advanced Usage

```bash
python -m pdf_scraper.main "Company Name" --year 2023 --out_dir custom/output/path --criteria cng_fleet,emission_goals
```

### Arguments

- `company_name`: Name of the company to search for (required)
- `--year`: Year of the report (optional)
- `--out_dir`: Custom output directory (optional)
- `--criteria`: Comma-separated list of specific criteria to analyze (optional)

## Analysis Criteria

The tool analyzes the following criteria:

1. **CNG Fleet Presence** (0-1)
   - Checks if company operates CNG vehicles

2. **CNG Fleet Size** (0-3)
   - 0: None or not mentioned
   - 1: 1-10 trucks
   - 2: 11-50 trucks
   - 3: 51+ trucks

3. **Emission Reporting** (0-1)
   - Checks for sustainability/emissions reports

4. **Emission Goals** (0-2)
   - 0: No goals mentioned
   - 1: Goal mentioned without timeline
   - 2: Goal with specific timeline

5. **Alternative Fuels** (0-1)
   - Checks for mentions of biogas, biodiesel, or RNG

6. **Clean Energy Partnerships** (0-1)
   - Checks for partnerships with RNG/CNG providers

7. **Regulatory Pressure** (0-1)
   - Checks for operations in regulated sectors

## Output Structure

The tool creates the following directory structure:

```
data/
├── pdfs/
│   └── company_name/
│       └── report.pdf
├── analysis/
│   └── company_name/
│       └── scorecard.json
└── temp/
```

## Configuration

Configuration settings can be found in `pdf_scraper/utils/config.py`:

- `MAX_SEARCH_RESULTS`: Maximum number of search results (default: 10)
- `MIN_PDF_SIZE_KB`: Minimum PDF size to consider valid (default: 50KB)
- `MAX_PDF_SIZE_MB`: Maximum PDF size to download (default: 50MB)
- `PDF_STORAGE_DIR`: Directory for storing downloaded PDFs
- `TEMP_DIR`: Directory for temporary files

## Error Handling

- The tool includes comprehensive error handling for:
  - PDF download failures
  - Text extraction issues
  - API rate limits
  - Invalid file formats

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
