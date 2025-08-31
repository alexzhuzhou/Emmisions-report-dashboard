"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

import Header from "@/components/ui/header";
import Button from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { EmissionGoal } from "@/components/emissiongoal";
import { Card } from "@/components/card";
import { ApiService } from "@/services/api";
import { OverallScoreCard, SustainabilityOverviewCard, CompanySummaryCard } from "@/components/dashboard-cards";
import { BACKEND_URL } from "globals";
import { useSaved } from '../SavedContext';

export default function SavedCompanyDetailPage() {
  const params = useParams();  
  const router = useRouter();
  const { setCurrentTabHandler } = useSaved();
  const [showGenericModal, setShowGenericModal] = useState(false);
  const [genericModalTitle, setGenericModalTitle] = useState("");
  const [genericModalContent, setGenericModalContent] = useState<React.ReactNode>(null);
  const [companyData, setCompanyData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const companyName = Array.isArray(params.company) ? params.company[0] : params.company;

  // Set currentTab to company name when page loads
  useEffect(() => {
    if (companyName) {
      // Decode the URL-encoded company name to match the name in openTabs
      const decodedCompanyName = decodeURIComponent(companyName);
      setCurrentTabHandler(decodedCompanyName);
    }
  }, [companyName, setCurrentTabHandler]);

  const scoreCriteria = [
    { label: 'CNG Fleet Presence', value: '10%' },
    { label: 'CNG Fleet Size', value: '25%' },
    { label: 'Emission Reporting', value: '10%' },
    { label: 'Emission Reduction Goals', value: '15%' },
    { label: 'Alternative Fuels Mentioned', value: '15%' },
    { label: 'Clean Energy Partnerships or CNG Infrastructure Announcements', value: '15%' },
    { label: 'Regulatory Pressure or Market Type', value: '10%' },
  ];

  useEffect(() => {
    const fetchCompanyData = async () => {
      if (!companyName) {
        setError("No company name provided");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Use the existing search route that returns data in dashboard format
        const response = await fetch(`${BACKEND_URL}/api/search/companies?q=${encodeURIComponent(companyName)}`);
        
        if (!response.ok) {
          throw new Error(`Company '${companyName}' not found`);
        }

        const data = await response.json();
        
        // Transform the backend data to match the dashboard's expected structure
        const transformedData = {
          company_name: data.company?.company_name || companyName,
          from_database: true, // This is always true for saved companies
          scraper_results: {
            company: data.company,
            sustainability_metrics: data.sustainability_metrics,
            summaries: data.summaries,
            overall_score: data.overall_score,
            metric_sources: data.metric_sources
          }
        };
        setCompanyData(transformedData);
      } catch (err) {
        console.error('Error fetching company data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load company data');
      } finally {
        setLoading(false);
      }
    };

    fetchCompanyData();
  }, [companyName]);

  const handleSave = async () => {
    if (!companyData) return;

    setSaving(true);
    setSaveMessage(null);
    
    try {
      // For saved companies, we'll remove them from the database
      const result = await ApiService.deleteCompanyFromDatabase(companyData.company_name);
      if (result.success) {
        setSaveMessage('Company removed from saved reports successfully!');
        // Navigate back to saved reports after a short delay
        setTimeout(() => {
          router.push('/saved');
        }, 2000);
      }
    } catch (error) {
      console.error('Delete error:', error);
      if (error instanceof Error) {
        setSaveMessage(`Failed to remove company: ${error.message}`);
      } else {
        setSaveMessage('Failed to remove company. Please try again.');
      }
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMessage(null), 5000);
    }
  };

  const getSafeValue = (value: any, defaultValue: string = "Not Found") => {
    if (value === null || value === undefined || value === "" || value === false) {
      return defaultValue;
    }
    return String(value);
  };

  const handleExport = () => {
    if (!companyData) return;
    
    // Prepare data in column format
    const exportData = [
      ["Field", "Value"],
      ["Company Name", companyData.company_name],
      ["Analysis Date", new Date().toISOString().split('T')[0]],
      ["Overall Score", getSafeValue(calculateScore(), "Not Available") + "%"],
      ["CNG Fleet Presence", getSafeValue(getMetricValue('owns_cng_fleet'), "Not Found")],
      ["CNG Fleet Size", getSafeValue(getMetricValue('cng_fleet_size_actual') || getMetricValue('cng_fleet_size_range'), "Not Found")],
      ["Total Fleet Size", getSafeValue(getMetricValue('total_fleet_size'), "Not Found")],
      ["Emission Reporting", getSafeValue(getMetricValue('emission_report'), "Not Found")],
      ["Emission Reduction Goals", getSafeValue(getMetricValue('emission_goals'), "Not Found")],
      ["Alternative Fuels", getSafeValue(getMetricValue('alt_fuels'), "Not Found")],
      ["Clean Energy Partnerships", getSafeValue(getMetricValue('clean_energy_partners'), "Not Found")],
      ["Regulatory Pressure", getSafeValue(getMetricValue('regulatory_pressure'), "Not Found")],
      ["CSO LinkedIn URL", getSafeValue(companyData.scraper_results?.company?.cso_linkedin_url, "Not Found")],
      ["CSO Name", getSafeValue(companyData.scraper_results?.company?.cso_name, "Not Found")],
      ["Company Website", getSafeValue(companyData.scraper_results?.company?.company_website, "Not Found")],
      ["Company Industry", getSafeValue(companyData.scraper_results?.company?.company_industry, "Not Found")],
      ["Company Size", getSafeValue(companyData.scraper_results?.company?.company_size, "Not Found")],
      ["Fleet Summary", getSafeValue(getSummaryText('fleet'), "Not Available")],
      ["Emissions Summary", getSafeValue(getSummaryText('emissions'), "Not Available")],
      ["Alternative Fuels Summary", getSafeValue(getSummaryText('alt_fuels'), "Not Available")],
      ["Clean Energy Partnerships Summary", getSafeValue(getSummaryText('clean_energy'), "Not Available")],
      ["Regulatory Pressure Summary", getSafeValue(getSummaryText('regulatory'), "Not Available")],
      ["Company Summary", getSafeValue(getCompanySummary(), "Not Available")],
      ["Sources", getSafeValue(companyData.scraper_results?.metric_sources?.map((s: any) => s.source_url).join('; '), "Not Available")]
    ];
    
    // Convert to CSV format
    const csvContent = exportData.map(row => 
      row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
    ).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${companyData.company_name.replace(/\s+/g, '_')}_sustainability_report.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const calculateScore = () => {
    if (!companyData?.scraper_results) return 0;
    
    // Handle both old and new formats
    if (companyData.scraper_results.evidence_found) {
      // Old format with evidence_found
      const evidence = companyData.scraper_results.evidence_found;
      const foundCriteria = Object.values(evidence).filter((item: any) => item.found).length;
      const totalCriteria = 8; // Total sustainability criteria
      return Math.round((foundCriteria / totalCriteria) * 100);
    } else if (companyData.scraper_results.overall_score?.overall_score_percentage) {
      // New structured format with overall_score
      return Math.round(companyData.scraper_results.overall_score.overall_score_percentage);
    } else if (companyData.scraper_results.sustainability_metrics) {
      // New format - calculate from sustainability_metrics
      const metrics = companyData.scraper_results.sustainability_metrics;
      let foundCount = 0;
      let totalCount = 0;
      
      // Count found metrics (non-null and non-false values)
      Object.entries(metrics).forEach(([key, value]) => {
        totalCount++;
        if (value !== null && value !== false && value !== 0) {
          foundCount++;
        }
      });
      
      return totalCount > 0 ? Math.round((foundCount / totalCount) * 100) : 0;
    }
    
    return 0;
  };

  const getMetricValue = (key: string) => {
    if (!companyData?.scraper_results) return null;
    
    // Handle both old and new formats
    if (companyData.scraper_results.sustainability_metrics) {
      return companyData.scraper_results.sustainability_metrics[key];
    } else if (companyData.scraper_results.evidence_found) {
      const evidence = companyData.scraper_results.evidence_found;
      // Map old format to new format
      const mapping: Record<string, string> = {
        'owns_cng_fleet': 'cng_fleet',
        'emission_report': 'emission_reporting',
        'alt_fuels': 'alt_fuels',
        'clean_energy_partners': 'clean_energy_partner',
        'regulatory_pressure': 'regulatory'
      };
      const oldKey = mapping[key] || key;
      return evidence[oldKey]?.found || false;
    }
    
    return null;
  };

  const getSummaryText = (summaryType: string) => {
    if (!companyData?.scraper_results?.summaries) return 'No summary available';
    
    const summaries = companyData.scraper_results.summaries;
    
    switch (summaryType) {
      case 'fleet':
        return summaries.fleet_summary?.summary_text || 'Fleet information not available';
      case 'emissions':
        return summaries.emissions_summary?.emissions_summary || 'Emissions information not available';
      case 'alt_fuels':
        return summaries.alt_fuels_summary?.summary_text || 'Alternative fuels information not available';
      case 'clean_energy':
        return summaries.clean_energy_partners_summary?.summary_text || 'Clean energy partnerships information not available';
      case 'regulatory':
        return summaries.regulatory_pressure_summary?.summary_text || 'Regulatory pressure information not available';
      default:
        return 'Information not available';
    }
  };

  const getCompanySummary = () => {
    if (!companyData?.scraper_results) return 'Company analysis not available';
    
    if (companyData.scraper_results.company?.company_summary) {
      return companyData.scraper_results.company.company_summary;
    }
    
    // Fallback: generate summary from available data
    const hasFleet = getMetricValue('owns_cng_fleet');
    const fleetSize = getMetricValue('cng_fleet_size_actual') || getMetricValue('cng_fleet_size_range');
    const hasReporting = getMetricValue('emission_report');
    const hasGoals = getMetricValue('emission_goals');
    
    let summary = `${companyData.company_name} `;
    
    if (hasReporting) {
      summary += 'has published sustainability reports. ';
    }
    
    if (hasGoals) {
      summary += 'The company has set emission reduction goals. ';
    }
    
    if (hasFleet) {
      summary += `The company operates CNG vehicles`;
      if (fleetSize) {
        summary += ` with a fleet size of ${fleetSize}`;
      }
      summary += '. ';
    }
    
    return summary || 'Company sustainability analysis is in progress.';
  };

  const getMetricSources = () => {
    if (!companyData?.scraper_results?.metric_sources) return 'Sources not available';
    
    const sources = companyData.scraper_results.metric_sources;
    if (sources.length === 0) return 'No sources available';
    
    return (
      <div className="text-[#2f2f2f] text-[16px] font-normal leading-[20px] mb-3" style={{ fontFamily: 'Figtree' }}>
        <h4 className="text-[#2f2f2f] text-[16px] font-medium leading-[20px] mb-3" style={{ fontFamily: 'Figtree' }}>
          Sources:
        </h4>
        <div className="flex flex-col gap-3">
          {sources.map((source: any, index: number) => (
            <div key={index} className="flex items-center gap-2">
              <img
                src="/Frame.svg"
                alt="Link"
                className="w-4 h-4 flex-shrink-0"
              />
              <a 
                href={source.source_url} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-[#2f2f2f] text-[14px] font-normal leading-[18px] underline hover:no-underline transition-all duration-200"
                style={{ fontFamily: 'Figtree' }}
                title={source.source_url}
              >
                {source.contribution_text || source.source_url}
              </a>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const openOverallScoreModal = () => {
    setGenericModalTitle("Overall Score");
    setGenericModalContent(
      <>
        <p className='text-[#6d6d6d] mb-3'>How is the score calculated?</p>
        <p className='text-[#2f2f2f] font-semibold mb-4'>Score criteria and their weights are outlined as follows:</p>
        <div className="space-y-2">
          {scoreCriteria.map((item, index) => (
            <div key={index} className="flex justify-between text-[#2f2f2f]">
              <span>{item.label}</span>
              <span>{item.value}</span>
            </div>
          ))}
        </div>
      </>
    );
    setShowGenericModal(true);
  };

  const openMetricModal = (title: string, content: React.ReactNode) => {
    setGenericModalTitle(title);
    setGenericModalContent(content);
    setShowGenericModal(true);
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Loading company data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <Button onClick={() => router.push('/saved')}>
            Return to Saved Reports
          </Button>
        </div>
      </div>
    );
  }

  if (!companyData) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">No company data found</p>
          <Button onClick={() => router.push('/saved')}>
            Return to Saved Reports
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 px-12 pt-6">
        <Header
          companyName={companyData.company_name}
          actions={
            <>
              {saveMessage && (
                <div className={`mr-4 px-3 py-1 rounded text-sm ${
                  saveMessage.includes('success') 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {saveMessage}
                </div>
              )}
              <Button
                onClick={handleSave}
                disabled={saving}
                className={`${
                  companyData.from_database 
                    ? 'bg-[#1e3a8a] hover:bg-red-600' 
                    : 'bg-[#2BA2D4] hover:bg-[#000000]'
                } text-white transition-colors duration-200`}>
                <span className="material-symbols-outlined text-white">
                  bookmark
                </span>
                {saving ? (companyData.from_database ? 'Removing...' : 'Saving...') : 
                 companyData.from_database ? 'Saved' : 'Save to Database'}
              </Button>
              <Button onClick={handleExport} variant="outline" className="!bg-[#F5F7FA] !border-[#2ba2d4] !text-[#2ba2d4] hover:!bg-[#0b2d71] cursor-pointer">
                <span className="material-symbols-outlined text-[#2BA2D4]">
                  download
                </span>
                Export
              </Button>
            </>
          }
        />

        <div className="mt-8 flex flex-col gap-6">
          <div className="flex flex-row gap-6">
            
            {/* Overall Score Card */}
            <OverallScoreCard 
              score={calculateScore()} 
              onScoreClick={openOverallScoreModal}
            />
            
            {/* Sustainability Overview Card */}
            <SustainabilityOverviewCard
              fleetSize={getMetricValue('cng_fleet_size_actual') || '0'}
              cngFleetPresence={!!getMetricValue('owns_cng_fleet')}
              regulatoryPressure={!!getMetricValue('regulatory_pressure')}
              alternativeFuels={!!getMetricValue('alt_fuels')}
              emissionsReporting={!!getMetricValue('emission_report')}
              cleanEnergy={!!getMetricValue('clean_energy_partners')}
              onMetricClick={openMetricModal}
              getSummaryText={getSummaryText}
            />
            
          </div>
          
          <div className="flex flex-row gap-6">
            
            {/* Company Summary Card */}
            <CompanySummaryCard 
              companySummary={getCompanySummary()}
              sources={getMetricSources()}
            />
            
            {/* Target Emission Goal Card */}
            <div className="flex-1">
              <EmissionGoal companyData={companyData} />
            </div>
          </div>
        </div>

        {/* Generic Modal */}
        {showGenericModal && ( 
          <Modal open={showGenericModal} onClose={() => setShowGenericModal(false)} title={genericModalTitle}>
            {genericModalContent}
          </Modal>
        )}
      </div>
    );
} 