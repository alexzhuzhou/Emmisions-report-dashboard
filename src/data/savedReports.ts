// TODO: DATABASE INTEGRATION - This entire file would be REMOVED when using a database
// This static data would be replaced with:
// 1. API routes in /api/saved-reports/ for CRUD operations
// 2. Database models/schemas for SavedReport entity
// 3. Database queries instead of this hardcoded array

// EXAMPLE DATABASE REPLACEMENT:
// Instead of importing this file, components would call:
// - GET /api/saved-reports - to fetch all saved reports
// - POST /api/saved-reports - to create new saved report
// - PUT /api/saved-reports/:id - to update existing saved report
// - DELETE /api/saved-reports/:id - to delete saved report
// - PATCH /api/saved-reports/:id/bookmark - to toggle bookmark status

import { SavedReport } from '../types/savedReport';

export const savedReportsData: SavedReport[] = [
  {
    id: "1", // TODO: DATABASE - This would be auto-generated UUID or database ID
    companyName: "Amazon",
    overallScore: 100,
    summary: "This is a summary of Amazon. It states key points and metrics about their sustainability efforts. Here is more of the summary to fill in the text box with information.",
    dateCreated: "2024-01-15", // TODO: DATABASE - Would be timestamp from database
    metrics: {
      cngFleetPresence: true,
      cngFleetSize: "3,000",
      emissionReporting: true,
      alternativeFuels: true,
      cleanEnergy: true,
      regulatoryPressure: true,
    }
  },
  {
    id: "2", 
    companyName: "Microsoft",
    overallScore: 85,
    summary: "Microsoft has demonstrated strong commitment to sustainability through various initiatives and carbon reduction goals. The company has invested heavily in renewable energy and clean technology solutions.",
    dateCreated: "2024-01-12",
    metrics: {
      cngFleetPresence: true,
      cngFleetSize: "1,250",
      emissionReporting: true,
      alternativeFuels: false,
      cleanEnergy: true,
      regulatoryPressure: true,
    }
  },
  {
    id: "3",
    companyName: "Google",
    overallScore: 92,
    summary: "Google leads in sustainable practices with carbon neutral operations since 2007. The company continues to invest in clean energy infrastructure and environmental initiatives across all business units.",
    dateCreated: "2024-01-10",
    metrics: {
      cngFleetPresence: false,
      cngFleetSize: "None",
      emissionReporting: true,
      alternativeFuels: true,
      cleanEnergy: true,
      regulatoryPressure: false,
    }
  },
  {
    id: "4",
    companyName: "Tesla",
    overallScore: 95,
    summary: "Tesla is at the forefront of sustainable transportation and energy solutions. The company's mission centers around accelerating the world's transition to sustainable energy through innovative technology.",
    dateCreated: "2024-01-08",
    metrics: {
      cngFleetPresence: false,
      cngFleetSize: "None",
      emissionReporting: true,
      alternativeFuels: true,
      cleanEnergy: true,
      regulatoryPressure: true,
    }
  },
  {
    id: "5",
    companyName: "Walmart",
    overallScore: 85,
    summary: "This is a summary of Amazon. It states key points and metrics about their sustainability efforts. Here is more of the summary to fill in the text box with information.",
    dateCreated: "2024-01-06",
    metrics: {
      cngFleetPresence: true,
      cngFleetSize: "5",
      emissionReporting: false,
      alternativeFuels: true,
      cleanEnergy: true,
      regulatoryPressure: true,
    }
  },
  {
    id: "6",
    companyName: "Costco",
    overallScore: 55,
    summary: "This is a summary of Amazon. It states key points and metrics about their sustainability efforts. Here is more of the summary to fill in the text box with information.",
    dateCreated: "2024-01-04",
    metrics: {
      cngFleetPresence: false,
      cngFleetSize: "0",
      emissionReporting: true,
      alternativeFuels: false,
      cleanEnergy: false,
      regulatoryPressure: false,
    }
  }
]; 