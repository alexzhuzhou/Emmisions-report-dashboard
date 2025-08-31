// Environment-based configuration
const isDev = process.env.NODE_ENV === 'development';

// Base URLs
export const BACKEND_URL = isDev 
  ? 'http://127.0.0.1:8000' 
  : (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000');

export const FRONTEND_URL = isDev 
  ? 'http://localhost:3000' 
  : (process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000');

// Dashboard URL (used in emails and redirects)
export const DASHBOARD_URL = FRONTEND_URL;

// API Endpoints (optional - for better organization)
export const API_ENDPOINTS = {
  COMPANIES: `${BACKEND_URL}/api/dashboard/companies`,
  SEARCH: `${BACKEND_URL}/api/search/companies`,
  SAVE_COMPANY: `${BACKEND_URL}/api/search/save-company`,
  COMPANY_EXISTS: (name: string) => `${BACKEND_URL}/api/search/company/exists/${encodeURIComponent(name)}`,
  DELETE_COMPANY: (name: string) => `${BACKEND_URL}/api/search/company/by-name/${encodeURIComponent(name)}`,
} as const;

// CORS configuration for backend
export const CORS_ORIGINS = [FRONTEND_URL, 'http://localhost:3000', 'http://127.0.0.1:3000'];