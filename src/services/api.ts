import { Company } from '../types/company';
import { EmissionGoalData } from '../types/emission';
import { BACKEND_URL } from '../../globals';

const API_BASE_URL = BACKEND_URL;

interface SearchResult {
  company_id: number;
  company_name: string;
  company_summary?: string;
  website_url?: string;
  industry?: string;
  cng_adopt_score?: number;
}

interface SearchResponse {
  success: boolean;
  query: string;
  total_results: number;
  companies: SearchResult[];
}

interface ScraperResponse {
  // Direct structured response from backend (not wrapped)
  company?: {
    company_name: string;
    company_summary?: string;
    website_url?: string;
    industry?: string;
    cso_linkedin_url?: string;
  };
  company_name?: string; // For legacy support
  sustainability_metrics?: any;
  metric_sources?: any[];
  summaries?: any;
  overall_score?: any;
  from_database?: boolean;
  
  // Legacy wrapper format (for backward compatibility)
  success?: boolean;
  query?: string;
  scraper_results?: any;
}

export class ApiService {
  static async getCompanies(): Promise<Company[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dashboard/companies`);
      if (!response.ok) {
        throw new Error('Failed to fetch companies');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching companies:', error);
      throw error;
    }
  }

  static async getCompanyEmissions(companyName: string): Promise<EmissionGoalData> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dashboard/emissions/${encodeURIComponent(companyName)}`);
      if (!response.ok) {
        throw new Error('Failed to fetch emission data');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching emission data:', error);
      throw error;
    }
  }

  static async getCompanyCard(companyId: number) {
    try {
      const response = await fetch(`${API_BASE_URL}/company_card/${companyId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch company card');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching company card:', error);
      throw error;
    }
  }

  static async searchCompanies(query: string): Promise<ScraperResponse> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/search/companies?q=${encodeURIComponent(query)}`
      );
      if (!response.ok) {
        throw new Error('Failed to search companies');
      }
      return await response.json();
    } catch (error) {
      console.error('Error searching companies:', error);
      throw error;
    }
  }

  static async saveCompanyToDatabase(scraperData: any): Promise<{success: boolean, message: string, company_id?: number, cng_adoption_score?: number}> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/search/save-company`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(scraperData),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save company');
      }
      return await response.json();
    } catch (error) {
      console.error('Error saving company:', error);
      throw error;
    }
  }

  static async deleteCompanyFromDatabase(companyName: string): Promise<{success: boolean, message: string}> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/search/company/by-name/${encodeURIComponent(companyName)}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete company');
      }
      return await response.json();
    } catch (error) {
      console.error('Error deleting company:', error);
      throw error;
    }
  }

  static async checkCompanyInDatabase(companyName: string): Promise<{exists: boolean, company?: any}> {
    try {
      console.log(`Checking company in database: ${companyName}`);
      const url = `${API_BASE_URL}/api/search/company/exists/${encodeURIComponent(companyName)}`;
      console.log(`Making request to: ${url}`);
      
      const response = await fetch(url);
      console.log(`Response status: ${response.status} ${response.statusText}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Response data:', data);
        return { exists: data.exists, company: data.company };
      } else if (response.status === 404) {
        console.log('Company not found in database (404)');
        return { exists: false };
      } else {
        const errorText = await response.text();
        console.error(`HTTP ${response.status}: ${response.statusText}`, errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error checking company status:', error);
      // Don't throw the error, just return false to not break the flow
      return { exists: false };
    }
  }
} 