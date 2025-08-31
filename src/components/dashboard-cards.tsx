"use client";

import React, { useState, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './card';
import ProgressBar from './ui/progress-bar';

interface OverallScoreCardProps {
  score: number;
  onScoreClick: () => void;
}

export const OverallScoreCard = ({ score, onScoreClick }: OverallScoreCardProps) => {
  return (
    <Card 
      className="bg-white border-[1.2px] border-[#c6cbcd] rounded-2xl cursor-pointer w-full max-w-[800px] min-w-[300px] max-h-[900px] min-h-[300px] flex flex-col"
      onClick={onScoreClick}>
      <CardHeader className="pt-15 pb-0 px-30 flex-shrink-0">
        <CardTitle className="font-bold text-[clamp(1.5rem,_2vw,_4rem)] text-[#2f2f2f] flex items-center gap-1">
          <div className="flex-1 text-center">Overall Score</div>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0 pb-4 px-6 flex-1 flex items-center justify-center"> 
        <ProgressBar value={score}/>
      </CardContent>
    </Card>
  );
};

interface MetricRowProps {
  label: string;
  value: boolean | string | number;
  onClick?: () => void;
  type?: 'boolean' | 'number';
}

const MetricRow = ({ label, value, onClick, type = 'boolean' }: MetricRowProps) => {
  const isClickable = !!onClick;
  
  return (
    <div 
      className={`flex justify-between items-center ${isClickable ? 'cursor-pointer' : ''}`} 
      onClick={onClick}
    >
      <span className="font-medium text-4xl py-10 ps-5">{label}</span>
      {type === 'number' ? (
        <span className="font-semibold text-[#5C951A] text-5xl">{value}</span>
      ) : (
        value ? (
          <span className="material-symbols-outlined text-[#5C951A]" style={{ fontSize: 'clamp(2rem, 3vw, 3.5rem)' }}>
            check_circle
          </span>
        ) : (
          <span className="material-symbols-outlined text-[#E7122B]" style={{ fontSize: 'clamp(2rem, 3vw, 3.5rem)' }}>
            cancel
          </span>
        )
      )}
    </div>
  );
};

interface SustainabilityOverviewCardProps {
  fleetSize: string | number;
  cngFleetPresence: boolean;
  regulatoryPressure: boolean;
  alternativeFuels: boolean;
  emissionsReporting: boolean;
  cleanEnergy: boolean;
  onMetricClick: (title: string, content: React.ReactNode) => void;
  getSummaryText: (type: string) => string;
}

export const SustainabilityOverviewCard = ({
  fleetSize,
  cngFleetPresence,
  regulatoryPressure,
  alternativeFuels,
  emissionsReporting,
  cleanEnergy,
  onMetricClick,
  getSummaryText
}: SustainabilityOverviewCardProps) => {
  return (
    <Card className="bg-white border-[1.2px] border-[#c6cbcd] rounded-2xl w-full max-w-[2250px] min-w-[500px] min-h-[300px] flex-1">
      <CardHeader className="pt-8 pb-4 px-6 gap-3">
        <CardTitle className="font-bold text-[clamp(1.5rem,_2vw,_4rem)] text-[#2f2f2f] flex items-center gap-1 pt-5">
          Sustainability Overview
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-2 pb-4 px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 text-[#2f2f2f]">
          
          {/* Left Column */}
          <div className="flex flex-col gap-4">
              <MetricRow
                  label="CNG Fleet Size" 
                  value={fleetSize} 
                  type="number"
              />
            <MetricRow 
              label="CNG Fleet Presence" 
              value={cngFleetPresence}
              onClick={() => onMetricClick("CNG Fleet Presence", 
                <>
                  <p className='text-[#6d6d6d] mb-5'>
                    Does this company currently operate any compressed natural gas (CNG) vehicles?
                  </p>
                  <p className='text-[#2f2f2f]'>{getSummaryText('fleet')}</p>
                </>
              )}
            />
            <MetricRow 
              label="Regulatory Pressure" 
              value={regulatoryPressure}
              onClick={() => onMetricClick("Regulatory Pressure", 
                <>
                  <p className='text-[#6d6d6d] mb-5'>
                    Is this company operating in sectors under high regulatory pressure?
                  </p>
                  <p className='text-[#2f2f2f]'>{getSummaryText('regulatory')}</p>
                </>
              )}
            />
          </div>
          
          {/* Right Column */}
          <div className="flex flex-col gap-4">
            <MetricRow 
              label="Alternative Fuels" 
              value={alternativeFuels}
              onClick={() => onMetricClick("Alternative Fuels", 
                <>
                  <p className='text-[#6d6d6d] mb-5'>
                    Does this company mention use of biogas, biodiesel, or RNG?
                  </p>
                  <p className='text-[#2f2f2f]'>{getSummaryText('alt_fuels')}</p>
                </>
              )}
            />
            <MetricRow 
              label="Emissions Reporting" 
              value={emissionsReporting}
              onClick={() => onMetricClick("Emissions Reporting",
                <>
                  <p className='text-[#6d6d6d] mb-5'>
                    Does this company publish an emissions/sustainability report?
                  </p>
                  <p className='text-[#2f2f2f]'>{getSummaryText('emissions')}</p>
                </>
              )}
            />
            <MetricRow 
              label="Clean Energy" 
              value={cleanEnergy}
              onClick={() => onMetricClick("Clean Energy", 
                <>
                  <p className='text-[#6d6d6d] mb-5'>
                    Has this company partnered with RNG, CNG, or OEM providers?
                  </p>
                  <p className='text-[#2f2f2f]'>{getSummaryText('clean_energy')}</p>
                </>
              )}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};[]

interface CompanySummaryCardProps {
  companySummary: string;
  sources: React.ReactNode;
}

export const CompanySummaryCard = ({ companySummary, sources }: CompanySummaryCardProps) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const hideTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = () => {
    if (hideTimeoutRef.current) {
      clearTimeout(hideTimeoutRef.current);
      hideTimeoutRef.current = null;
    }
    setShowTooltip(true);
  };

  const handleMouseLeave = () => {
    hideTimeoutRef.current = setTimeout(() => {
      setShowTooltip(false);
      hideTimeoutRef.current = null;
    }, 50);
  };
  
  return (
    <Card className="bg-white border-[1.2px] border-[#c6cbcd] rounded-2xl flex-1 min-w-0">
      <CardHeader className="pb-4 pt-8 px-6 flex-row items-center">
        <CardTitle className="font-bold text-[clamp(1.5rem,_2vw,_4rem)] text-[#2f2f2f] flex items-center gap-1">
          Company Summary
          <div 
            className="relative"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            <span 
              className="material-symbols-outlined text-[#6D6D6D] text-base cursor-pointer" 
              title="Company sustainability summary"
            >
              info
            </span>
            {showTooltip && (
              <div 
                className="absolute z-50 w-80 max-w-[90vw] p-4 bg-white border border-[#c6cbcd] rounded-[12px] shadow-lg top-8 left-0"
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
              >
                {sources}
              </div>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-4 pb-8 px-6">
        <div className="text-[#2f2f2f] text-[clamp(1rem,_1.5vw,2rem)] leading-[1.375]">
          {companySummary}
        </div> 
      </CardContent>
    </Card>
  );
}; 