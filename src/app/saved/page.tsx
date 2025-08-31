"use client";

import React, { useState, useEffect } from "react";
import { SavedReportsBar } from "@/components/ui/saved-reports-bar";
import { SavedReportCard } from "@/components/ui/saved-report-card";
import { SavedReport } from "@/types/savedReport";
import { BACKEND_URL } from "globals";
import { useSaved } from './SavedContext';
import { useRouter } from "next/navigation";

interface FilterState {
  sustainabilityScore: {
    min: number;
    max: number;
  };
  metrics: string[];
}

export default function SavedReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [filteredReports, setFilteredReports] = useState<SavedReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { openTabs, setOpenTabsHandler, setCurrentTabHandler } = useSaved();

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/saved-reports/`);
        if (!response.ok) {
          throw new Error('Failed to fetch reports');
        }
        const data = await response.json();
        setReports(data);
        setFilteredReports(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    fetchReports();
  }, []);

  const handleSearch = (searchTerm: string) => {
    if (!searchTerm.trim()) {
      setFilteredReports(reports);
      return;
    }

    const filtered = reports.filter(report =>
      report.companyName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.summary.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredReports(filtered);
  };

  const handleFilter = (filters: FilterState) => {
    let filtered = [...reports];

    // Filter by sustainability score range
    filtered = filtered.filter(report => 
      report.overallScore >= filters.sustainabilityScore.min && 
      report.overallScore <= filters.sustainabilityScore.max
    );

    // Filter by metrics (if any metrics are selected)
    if (filters.metrics.length > 0) {
      filtered = filtered.filter(report => {
        return filters.metrics.some(metric => {
          switch (metric) {
            case "CNG Fleet Presence":
              return report.metrics.cngFleetPresence;
            case "CNG Fleet Size":
              return report.metrics.cngFleetSize;
            case "Emission Reporting":
              return report.metrics.emissionReporting;
            case "Alternative Fuels":
              return report.metrics.alternativeFuels;
            case "Clean Energy":
              return report.metrics.cleanEnergy;
            case "Regulatory Pressure":
              return report.metrics.regulatoryPressure;
            default:
              return false;
          }
        });
      });
    }

    setFilteredReports(filtered);
  };

  const handleApplySort = (selectedSorts: string[]) => {
    let sorted = [...filteredReports];

    // Apply multiple sort criteria in order
    selectedSorts.forEach(sortBy => {
      switch (sortBy) {
        case "Sustainability Score":
          sorted.sort((a, b) => b.overallScore - a.overallScore);
          break;
        case "Companies: A to Z":
          sorted.sort((a, b) => a.companyName.localeCompare(b.companyName));
          break;
        default:
          break;
      }
    });

    // If no sorts are selected, reset to original order
    if (selectedSorts.length === 0) {
      sorted = [...reports];
    }

    setFilteredReports(sorted);
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-500">Loading reports...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-red-500">Error: {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1">
        <SavedReportsBar
          onSearch={handleSearch}
          onFilter={handleFilter}
          onApplySort={handleApplySort}
        />
        
        <div className="p-6">
          {filteredReports.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-500 text-lg mb-2">No saved reports found</div>
              <div className="text-gray-400 text-sm">
                Try adjusting your search or filter criteria
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 ">
              {filteredReports.map((report) => (
                <div onClick={() => {
                  if (!openTabs.includes(report.companyName)) {
                    setOpenTabsHandler([...openTabs, report.companyName]);
                  }
                  setCurrentTabHandler(report.companyName);
                  router.push(`/saved/${report.companyName}`)
                }} key={report.id}>
                  <SavedReportCard
                    report={report}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
  );
}
