"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/sidebar";
import { ChartCard } from "@/components/piechart";
import { ExpandedChart } from "@/components/expanded-chart";
import { ApiService } from "@/services/api";
import { Company } from "@/types/company";
import { calculateChartData } from "@/utils/chartUtils";
import { dashboardConfig } from "@/config/dashboard";

interface ExpandedChartData {
  title: string;
  percentage: string;
  data: {
    labels: string[];
    values: number[];
    colors: string[];
  };
  question?: string;
  weight?: string;
  companies?: any;
}

export default function ComparePage() {
  const router = useRouter();
  const [companyData, setCompanyData] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedChart, setExpandedChart] = useState<ExpandedChartData | null>(null);

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        setLoading(true);
        const companies = await ApiService.getCompanies();
        setCompanyData(companies);
        setError(null);
      } catch (err) {
        setError('Failed to load company data');
        console.error('Error fetching companies:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCompanies();
  }, []);

  const handleExpandChart = (chartData: ExpandedChartData) => {
    setExpandedChart(chartData);
  };

  const handleCloseExpandedChart = () => {
    setExpandedChart(null);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-white">
        <Sidebar />
        <div className="flex-1 p-6 flex items-center justify-center">
          <div className="text-lg">Loading company data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen bg-white">
        <Sidebar />
        <div className="flex-1 p-6 flex items-center justify-center">
          <div className="text-lg text-red-600">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-white">
      <Sidebar />
      <div className="flex-1 p-6">
        <div className="mb-6">
          <h1 className="text-[36px] font-['Figtree'] font-normal text-black leading-[150%] tracking-[-0.684px]">
            Company Comparison
          </h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {dashboardConfig.map((item) => {
            const chartData = calculateChartData(companyData, item.metric);
            return (
              <ChartCard
                key={item.id}
                title={item.title}
                subtitle={`${companyData.length} ${item.subtitle}`}
                percentage={chartData.percentage}
                data={{
                  labels: chartData.labels,
                  values: chartData.values,
                  colors: chartData.colors,
                }}
                question={item.question}
                weight={item.weight}
                companies={chartData.companies}
                onExpand={() => handleExpandChart({
                  title: item.title,
                  percentage: chartData.percentage,
                  data: {
                    labels: chartData.labels,
                    values: chartData.values,
                    colors: chartData.colors,
                  },
                  question: item.question,
                  weight: item.weight,
                  companies: chartData.companies,
                })}
              />
            );
          })}
        </div>
        {expandedChart && (
          <ExpandedChart
            {...expandedChart}
            onClose={handleCloseExpandedChart}
          />
        )}
      </div>
    </div>
  );
}
