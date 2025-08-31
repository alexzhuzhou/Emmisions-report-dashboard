"use client";

import React from "react";
import { SavedReport } from "@/types/savedReport";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface SavedReportCardProps {
  report: SavedReport;
  className?: string;
}

export function SavedReportCard({ 
  report, 
  className 
}: SavedReportCardProps) {
  const renderMetricIcon = (value: boolean | string | number, metricType?: string) => {
    // Special handling for CNG Fleet Size
    if (metricType === 'cngFleetSize') {
      if (value === "None" || value === "0" || value === 0) {
        return (
          <span className="text-red-500 font-semibold text-sm">
            0
          </span>
        );
      } else {
        return (
          <span className="text-green-600 font-semibold text-sm">
            {value}
          </span>
        );
      }
    }

    if (typeof value === 'boolean') {
      return value ? (
        <div className="w-4 h-4 border-2 border-green-500 rounded-full flex items-center justify-center bg-white">
          <span className="material-symbols-outlined text-green-500" style={{ fontSize: '12px', fontVariationSettings: "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 16" }}>check</span>
        </div>
      ) : (
        <div className="w-4 h-4 border-2 border-red-500 rounded-full flex items-center justify-center bg-white">
          <span className="material-symbols-outlined text-red-500" style={{ fontSize: '12px', fontVariationSettings: "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 16" }}>close</span>
        </div>
      );
    }
    return (
      <span className="text-green-600 font-semibold text-sm">
        {value}
      </span>
    );
  };

  return (
    <Card className={cn(
      "bg-white border border-gray-200 rounded-2xl p-4 w-full",
      className
    )}>
      <CardContent className="p-0">
        {/* Header with company name */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            {report.companyName}
          </h2>
        </div>

        {/* Main content area - Overall Score and Summary */}
        <div className="flex gap-4 mb-6">
          {/* Left side - Compact Overall Score */}
          <div className="flex-shrink-0">
            <div className="bg-white rounded-xl border border-gray-200 pt-3 pb-2 px-3 flex flex-col items-center h-32 w-48">
              {/* Header */}
              <div className="mb-2">
                <h3 className="text-sm font-semibold text-gray-800 text-center">Overall Score</h3>
              </div>

              {/* Very Compact Semicircular Progress */}
              <div className="relative">
                <svg width={160} height={90} viewBox="0 0 160 90" className="overflow-visible">
                  {/* Background semicircle - no roundedness */}
                  <path
                    d="M 20 70 A 60 60 0 0 1 140 70"
                    fill="none"
                    stroke="#E5E7EB"
                    strokeWidth={20}
                    strokeLinecap="butt"
                  />
                  {/* Progress semicircle - no roundedness, reflects actual score */}
                  <path
                    d="M 20 70 A 60 60 0 0 1 140 70"
                    fill="none"
                    stroke="#2BA2D4"
                    strokeWidth={20}
                    strokeLinecap="butt"
                    strokeDasharray={188.49}
                    strokeDashoffset={188.49 - (report.overallScore / 100) * 188.49}
                    style={{
                      transition: 'stroke-dashoffset 0.5s ease-in-out',
                    }}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-semibold leading-tight text-gray-900 mt-6">
                    {report.overallScore}<span className="text-2xl">%</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right side - Summary */}
          <div className="flex-1">
            <p className="text-gray-700 text-sm leading-relaxed">
              {report.summary}
            </p>
          </div>
        </div>

        {/* Bottom section - Overview with metrics */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 mb-3">
            Overview
          </h3>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center">
              <div className="text-xs font-medium text-gray-700 mb-1">
                CNG Fleet Presence
              </div>
              <div className="flex justify-center">
                {renderMetricIcon(report.metrics.cngFleetPresence)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs font-medium text-gray-700 mb-1">
                CNG Fleet Size
              </div>
              <div className="flex justify-center">
                {renderMetricIcon(report.metrics.cngFleetSize, 'cngFleetSize')}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs font-medium text-gray-700 mb-1">
                Emission Reporting
              </div>
              <div className="flex justify-center">
                {renderMetricIcon(report.metrics.emissionReporting)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs font-medium text-gray-700 mb-1">
                Alternative Fuels
              </div>
              <div className="flex justify-center">
                {renderMetricIcon(report.metrics.alternativeFuels)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs font-medium text-gray-700 mb-1">
                Clean Energy
              </div>
              <div className="flex justify-center">
                {renderMetricIcon(report.metrics.cleanEnergy)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs font-medium text-gray-700 mb-1">
                Regulatory Pressure
              </div>
              <div className="flex justify-center">
                {renderMetricIcon(report.metrics.regulatoryPressure)}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 