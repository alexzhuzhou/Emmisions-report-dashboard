export interface Company {
    name: string;
    cngFleetPresence: boolean;
    cngFleetSize: "50+" | "11-50" | "1-10" | "None";
    emissionReporting: boolean;
    emissionReductionGoals: "Goal with timeline" | "Goal mentioned" | "No";
    alternativeFuels: boolean;
    cleanEnergyPartnerships: boolean;
    regulatoryPressure: boolean;
  }
  
  export type MetricKey = keyof Omit<Company, 'name'>;
  
  export interface ChartData {
    labels: string[];
    values: number[];
    colors: string[];
    percentage: string;
    companies: Record<string, string[]>;
  }
  
  export interface DashboardItem {
    id: number;
    title: string;
    subtitle: string;
    question: string;
    weight: string;
    metric: MetricKey;
  } 