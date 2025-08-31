// TODO: DATABASE INTEGRATION - This interface would be enhanced for database use
export interface SavedReport {
  id: string; // TODO: DATABASE - Change to number if using auto-increment IDs, or keep string for UUIDs
  companyName: string;
  overallScore: number;
  summary: string;
  dateCreated: string; // TODO: DATABASE - Consider changing to Date type for better database compatibility
  // TODO: DATABASE - Add additional fields that would come from database:
  // createdAt?: Date;        // Database timestamp
  // updatedAt?: Date;        // Database timestamp
  // userId?: string;         // Link to user who saved the report
  // companyId?: string;      // Link to company entity in database
  // tags?: string[];         // User-defined tags for organization
  metrics: {
    cngFleetPresence: boolean;
    cngFleetSize: string | number;
    emissionReporting: boolean;
    alternativeFuels: boolean;
    cleanEnergy: boolean;
    regulatoryPressure: boolean;
    // TODO: DATABASE - Consider normalizing metrics into separate table:
    // metricsId?: string;    // Foreign key to metrics table
  };
  // TODO: DATABASE - Add optional fields for API responses:
  // _count?: {               // Prisma-style count relations
  //   bookmarks?: number;
  // };
} 