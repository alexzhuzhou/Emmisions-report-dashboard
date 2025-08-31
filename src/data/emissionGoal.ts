import { EmissionGoalData } from '../types/emission';

export const emissionGoalData: EmissionGoalData = {
  companyName: "Company A",
  targetYear: 2050,
  currentYear: 2025,
  goalDescription: "net-zero carbon emissions across its operations",
  strategy: "investing in carbon-free energy, scale solutions, and collaborate with partners to broaden their impact",
  additionalInfo: "CNG usage and focus of transport and supply chain emissions in sustainability efforts is included in their emission reduction plan and overall sustainability report",
  sources: [
    {
      title: "Amazon Sustainability Report",
      url: "https://sustainability.aboutamazon.com/2023-sustainability-report"
    },
    {
      title: "Amazon Sustainability Site",
      url: "https://sustainability.aboutamazon.com"
    }
  ],
  emissions: [
    { year: 2020, value: 45.2 },
    { year: 2021, value: 42.8 },
    // { year: 2022, value: 40.1 },
    // { year: 2023, value: 38.5 },
    // { year: 2024, value: 36.2 },
    // { year: 2025, value: 34.0 },
    // { year: 2030, value: 25.5 },
    // { year: 2035, value: 12.8 },
    // { year: 2040, value: 0 }
  ]
}; 