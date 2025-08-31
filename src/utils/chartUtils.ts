import { Company, MetricKey, ChartData } from '../types/company';

export const calculateChartData = (companies: Company[], metric: MetricKey): ChartData => {
  const totalCompanies = companies.length;
  
  switch (metric) {
    case "cngFleetPresence": {
      const yesCount = companies.filter(c => c.cngFleetPresence).length;
      const noCount = totalCompanies - yesCount;
      return {
        labels: ["Yes", "No"],
        values: [Math.round((yesCount / totalCompanies) * 100), Math.round((noCount / totalCompanies) * 100)],
        colors: ["#2ba2d4", "#c6cbcd"],
        percentage: `${Math.round((yesCount / totalCompanies) * 100)}%`,
        companies: {
          yes: companies.filter(c => c.cngFleetPresence).map(c => c.name),
          no: companies.filter(c => !c.cngFleetPresence).map(c => c.name)
        }
      };
    }
    case "cngFleetSize": {
      const size50Plus = companies.filter(c => c.cngFleetSize === "50+").length;
      const size11to50 = companies.filter(c => c.cngFleetSize === "11-50").length;
      const size1to10 = companies.filter(c => c.cngFleetSize === "1-10").length;
      const sizeNone = companies.filter(c => c.cngFleetSize === "None").length;
      const withFleet = size50Plus + size11to50 + size1to10;
      return {
        labels: ["50+", "11-50", "1-10", "None"],
        values: [
          Math.round((size50Plus / totalCompanies) * 100),
          Math.round((size11to50 / totalCompanies) * 100),
          Math.round((size1to10 / totalCompanies) * 100),
          Math.round((sizeNone / totalCompanies) * 100)
        ],
        colors: ["#2ba2d4", "#5bb3d9", "#1e3a8a", "#c6cbcd"],
        percentage: `${Math.round((withFleet / totalCompanies) * 100)}%`,
        companies: {
          "50+": companies.filter(c => c.cngFleetSize === "50+").map(c => c.name),
          "11-50": companies.filter(c => c.cngFleetSize === "11-50").map(c => c.name),
          "1-10": companies.filter(c => c.cngFleetSize === "1-10").map(c => c.name),
          "None": companies.filter(c => c.cngFleetSize === "None").map(c => c.name)
        }
      };
    }
    case "emissionReporting": {
      const yesCount = companies.filter(c => c.emissionReporting).length;
      const noCount = totalCompanies - yesCount;
      return {
        labels: ["Yes", "No"],
        values: [Math.round((yesCount / totalCompanies) * 100), Math.round((noCount / totalCompanies) * 100)],
        colors: ["#2ba2d4", "#c6cbcd"],
        percentage: `${Math.round((yesCount / totalCompanies) * 100)}%`,
        companies: {
          yes: companies.filter(c => c.emissionReporting).map(c => c.name),
          no: companies.filter(c => !c.emissionReporting).map(c => c.name)
        }
      };
    }
    case "emissionReductionGoals": {
      const goalWithTimeline = companies.filter(c => c.emissionReductionGoals === "Goal with timeline").length;
      const goalMentioned = companies.filter(c => c.emissionReductionGoals === "Goal mentioned").length;
      const noGoal = companies.filter(c => c.emissionReductionGoals === "No").length;
      const withGoals = goalWithTimeline + goalMentioned;
      return {
        labels: ["Goal with timeline", "Goal mentioned", "No"],
        values: [
          Math.round((goalWithTimeline / totalCompanies) * 100),
          Math.round((goalMentioned / totalCompanies) * 100),
          Math.round((noGoal / totalCompanies) * 100)
        ],
        colors: ["#2ba2d4", "#1e3a8a", "#c6cbcd"],
        percentage: `${Math.round((withGoals / totalCompanies) * 100)}%`,
        companies: {
          "Goal with timeline": companies.filter(c => c.emissionReductionGoals === "Goal with timeline").map(c => c.name),
          "Goal mentioned": companies.filter(c => c.emissionReductionGoals === "Goal mentioned").map(c => c.name),
          "No": companies.filter(c => c.emissionReductionGoals === "No").map(c => c.name)
        }
      };
    }
    case "alternativeFuels": {
      const yesCount = companies.filter(c => c.alternativeFuels).length;
      const noCount = totalCompanies - yesCount;
      return {
        labels: ["Yes", "No"],
        values: [Math.round((yesCount / totalCompanies) * 100), Math.round((noCount / totalCompanies) * 100)],
        colors: ["#2ba2d4", "#c6cbcd"],
        percentage: `${Math.round((yesCount / totalCompanies) * 100)}%`,
        companies: {
          yes: companies.filter(c => c.alternativeFuels).map(c => c.name),
          no: companies.filter(c => !c.alternativeFuels).map(c => c.name)
        }
      };
    }
    case "cleanEnergyPartnerships": {
      const yesCount = companies.filter(c => c.cleanEnergyPartnerships).length;
      const noCount = totalCompanies - yesCount;
      return {
        labels: ["Yes", "No"],
        values: [Math.round((yesCount / totalCompanies) * 100), Math.round((noCount / totalCompanies) * 100)],
        colors: ["#2ba2d4", "#c6cbcd"],
        percentage: `${Math.round((yesCount / totalCompanies) * 100)}%`,
        companies: {
          yes: companies.filter(c => c.cleanEnergyPartnerships).map(c => c.name),
          no: companies.filter(c => !c.cleanEnergyPartnerships).map(c => c.name)
        }
      };
    }
    case "regulatoryPressure": {
      const yesCount = companies.filter(c => c.regulatoryPressure).length;
      const noCount = totalCompanies - yesCount;
      return {
        labels: ["Yes", "No"],
        values: [Math.round((yesCount / totalCompanies) * 100), Math.round((noCount / totalCompanies) * 100)],
        colors: ["#2ba2d4", "#c6cbcd"],
        percentage: `${Math.round((yesCount / totalCompanies) * 100)}%`,
        companies: {
          yes: companies.filter(c => c.regulatoryPressure).map(c => c.name),
          no: companies.filter(c => !c.regulatoryPressure).map(c => c.name)
        }
      };
    }
    default:
      return {
        labels: [],
        values: [],
        colors: [],
        percentage: "0%",
        companies: {}
      };
  }
}; 