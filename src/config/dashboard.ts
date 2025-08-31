import { DashboardItem } from '../types/company';

export const dashboardConfig: DashboardItem[] = [
  {
    id: 1,
    title: "CNG Fleet Presence",
    subtitle: "companies",
    question: "Does the company currently operate any CNG vehicles?",
    weight: "10%",
    metric: "cngFleetPresence"
  },
  {
    id: 2,
    title: "CNG Fleet Size",
    subtitle: "companies",
    question: "What is the size of the company's CNG fleet?",
    weight: "25%",
    metric: "cngFleetSize"
  },
  {
    id: 3,
    title: "Emission Reporting",
    subtitle: "companies",
    question: "Does the company report on emissions or environmental impact?",
    weight: "10%",
    metric: "emissionReporting"
  },
  {
    id: 4,
    title: "Emission Reduction Goals",
    subtitle: "companies",
    question: "Does the company have emission reduction goals?",
    weight: "15%",
    metric: "emissionReductionGoals"
  },
  {
    id: 5,
    title: "Alternative Fuels Mentioned",
    subtitle: "companies",
    question: "Does the company mention alternative fuels in their reports?",
    weight: "15%",
    metric: "alternativeFuels"
  },
  {
    id: 6,
    title: "Clean Energy Partnerships",
    subtitle: "companies",
    question: "Does the company have partnerships with clean energy providers?",
    weight: "15%",
    metric: "cleanEnergyPartnerships"
  },
  {
    id: 7,
    title: "Regulatory Pressure or Market Type",
    subtitle: "companies",
    question: "Is the company subject to regulatory pressure for clean energy?",
    weight: "10%",
    metric: "regulatoryPressure"
  },
]; 