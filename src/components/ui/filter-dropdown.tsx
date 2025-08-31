"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import Button from "@/components/ui/button";

interface FilterDropdownProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyFilters: (filters: FilterState) => void;
  className?: string;
}

interface FilterState {
  sustainabilityScore: {
    min: number;
    max: number;
  };
  metrics: string[];
}

export function FilterDropdown({ 
  isOpen, 
  onClose, 
  onApplyFilters,
  className 
}: FilterDropdownProps) {
  const [filters, setFilters] = useState<FilterState>({
    sustainabilityScore: { min: 0, max: 100 },
    metrics: []
  });

  // Separate state for input display values
  const [displayValues, setDisplayValues] = useState({
    min: "0",
    max: "100"
  });

  const sustainabilityMetrics = [
    "CNG Fleet Presence",
    "Emission Reporting", 
    "Alternative Fuels",
    "Clean Energy",
    "Regulatory Pressure"
  ];

  const handleScoreChange = (type: 'min' | 'max', value: string) => {
    // Update display value immediately
    setDisplayValues(prev => ({
      ...prev,
      [type]: value
    }));

    // Handle empty string
    if (value === '') {
      return; // Don't update filters yet, wait for valid input
    }

    const numValue = parseInt(value);
    if (isNaN(numValue)) return; // Don't update if invalid number
    
    const clampedValue = Math.max(0, Math.min(100, numValue));
    
    setFilters(prev => {
      const newScore = { ...prev.sustainabilityScore };
      
      if (type === 'min') {
        newScore.min = Math.min(clampedValue, prev.sustainabilityScore.max);
      } else {
        newScore.max = Math.max(clampedValue, prev.sustainabilityScore.min);
      }
      
      return {
        ...prev,
        sustainabilityScore: newScore
      };
    });
  };

  const handleSliderChange = (type: 'min' | 'max', value: string) => {
    const numValue = parseInt(value);
    
    // Update display values
    setDisplayValues(prev => ({
      ...prev,
      [type]: value
    }));
    
    setFilters(prev => {
      const newScore = { ...prev.sustainabilityScore };
      
      if (type === 'min') {
        newScore.min = Math.min(numValue, prev.sustainabilityScore.max);
      } else {
        newScore.max = Math.max(numValue, prev.sustainabilityScore.min);
      }
      
      return {
        ...prev,
        sustainabilityScore: newScore
      };
    });
  };

  const toggleMetric = (metric: string) => {
    setFilters(prev => ({
      ...prev,
      metrics: prev.metrics.includes(metric)
        ? prev.metrics.filter(m => m !== metric)
        : [...prev.metrics, metric]
    }));
  };

  const handleApplyFilters = () => {
    onApplyFilters(filters);
    onClose();
  };

  const handleClearFilters = () => {
    setFilters({
      sustainabilityScore: { min: 0, max: 100 },
      metrics: []
    });
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 z-40"
        onClick={onClose}
      />
      
      {/* Dropdown */}
      <div className={cn(
        "absolute right-0 top-full mt-1 w-96 bg-white border border-gray-200 rounded-2xl shadow-lg z-50 p-6",
        className
      )}>
        {/* Sustainability Score Section */}
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Sustainability Score</h3>
          
          {/* Slider */}
          <div className="mb-4">
            <div className="relative">
              {/* Track background */}
              <div className="w-full h-3 bg-gray-200 rounded-full relative">
                {/* Active range */}
                <div 
                  className="absolute h-3 bg-[#2BA2D4] rounded-full"
                  style={{
                    left: `${filters.sustainabilityScore.min}%`,
                    width: `${filters.sustainabilityScore.max - filters.sustainabilityScore.min}%`
                  }}
                />
              </div>
              
              {/* Min range input */}
              <input
                type="range"
                min="0"
                max="100"
                value={filters.sustainabilityScore.min}
                onChange={(e) => handleSliderChange('min', e.target.value)}
                className="absolute top-0 w-full h-3 bg-transparent appearance-none cursor-pointer slider-thumb pointer-events-none"
                style={{ pointerEvents: 'auto' }}
              />
              
              {/* Max range input */}
              <input
                type="range"
                min="0"
                max="100"
                value={filters.sustainabilityScore.max}
                onChange={(e) => handleSliderChange('max', e.target.value)}
                className="absolute top-0 w-full h-3 bg-transparent appearance-none cursor-pointer slider-thumb pointer-events-none"
                style={{ pointerEvents: 'auto' }}
              />
              
              <div className="flex justify-between text-sm text-gray-500 mt-2">
                <span>Minimum</span>
                <span>Maximum</span>
              </div>
            </div>
          </div>

          {/* Min/Max Inputs */}
          <div className="flex justify-between">
            <div className="w-16">
              <Input
                type="number"
                min="0"
                max="100"
                value={displayValues.min}
                onChange={(e) => handleScoreChange('min', e.target.value)}
                className="text-center h-6 rounded-lg border-gray-300 text-base px-1 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />
            </div>
            <div className="w-16">
              <Input
                type="number"
                min="0"
                max="100"
                value={displayValues.max}
                onChange={(e) => handleScoreChange('max', e.target.value)}
                className="text-center h-6 rounded-lg border-gray-300 text-base px-1 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />
            </div>
          </div>
        </div>

        {/* Sustainability Metrics Section */}
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Sustainability Metrics</h3>
          
          <div className="flex flex-wrap gap-2">
            {sustainabilityMetrics.map((metric) => (
              <button
                key={metric}
                onClick={() => toggleMetric(metric)}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-normal transition-all duration-200 border",
                  filters.metrics.includes(metric)
                    ? "bg-[#2BA2D4] text-white border-[#2BA2D4]"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                )}
              >
                {metric}
              </button>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            onClick={handleApplyFilters}
            className="flex-1 bg-[#2BA2D4] hover:bg-[#2BA2D4]/90 text-white h-12 rounded-lg font-medium"
          >
            Apply filters
          </Button>
          
        </div>
      </div>

      {/* Custom slider styles */}
      <style jsx>{`
        .slider-thumb::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: white;
          border: 2px solid #2BA2D4;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          position: relative;
          z-index: 10;
        }
        
        .slider-thumb::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: white;
          border: 2px solid #2BA2D4;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          position: relative;
          z-index: 10;
        }
        
        .slider-thumb::-webkit-slider-track {
          background: transparent;
        }
        
        .slider-thumb::-moz-range-track {
          background: transparent;
        }
      `}</style>
    </>
  );
} 