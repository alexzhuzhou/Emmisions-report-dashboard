import { InfoIcon, ExternalLink } from "lucide-react";
import React, { useState, useRef, useEffect, JSX } from "react";
import { Card, CardContent } from "./card";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { EmissionGoalData, SourceLink } from '../types/emission';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const SourcesTooltip = ({ sources, isVisible, onMouseEnter, onMouseLeave }: { 
  sources: SourceLink[], 
  isVisible: boolean,
  onMouseEnter: () => void,
  onMouseLeave: () => void
}) => {
  if (!isVisible) return null;

  return (
    <div 
      className="absolute top-8 left-0 z-50 bg-white rounded-[12px] border border-[#c6cbcd] shadow-lg p-4 min-w-[280px] max-w-[400px]"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <h4 className="text-[#2f2f2f] font-normal mb-3" style={{ fontFamily: 'Figtree', fontSize: 'clamp(14px, 1.2vw, 16px)', lineHeight: 'clamp(16px, 1.5vw, 20px)' }}>
        Sources:
      </h4>
      <div className="flex flex-col gap-3">
        {sources.map((source, index) => (
          <div key={index} className="flex items-start gap-2">
            <img
              src="/Frame.svg"
              alt="Link"
              className="w-4 h-4 flex-shrink-0 mt-1"
            />
            <a 
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#2f2f2f] font-normal underline hover:no-underline break-words"
              style={{ fontFamily: 'Figtree', fontSize: 'clamp(12px, 1.1vw, 14px)', lineHeight: 'clamp(16px, 1.4vw, 18px)' }}
            >
              {source.title}
            </a>
          </div>
        ))}
      </div>
    </div>
  );
};

interface EmissionGoalProps {
  companyData?: any;
}

export const EmissionGoal = ({ companyData }: EmissionGoalProps): JSX.Element => {
  const [showSources, setShowSources] = useState(false);
  const hideTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Extract emission data from company data instead of API call
  const extractEmissionData = (): EmissionGoalData | null => {
    if (!companyData?.scraper_results) return null;

    const scraperResults = companyData.scraper_results;
    const companyName = companyData.company_name || scraperResults.company?.company_name || "Unknown Company";
    
    // Get emissions summary data
    const emissionsSummary = scraperResults.summaries?.emissions_summary;
    
    if (!emissionsSummary) return null;

    // Extract sources from metric_sources for emission goals
    const sources: SourceLink[] = [];
    if (scraperResults.metric_sources && Array.isArray(scraperResults.metric_sources)) {
      // Look for emission-related sources with broader matching
      const emissionSources = scraperResults.metric_sources.filter((source: any) => {
        const metricNames = Array.isArray(source.metric_name) ? source.metric_name : [source.metric_name];
        return metricNames.some((name: string) => {
          const metricName = name?.toLowerCase() || '';
          return metricName.includes('emission') || metricName === 'emission_goals' || metricName === 'emission_reporting';
        });
      });
      
      emissionSources.forEach((source: any) => {
        if (source.source_url && source.source_url !== "#") {
          // Use contribution_text as title if available, otherwise use a formatted metric name
          const title = source.contribution_text || 
                       `${companyName} - Emissions Information`;
          sources.push({
            title: title,
            url: source.source_url
          });
        }
      });
    }

    // If no specific emission sources found, add any available sources
    if (sources.length === 0 && scraperResults.metric_sources && Array.isArray(scraperResults.metric_sources)) {
      scraperResults.metric_sources.slice(0, 3).forEach((source: any) => {
        if (source.source_url && source.source_url !== "#") {
          const title = source.contribution_text || 
                       `${companyName} - Sustainability Information`;
          sources.push({
            title: title,
            url: source.source_url
          });
        }
      });
    }

    // Add company website as fallback source
    if (scraperResults.company?.website_url) {
      sources.push({
        title: `${companyName} Sustainability Information`,
        url: scraperResults.company.website_url
      });
    }

    // Create emission data points if we have current and target emissions
    const emissions = [];
    if (emissionsSummary.current_emissions && emissionsSummary.target_emissions && emissionsSummary.target_year) {
      emissions.push(
        { year: 2024, value: emissionsSummary.current_emissions },
        { year: emissionsSummary.target_year, value: emissionsSummary.target_emissions }
      );
    }

    return {
      companyName: companyName,
      targetYear: emissionsSummary.target_year || 2050,
      currentYear: 2025,
      goalDescription: emissionsSummary.emissions_goals_summary || "No specific emission goals found",
      strategy: emissionsSummary.emissions_summary || "No specific strategy outlined",
      additionalInfo: "Analysis based on publicly available sustainability information and reports.",
      sources: sources,
      emissions: emissions
    };
  };

  const emissionData = extractEmissionData();

  const handleMouseEnter = () => {
    if (hideTimeoutRef.current) {
      clearTimeout(hideTimeoutRef.current);
      hideTimeoutRef.current = null;
    }
    setShowSources(true);
  };

  const handleMouseLeave = () => {
    hideTimeoutRef.current = setTimeout(() => {
      setShowSources(false);
      hideTimeoutRef.current = null;
    }, 50);
  };

  if (!emissionData) {
    return (
      <Card className="flex flex-col w-full max-w-[621px] items-start gap-5 p-10 bg-white rounded-[15px] border border-solid border-[#c6cbcd]">
        <div className="flex items-center justify-center w-full h-32">
          <div className="text-gray-500" style={{ fontSize: 'clamp(16px, 1.3vw, 18px)' }}>No emission data available</div>
        </div>
      </Card>
    );
  }

  const currentYear = new Date().getFullYear();
  const hasRealEmissionData = emissionData.emissions.length > 0;
  
  const chartData = {
    labels: [currentYear.toString(), '2040'],
    datasets: [
      {
        label: 'Carbon Emissions (millions of tons CO₂)',
        data: [50, 25], // Hardcoded values: current year higher, target year lower
        backgroundColor: '#2ba2d4',
        borderColor: '#2ba2d4',
        borderWidth: 1,
        borderRadius: 2,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            if (hasRealEmissionData) {
              return `${context.parsed.y} million tons CO₂`;
            } else {
              return ['Visual estimate of', 'carbon emissions'];
            }
          }
        },
        bodyFont: {
          size: Math.max(10, Math.min(12, window.innerWidth * 0.008))
        },
        padding: 8,
        cornerRadius: 4
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Carbon Emissions',
          font: {
            size: Math.max(12, Math.min(14, window.innerWidth * 0.01)),
          },
          color: '#2f2f2f',
        },
        ticks: {
          color: '#2f2f2f',
          font: {
            size: Math.max(10, Math.min(12, window.innerWidth * 0.008)),
          },
          display: false,
        },
        grid: {
          display: false,
        },
        border: {
          width: 1.2,
          color: '#2f2f2f',
        },
      },
      x: {
        title: {
          display: false,
          text: 'Year',
          font: {
            size: Math.max(12, Math.min(14, window.innerWidth * 0.01)),
          },
          color: '#2f2f2f',
        },
        ticks: {
          color: '#2f2f2f',
          font: {
            size: Math.max(10, Math.min(12, window.innerWidth * 0.008)),
          },
        },
        grid: {
          display: false,
        },
        border: {
          width: 1.2,
          color: '#2f2f2f',
        },
      },
    },
  };

  return (
    <Card className="flex flex-col w-full max-w-[1500px] items-start gap-5 ps-5 pt-6 bg-white rounded-[15px] border border-solid border-[#c6cbcd]">
      <div className="flex items-center gap-2.5">
        <h2 className="font-semibold text-[#2f2f2f]" style={{ fontSize: 'clamp(2.5rem, 2vw, 4rem)' }}>
          Target Emission Goals
        </h2>
        <div className="relative">
          <InfoIcon 
            size={Math.max(16, Math.min(20, window.innerWidth * 0.015))} 
            className="text-[#6d6d6d] cursor-pointer" 
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          />
          <SourcesTooltip 
            sources={emissionData.sources}
            isVisible={showSources}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          />
        </div>
      </div>

      <CardContent className="w-full p-0">
        <div className="relative w-full">
          <div className="float-left w-[350px] h-[350px] mr-6 mb-2">
            <Bar data={chartData} options={chartOptions} />
          </div>
          <div className="text-[#2f2f2f] text-[clamp(1rem,_1.5vw,2rem)] leading-[1.375]">
            {(() => {
              const hasGoalDescription = emissionData.goalDescription && 
                emissionData.goalDescription !== "Summary not provided." && 
                emissionData.goalDescription !== "No specific emission goals found";
              const hasTargetYear = emissionData.targetYear && emissionData.targetYear !== 2050;
              const hasStrategy = emissionData.strategy && 
                emissionData.strategy !== "Summary not provided." && 
                emissionData.strategy !== "No specific strategy outlined";
              if (hasGoalDescription && hasTargetYear) {
                return (
                  <>
                    {emissionData.companyName}&apos;s target emission goal is to achieve {emissionData.goalDescription} by {emissionData.targetYear}.
                    <br /><br />
                    {hasStrategy ? 
                      `${emissionData.companyName} plans to meet this goal by ${emissionData.strategy}` :
                      `${emissionData.companyName} has not disclosed specific strategies for achieving their emission reduction goals.`
                    }
                  </>
                );
              }
              if (hasGoalDescription && !hasTargetYear) {
                return (
                  <>
                    {emissionData.companyName}&apos;s target emission goal is to achieve {emissionData.goalDescription}, though no specific target year has been publicly disclosed.
                    <br /><br />
                    {hasStrategy ? 
                      `${emissionData.companyName} plans to meet this goal by ${emissionData.strategy}` :
                      `${emissionData.companyName} has not disclosed specific strategies for achieving their emission reduction goals.`
                    }
                  </>
                );
              }
              if (!hasGoalDescription && hasTargetYear) {
                return (
                  <>
                    {emissionData.companyName} has indicated a target year of {emissionData.targetYear} for their emission reduction efforts, but specific emission reduction goals have not been publicly disclosed.
                    <br /><br />
                    {hasStrategy ? 
                      `${emissionData.companyName} plans to achieve their targets by ${emissionData.strategy}` :
                      `${emissionData.companyName} has not disclosed specific strategies for achieving their emission reduction targets.`
                    }
                  </>
                );
              }
              if (!hasGoalDescription && !hasTargetYear && hasStrategy) {
                return (
                  <>
                    {emissionData.companyName} has not publicly disclosed specific emission reduction goals or target years.
                    <br /><br />
                    However, the company has outlined some environmental initiatives: {emissionData.strategy}
                  </>
                );
              }
              return (
                <>
                  {emissionData.companyName} has not publicly disclosed specific emission reduction goals, target years, or detailed strategies for reducing their carbon footprint.
                  <br /><br />
                  This analysis is based on publicly available information, and the company may have internal sustainability initiatives that have not been publicly reported.
                </>
              );
            })()}
          </div>
          <div className="clear-both"></div>
        </div>
      </CardContent>

      <p className="text-[#2f2f2f] font-normal break-words pb-5" style={{ fontFamily: 'Figtree', fontSize: 'clamp(12px, 1.2vw, 16px)', lineHeight: 'clamp(16px, 1.5vw, 20px)' }}>
        {(() => {
          const hasAdditionalInfo = emissionData.additionalInfo && 
            emissionData.additionalInfo !== "Analysis based on publicly available sustainability information and reports." &&
            emissionData.additionalInfo.trim().length > 0;
          
          if (hasAdditionalInfo) {
            return emissionData.additionalInfo;
          }
          
          // Check if we have any meaningful emission data
          const hasAnyEmissionData = (emissionData.goalDescription && 
            emissionData.goalDescription !== "Summary not provided." && 
            emissionData.goalDescription !== "No specific emission goals found") ||
            (emissionData.strategy && 
            emissionData.strategy !== "Summary not provided." && 
            emissionData.strategy !== "No specific strategy outlined") ||
            (emissionData.targetYear && emissionData.targetYear !== 2050);
          
          if (hasAnyEmissionData) {
            return "This analysis is based on publicly available sustainability information and reports. Companies may have additional internal initiatives or more recent commitments not reflected in this data.";
          } else {
            return "No specific emission-related information was found in publicly available sources. This company may have sustainability initiatives that are not publicly disclosed, or may be in the process of developing emission reduction strategies.";
          }
        })()}
      </p>
    </Card>
  );
};
