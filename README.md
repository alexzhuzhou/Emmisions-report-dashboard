# Chevron-SQ - Sustainability Scoring Platform

A comprehensive platform for analyzing and scoring companies' sustainability metrics, particularly focused on CNG (Compressed Natural Gas) adoption potential. The application combines intelligent web scraping, AI-powered analysis, and a modern web interface to provide detailed sustainability insights.

## 🏗️ Project Architecture

- **Frontend**: Next.js 15 with TypeScript, Tailwind CSS, and React 19
- **Backend**: FastAPI with SQLAlchemy and PostgreSQL
- **AI Scraper**: Python-based intelligent web scraping with OpenAI integration
- **Database**: PostgreSQL with comprehensive sustainability metrics schema
- **State Management**: React Context API and localStorage for client-side persistence

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v18 or higher)
- **Python** (v3.8 or higher)
- **PostgreSQL** (v12 or higher)
- **Git**

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Chevron-SQ
```

### 2. Database Setup

1. **Install PostgreSQL** and create a database:
```bash
# Create database
createdb chevron_sq_db

# Or using psql
psql -U postgres
CREATE DATABASE chevron_sq_db;
\q
```

2. **Run the database schema**:
```bash
psql -U postgres -d chevron_sq_db -f schema.sql
```

### 3. Backend Setup

#### FastAPI Backend

1. **Navigate to the FastAPI directory**:
```bash
cd fastAPI_backend
```

2. **Create and activate virtual environment**:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables** (create `.env` file):
```bash
# Database configuration
DATABASE_URL=postgresql://username:password@localhost:5432/chevron_sq_db

# OpenAI API (for AI analysis)
OPENAI_API_KEY=your_openai_api_key

# For Search Functionality
GOOGLE_CSE_ID=

# Email configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

5. **Start the FastAPI server**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at [http://localhost:8000](http://localhost:8000)
API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

#### AI Scraper Backend

1. **Navigate to the scraper directory**:
```bash
cd backend/src/scraper
```

2. **Install scraper dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers** (required for web scraping):
```bash
playwright install
```

### 4. Frontend Setup

1. **Return to project root**:
```bash
cd ../../../
```

2. **Install Node.js dependencies**:
```bash
npm install
```

3. **Start the development server**:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

## 📁 Codebase Organization

```
Chevron-SQ/
├── src/                          # Next.js frontend (App Router)
│   ├── app/                      # App router pages
│   │   ├── dashboard/           # Main dashboard with sustainability metrics
│   │   ├── home/                # Search page
│   │   ├── loading/             # Loading screen during analysis
│   │   ├── saved/               # Saved reports management
│   │   └── layout.tsx           # Root layout with navigation
│   ├── components/              # React components
│   │   ├── ui/                  # Reusable UI components
│   │   ├── dashboard-cards.tsx  # Dashboard metric cards
│   │   ├── emissiongoal.tsx     # Emission goals visualization
│   │   ├── piechart.tsx         # Chart components
│   │   └── protected-sidebar.tsx # Navigation sidebar
│   ├── hooks/                   # Custom React hooks
│   │   ├── useNavigationWarning.ts # Navigation warning logic
│   │   └── useClearTabsOnRouteChange.ts # Tab management
│   ├── services/                # API service layer
│   │   └── api.ts               # API client functions
│   ├── types/                   # TypeScript type definitions
│   ├── utils/                   # Utility functions
│   └── config/                  # Configuration files
├── fastAPI_backend/             # FastAPI backend
│   ├── routers/                 # API route handlers
│   │   ├── company_routes.py    # Company CRUD operations
│   │   ├── search_routes.py     # Search and analysis endpoints
│   │   ├── saved_reports.py     # Saved reports management
│   │   └── dashboard_routes.py  # Dashboard data endpoints
│   ├── models.py                # SQLAlchemy database models
│   ├── database.py              # Database configuration
│   ├── config.py                # Backend configuration
│   ├── main.py                  # FastAPI application entry
│   └── requirements.txt         # Python dependencies
├── backend/                     # AI Scraper system
│   └── src/
│       ├── scraper/             # Core scraping logic
│       │   ├── main_ai_scraper.py # Main scraper orchestration
│       │   ├── ai_criteria_analyzer.py # AI analysis logic
│       │   ├── crawler/         # Web crawling components
│       │   ├── analysis/        # Data analysis modules
│       │   └── utils/           # Scraper utilities
│       ├── search/              # Google search integration
│       └── EmailService/        # Email notifications
├── public/                      # Static assets
│   └── truck-icon.svg          # Application favicon
└── schema.sql                  # Database schema
```

## 🔄 Application Flow & Logic

### 1. User Journey

1. **Search Initiation** (`/home` page)
   - User enters company name
   - Frontend calls `/api/search/companies` endpoint
   - Backend checks database first (cache-first approach)

2. **Data Retrieval Logic**
   - **Cache Hit**: If company exists in database, return formatted data
   - **Cache Miss**: If not found, trigger AI scraper analysis
   - **Loading State**: User sees loading screen with progress indicators

3. **AI Analysis Process** (when cache miss)
   - Google search for company sustainability information
   - Web scraping of relevant pages and PDFs
   - AI-powered analysis using OpenAI
   - Extraction of sustainability metrics
   - Generation of overall CNG adoption score

4. **Results Display** (`/dashboard` page)
   - Sustainability metrics visualization
   - CNG fleet analysis
   - Emission goals tracking
   - Alternative fuels assessment
   - Clean energy partnerships
   - Regulatory pressure analysis

5. **Data Persistence**
   - Results stored in localStorage temporarily
   - User can save to database or discard
   - Saved reports accessible via `/saved` page

### 2. Key Components

#### Frontend Architecture

- **App Router**: Next.js 15 App Router for file-based routing
- **Client Components**: Interactive components with `'use client'` directive
- **Server Components**: Static components for better performance
- **State Management**: Combination of React Context and localStorage
- **Navigation**: Protected routes with warning dialogs for unsaved changes

#### Backend Architecture

- **FastAPI**: Modern Python web framework with automatic API docs
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Relational database for data persistence
- **CORS**: Configured for frontend communication
- **Async/Await**: Non-blocking I/O operations

#### AI Scraper System

- **Playwright**: Browser automation for dynamic content
- **OpenAI Integration**: GPT models for intelligent analysis
- **Google Custom Search API**: Google search results
- **Trafilatura**: Web content extraction
- **PyMuPDF**: PDF processing capabilities

### 3. Database Schema

#### Core Tables

- **`Companies`**: Company information and metadata
- **`SustainabilityMetrics`**: Core sustainability metrics and CNG adoption scores
- **`MetricSources`**: Evidence sources for each metric

#### Summary Tables

- **`FleetSummary`**: CNG fleet analysis summaries
- **`EmissionsSummary`**: Emissions reporting and goals summaries
- **`AltFuelsSummary`**: Alternative fuels usage summaries
- **`CleanEnergyPartnersSummary`**: Clean energy partnerships summaries
- **`RegulatoryPressureSummary`**: Regulatory pressure analysis summaries

### 4. API Endpoints

#### Search & Analysis
- `GET /api/search/companies` - Smart company search
- `POST /api/search/save-company` - Save analysis results
- `GET /api/search/company/exists/{name}` - Check if company exists

#### Dashboard & Reports
- `GET /api/dashboard/companies` - Get all companies
- `GET /api/saved-reports/` - Get saved reports
- `DELETE /api/search/company/by-name/{name}` - Delete company

## 🛠️ Development Features

### Frontend Development
- **Hot Reload**: Automatic refresh on code changes
- **TypeScript**: Full type safety and IntelliSense
- **Tailwind CSS**: Utility-first CSS framework
- **ESLint**: Code linting and formatting
- **Turbopack**: Fast bundling for development

### Backend Development
- **Auto-reload**: Uvicorn with `--reload` flag
- **API Documentation**: Auto-generated Swagger docs
- **Type Hints**: Full Python type annotations
- **Error Handling**: Comprehensive error tracking
- **Database Migrations**: SQLAlchemy-based schema management

### AI Scraper Development
- **Modular Design**: Separate modules for different analysis types
- **Configurable**: YAML-based configuration files
- **Testable**: Unit tests for core functionality
- **Logging**: Comprehensive logging for debugging

## 🔧 Configuration

### Environment Variables

#### Frontend (`.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000
```

#### Backend (`.env`)
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/chevron_sq_db
OPENAI_API_KEY=your_openai_api_key
GOOGLE_CSE_ID=your_key
ENVIRONMENT=development
```

### Database Configuration

The application uses PostgreSQL with the following connection string format:
```
postgresql://username:password@host:port/database_name
```

## 🧪 Testing

### Frontend Testing
```bash
npm run lint          # Run ESLint
npm run build         # Build for production
```

### Backend Testing
```bash
# Navigate to backend directory
cd fastAPI_backend

## 🚀 Deployment

### Development
```bash
# Terminal 1 - Backend
cd fastAPI_backend
uvicorn main:app --reload

# Terminal 2 - Frontend
npm run dev
```


## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database exists and schema is loaded

2. **Frontend Can't Connect to Backend**
   - Verify backend is running on port 8000
   - Check CORS configuration
   - Ensure `BACKEND_URL` in `globals.ts` is correct

3. **AI Scraper Not Working**
   - Verify OpenAI API key is set
   - Check SerpAPI key for Google search
   - Ensure Playwright browsers are installed

4. **Port Already in Use**
   - Change ports in configuration files
   - Kill existing processes using the ports

### Getting Help

- Review the console logs for error messages
- Verify all environment variables are set correctly
- Ensure all dependencies are installed
- please reach out to myurkovsky@ucdavis.edu for post-handoff troubleshooting
