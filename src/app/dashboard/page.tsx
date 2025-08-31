"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/sidebar";
import Header from "@/components/ui/header";
import Button from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { EmissionGoal } from "@/components/emissiongoal";
import { Card } from "@/components/card";
import ProtectedSidebar from "@/components/protected-sidebar";
import NavigationWarningPopup from "@/components/ui/navigation-warning-popup";
import { useNavigationWarning } from "@/hooks/useNavigationWarning";
import { ApiService } from "@/services/api";
import { OverallScoreCard, SustainabilityOverviewCard, CompanySummaryCard } from "@/components/dashboard-cards";
import { saveOrDeleteCompany } from "@/utils/companySaveUtils";

export default function Dashboard() {
  const router = useRouter();
  const [showGenericModal, setShowGenericModal] = useState(false);
  const [genericModalTitle, setGenericModalTitle] = useState("");
  const [genericModalContent, setGenericModalContent] = useState<React.ReactNode>(null);
  const [companyData, setCompanyData] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const scoreCriteria = [
    { label: 'CNG Fleet Presence', value: '10%' },
    { label: 'CNG Fleet Size', value: '25%' },
    { label: 'Emission Reporting', value: '10%' },
    { label: 'Emission Reduction Goals', value: '15%' },
    { label: 'Alternative Fuels Mentioned', value: '15%' },
    { label: 'Clean Energy Partnerships or CNG Infrastructure Announcements', value: '15%' },
    { label: 'Regulatory Pressure or Market Type', value: '10%' },
  ];

  // Navigation warning hook  // Navigation warning hook
  const {
    showWarning,
    pendingNavigation,
    interceptNavigation,
    handleSaveAndContinue,
    handleLeaveWithoutSaving,
    handleCancelNavigation
  } = useNavigationWarning(companyData);
  useEffect(() => {
    const loadAndCheckCompanyData = async () => {
      // Load company data from localStorage
      const storedData = localStorage.getItem('currentCompanyData');
      if (storedData) {
        try {
          const parsedData = JSON.parse(storedData);
          
          // Check if company exists in database
          try {
            const companyName = parsedData.company_name || parsedData.scraper_results?.company?.company_name;
            if (companyName) {
              console.log('Checking database status for:', companyName);
              const checkResult = await ApiService.checkCompanyInDatabase(companyName);
              parsedData.from_database = checkResult.exists;
              console.log('Database check result:', checkResult);
            } else {
              console.log('No company name found, setting from_database to false');
              parsedData.from_database = false;
            }
          } catch (error) {
            console.log('Could not check database status:', error);
            // Default to false if we can't check - this is safe
            parsedData.from_database = false;
          }
          
          setCompanyData(parsedData);
          // Update localStorage with the database status
          localStorage.setItem('currentCompanyData', JSON.stringify(parsedData));
        } catch (error) {
          console.error('Error parsing stored company data:', error);
          router.push('/home');
        }
      } else {
        router.push('/home');
      }
    };

    loadAndCheckCompanyData();
  }, [router]);

    const handleSave = async () => {
      await saveOrDeleteCompany({
        companyData,
        setCompanyData,
        setSaveMessage,
        setSaving,
        ApiService
      });
    };

  const handleExport = () => {
    if (!companyData) return;
    
    const exportData = {
      company: companyData.company_name,
      analysis_date: new Date().toISOString(),
      results: companyData.scraper_results
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${companyData.company_name.replace(/\s+/g, '_')}_sustainability_report.json`;
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

  if (!companyData) {
    return (
      <div className="flex min-h-screen bg-white">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-gray-600 mb-4">No company data found</p>
            <Button onClick={() => router.push('/home')}>
              Return to Search
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-white">
      <ProtectedSidebar onNavigationAttempt={interceptNavigation} shouldIntercept={!companyData.from_database} />
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


        <div className="mt-10 flex flex-col gap-6">
          <div className=" flex flex-col xl:flex-row gap-6">
            
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
          
          <div className="flex flex-col xl:flex-row gap-6">
            
            {/* Company Summary Card */}
            <CompanySummaryCard 
              companySummary={getCompanySummary()}
              sources={getMetricSources()}
            />
            
            {/* Target Emission Goal Card */}
            <div className="flex-1 min-w-0">
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


        {/* Navigation Warning Popup */}
        <NavigationWarningPopup
          isOpen={showWarning}
          onClose={handleCancelNavigation}
          onSaveAndContinue={handleSaveAndContinue}
          onLeaveWithoutSaving={handleLeaveWithoutSaving}
        />
      </div>
    </div>
  );
}