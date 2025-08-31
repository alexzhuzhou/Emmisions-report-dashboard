export interface EmissionDataPoint {
  year: number;
  value: number;
}

export interface SourceLink {
  title: string;
  url: string;
}

export interface EmissionGoalData {
  companyName: string;
  targetYear: number;
  currentYear: number;
  goalDescription: string;
  strategy: string;
  additionalInfo: string;
  sources: SourceLink[];
  emissions: EmissionDataPoint[];
} 