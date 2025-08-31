# FastAPI Backend Server

A FastAPI-based backend server for the Chevron-SQ project with RESTful capabilities and CORS support for frontend integration.

## 📋 Prerequisites

- Python 3.8+ (tested with Python 3.12)
- pip (Python package installer)

## 🚀 Quick Start

### 1. Navigate to Backend Directory
```bash
cd fastAPI_backend
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note for Windows Users**: If you encounter issues with `asyncpg` installation, see the [Troubleshooting](#troubleshooting) section below.

### 3. Configure Environment Variables

**Important**: The `.env` file must be located in the **project root directory** (not in the `fastAPI_backend` folder).

```bash
# Create .env file in the PROJECT ROOT (one level up from fastAPI_backend)
cd ..  # Go to project root if you're in fastAPI_backend
cp backend/.env.example .env
```

Edit the `.env` file in the root directory and add your API keys:

```env
# Required API keys for scraper functionality
GOOGLE_CSE_API_KEY=your_google_custom_search_api_key
GOOGLE_CSE_ID=your_google_custom_search_engine_id
OPENAI_API_KEY=your_openai_api_key

# Database configuration (if using PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost/dbname

# Email service configuration (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**Reference**: See `backend/.env.example` for a complete template with all available configuration options.

### 4. Run the Server
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start and be accessible at:
- **API Base URL**: `http://localhost:8000`
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## 📚 API Documentation

Once the server is running, you can explore the API using the automatically generated documentation:

- **Swagger UI**: Visit `http://localhost:8000/docs` for an interactive API explorer
- **ReDoc**: Visit `http://localhost:8000/redoc` for alternative documentation format

## 🛣️ Available API Routes

### 🔍 **Search Routes** (`/api/search`)
**Main functionality for company analysis and scraper integration**

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/search/companies` | GET | **Primary endpoint** - Analyze company sustainability using AI scraper | `q` (query string) - Company name |
| `/api/search/company/exists/{company_name}` | GET | **Check if company exists** - Verify if company is already in database | `company_name` (path parameter) |
| `/api/search/save-company` | POST | Save scraper results to database | JSON body with scraper data |
| `/api/search/test-scraper/{company_name}` | GET | Test scraper integration and imports | `company_name` (path parameter) |
| `/api/search/company/{company_id}` | DELETE | Delete company and all related data (cascade delete) | `company_id` (path parameter) |
| `/api/search/company/by-name/{company_name}` | DELETE | Delete company by name and all related data (cascade delete) | `company_name` (path parameter) |

**Debug/Development Endpoints:**

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/search/debug/companies` | GET | List all companies in database with basic info | None |
| `/api/search/debug/company/{company_id}` | GET | Get detailed company data including all summaries | `company_id` (path parameter) |

### 📊 **Dashboard Routes** (`/api/dashboard`)
**Data for dashboard visualizations and analytics**

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/dashboard/companies` | GET | Get all companies with sustainability metrics | Array of company data objects |
| `/api/dashboard/emissions/{company_name}` | GET | Get emission data and goals for specific company | Emission goals and timeline data |

### 💾 **Saved Reports Routes** (`/api/saved-reports`)
**Manage saved company analysis reports**

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/saved-reports/` | GET | Get all saved company reports with scores | Array of saved report objects |

### 🏢 **Company Routes** (`/api/companies`)
**Basic company CRUD operations**

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/companies/` | GET | List all companies | None |
| `/api/companies/{company_id}` | GET | Get specific company details | `company_id` (path parameter) |
| `/api/companies/` | POST | Create new company | JSON body with company data |
| `/api/companies/{company_id}` | PUT | Update company information | `company_id` + JSON body |
| `/api/companies/{company_id}` | DELETE | Delete company | `company_id` (path parameter) |

### 📋 **Company Card Routes** (`/api/company-cards`)
**Simplified company card data for UI components**

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/company-cards/` | GET | Get company card data for UI | Array of company card objects |

### 🌱 **Sustainability Routes** (`/api/sustainability`)
**Sustainability metrics and environmental data**

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/sustainability/metrics` | GET | Get sustainability metrics | Company-specific filters |
| `/api/sustainability/scores` | GET | Get sustainability scores | Scoring parameters |

### ⛽ **CNG Routes** (`/api/cng`)
**Compressed Natural Gas fleet and infrastructure data**

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/cng/fleet-data` | GET | Get CNG fleet information | Fleet size and infrastructure data |

### 📝 **Summary Routes** (`/api/summaries`)
**AI-generated summaries and reports**

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/summaries/` | GET | Get company summaries | Query parameters for filtering |
| `/api/summaries/generate` | POST | Generate new AI summary | JSON body with generation parameters |

## 🧪 How to Test the API Routes

### **Method 1: Interactive Swagger UI (Recommended)**

1. **Start the server**:
   ```bash
   cd fastAPI_backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open Swagger UI**: Visit `http://localhost:8000/docs`

3. **Test the main functionality**:
   - Expand **"Search"** section
   - Click on **`GET /api/search/companies`**
   - Click **"Try it out"**
   - Enter a company name (e.g., "Amazon", "FedEx", "UPS")
   - Click **"Execute"**
   - View the structured response with overall sustainability score

### **Method 2: cURL Commands**

```bash
# Test main scraper endpoint
curl -X GET "http://localhost:8000/api/search/companies?q=Amazon" \
     -H "accept: application/json"

# Check if company exists in database
curl -X GET "http://localhost:8000/api/search/company/exists/Amazon" \
     -H "accept: application/json"

# Test scraper integration
curl -X GET "http://localhost:8000/api/search/test-scraper/Amazon" \
     -H "accept: application/json"

# Get dashboard companies
curl -X GET "http://localhost:8000/api/dashboard/companies" \
     -H "accept: application/json"

# Get saved reports
curl -X GET "http://localhost:8000/api/saved-reports/" \
     -H "accept: application/json"

# Delete company by ID (cascade delete all related data)
curl -X DELETE "http://localhost:8000/api/search/company/1" \
     -H "accept: application/json"

# Delete company by name (case-insensitive)
curl -X DELETE "http://localhost:8000/api/search/company/by-name/FedEx" \
     -H "accept: application/json"

# Debug: List all companies in database
curl -X GET "http://localhost:8000/api/search/debug/companies" \
     -H "accept: application/json"

# Debug: Get detailed company data
curl -X GET "http://localhost:8000/api/search/debug/company/1" \
     -H "accept: application/json"
```

### **Method 3: Python Requests**

```python
import requests

# Test main scraper functionality
response = requests.get("http://localhost:8000/api/search/companies?q=Amazon")
data = response.json()

print(f"Overall Score: {data['overall_score']['overall_score_percentage']}%")
print(f"Company: {data['company']['company_name']}")
print(f"Metrics: {data['sustainability_metrics']}")
```

### **Method 4: Frontend Integration**

```javascript
// Example fetch call from React frontend
const searchCompany = async (companyName) => {
  try {
    const response = await fetch(`http://localhost:8000/api/search/companies?q=${companyName}`);
    const data = await response.json();
    
    console.log('Overall Score:', data.overall_score.overall_score_percentage);
    console.log('Sustainability Metrics:', data.sustainability_metrics);
    return data;
  } catch (error) {
    console.error('API Error:', error);
  }
};
```

## 🎯 **Key Testing Scenarios**

### **Scenario 1: Basic Company Analysis**
- **Endpoint**: `/api/search/companies?q=Amazon`
- **Expected**: Structured JSON with overall score, metrics, sources, summaries
- **Test Data**: Try "Amazon", "FedEx", "UPS", "Walmart"

### **Scenario 2: Company Existence Check**
- **Endpoint**: `/api/search/company/exists/Amazon`
- **Expected**: `{"exists": true, "company": {...}}` if found, 404 if not found
- **Purpose**: Verify if company is already in database before analysis
- **Test Data**: Try existing companies like "FedEx" and new companies

### **Scenario 3: Integration Testing**  
- **Endpoint**: `/api/search/test-scraper/TestCompany`
- **Expected**: Success message with import confirmation
- **Purpose**: Verify scraper service integration

### **Scenario 4: Dashboard Data**
- **Endpoint**: `/api/dashboard/companies`
- **Expected**: Array of company objects with sustainability data
- **Purpose**: Test dashboard visualization data

### **Scenario 5: Error Handling**
- **Test**: Empty query `/api/search/companies?q=`
- **Expected**: 400 error with "Search query cannot be empty"
- **Test**: Invalid company `/api/search/companies?q=NonExistentCompany`
- **Expected**: Structured response with empty/minimal data

### **Scenario 6: Company Deletion (Cascade Delete)**
- **Endpoint**: `/api/search/company/by-name/FedEx`
- **Method**: DELETE
- **Expected**: Success message with deleted company info
- **Purpose**: Clean up database entries with incorrect scores
- **Note**: Automatically deletes all related data:
  - SustainabilityMetric record
  - All MetricSource entries
  - All Summary records (Fleet, Emissions, AltFuels, CleanEnergyPartners, RegulatoryPressure)

**Typical Delete Workflow:**
1. List companies: `GET /api/search/debug/companies`
2. Find company to delete by name or ID
3. Delete by name: `DELETE /api/search/company/by-name/CompanyName` 
4. Or delete by ID: `DELETE /api/search/company/123`
5. Verify deletion: `GET /api/search/debug/companies`

## ⚠️ **Important Testing Notes**

1. **API Key Requirements**: The `/api/search/companies` endpoint requires valid API keys in your `.env` file
2. **Rate Limits**: Google Custom Search API has daily limits (100 requests/day free tier)
3. **Response Time**: Initial scraper requests may take 30-60 seconds for comprehensive analysis
4. **Database State**: Some endpoints are currently in testing mode with database operations disabled

## 🏗️ Project Structure

```
fastAPI_backend/
├── main.py                 # FastAPI application entry point
├── models.py              # Database models
├── database.py            # Database configuration
├── requirements.txt       # Python dependencies
├── routers/              # API route modules
│   ├── company_routes.py
│   ├── search_routes.py
│   ├── dashboard_routes.py
│   └── ...
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables
**Critical**: The `.env` file must be in the **project root directory** for the API to function properly.

Required environment variables:
```env
GOOGLE_CSE_API_KEY=your_google_api_key      # For web search functionality
GOOGLE_CSE_ID=your_search_engine_id         # For web search functionality  
OPENAI_API_KEY=your_openai_api_key          # For AI analysis functionality
```

Optional environment variables:
```env
DATABASE_URL=postgresql://...               # Database connection
EMAIL_HOST=smtp.gmail.com                   # Email notifications
EMAIL_PORT=587                              # Email port
EMAIL_USERNAME=your_email@gmail.com         # Email username
EMAIL_PASSWORD=your_app_password            # Email password
```

**Template**: Use `backend/.env.example` as your template - copy it to the project root as `.env`.

### CORS Settings
The server is configured to accept requests from:
- `http://localhost:3000` (Frontend development server)

### Default Port
- The server runs on port `8000` by default
- Frontend is expected to run on port `3000`

## 🛠️ Development

### Running in Development Mode
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag enables auto-reload when code changes are detected.

### Running in Production Mode
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🐛 Troubleshooting

### Issue: `uvicorn: command not found`
**Solution**: Use Python module syntax:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Issue: `asyncpg` installation fails on Windows
This is a common issue with Python 3.12 on Windows. Try these solutions:

**Option 1: Install compatible version**
```bash
pip install asyncpg>=0.29.0
```

**Option 2: Use alternative PostgreSQL driver**
```bash
pip install psycopg2-binary
# Then install other dependencies
pip install fastapi uvicorn starlette pydantic click h11 typing-extensions
```

**Option 3: Install without asyncpg (if database not needed immediately)**
```bash
pip install fastapi uvicorn starlette pydantic click h11 typing-extensions
```

**Option 4: Install Visual C++ Build Tools**
1. Download Visual Studio Build Tools from Microsoft
2. Install with C++ build tools
3. Retry: `pip install -r requirements.txt`

### Issue: Port already in use
If port 8000 is already in use, change the port:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Issue: CORS errors from frontend
Ensure your frontend is running on `http://localhost:3000`, or update the CORS origins in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Missing API keys / Environment variables not found
**Symptoms**: 
- `"Missing required environment variables"` error
- `"Google Custom Search API credentials not found"` error
- Scraper functionality fails

**Solution**: Ensure `.env` file is in the correct location:
```bash
# Check current directory
pwd

# Should show project root, not fastAPI_backend
# Correct structure:
project-root/
├── .env                    # ← Environment file goes HERE
├── fastAPI_backend/        # ← Not here
├── backend/
│   └── .env.example       # ← Use this as template
└── src/
```

**Fix**:
```bash
# If you're in fastAPI_backend folder, go to project root
cd ..

# Copy the example file
cp backend/.env.example .env

# Edit with your actual API keys
nano .env  # or use your preferred editor
```

### Issue: Scraper service import errors
**Symptoms**: `"No module named 'backend'"` error when calling scraper routes

**Solution**: Ensure you're running the server from the correct directory:
```bash
# Make sure you're in the fastAPI_backend directory when running
cd fastAPI_backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server automatically handles path setup to import the backend modules.

## 📦 Dependencies

Key dependencies include:
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **Pydantic**: Data validation using Python type annotations
- **asyncpg**: Async PostgreSQL driver (optional, see troubleshooting)
- **Starlette**: Lightweight ASGI framework (FastAPI dependency)

## 🤝 Contributing

1. Make sure the server runs without errors
2. Test your changes with the interactive docs at `/docs`
3. Ensure CORS is properly configured for frontend integration
4. Update this README if you add new dependencies or change setup procedures

## 📞 Support

If you encounter issues not covered in the troubleshooting section:
1. Check the server logs for detailed error messages
2. Verify all dependencies are installed correctly
3. Ensure no other services are using port 8000
4. Try running with `--reload` flag for development debugging 