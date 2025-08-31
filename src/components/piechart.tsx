import React, { useState, useCallback, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./card";
import { InfoIcon } from "lucide-react";
import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

export interface ChartCardProps {
  title: string;
  subtitle: string;
  percentage: string;
  data: {
    labels: string[];
    values: number[];
    colors: string[];
  };
  question?: string;
  weight?: string;
  companies?: any;
  onExpand?: () => void;
}

export const ChartCard = ({
  title,
  subtitle,
  percentage,
  data,
  question,
  weight,
  companies,
  onExpand,
}: ChartCardProps) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [hoveredSegment, setHoveredSegment] = useState<number | null>(null);
  const [displayedPercentage, setDisplayedPercentage] = useState(percentage);
  const [percentageOpacity, setPercentageOpacity] = useState(1);
  const [segmentTooltip, setSegmentTooltip] = useState<{
    show: boolean;
    content: string[];
    x: number;
    y: number;
    label: string;
  }>({
    show: false,
    content: [],
    x: 0,
    y: 0,
    label: "",
  });

  // Calculate total values for percentage calculation
  const totalValue = useMemo(() => {
    return data.values.reduce((sum, value) => sum + value, 0);
  }, [data.values]);

  // Calculate segment percentages
  const segmentPercentages = useMemo(() => {
    return data.values.map(value => 
      totalValue > 0 ? Math.round((value / totalValue) * 100) : 0
    );
  }, [data.values, totalValue]);

  // Calculate default percentage (excluding non-categories like "No", "None", etc.)
  const defaultPercentage = useMemo(() => {
    const nonCategories = ['No', 'None', 'N/A', 'Not Available', 'Not Applicable'];
    let meaningfulTotal = 0;
    
    data.labels.forEach((label, index) => {
      // Check if this label is NOT a non-category
      const isNonCategory = nonCategories.some(nonCat => 
        label.toLowerCase().includes(nonCat.toLowerCase())
      );
      
      if (!isNonCategory) {
        meaningfulTotal += data.values[index];
      }
    });
    
    const percentage = totalValue > 0 ? Math.round((meaningfulTotal / totalValue) * 100) : 0;
    return `${percentage}%`;
  }, [data.labels, data.values, totalValue]);

  // Function to smoothly update percentage with fade effect
  const updatePercentageWithFade = useCallback((newPercentage: string) => {
    if (newPercentage !== displayedPercentage) {
      setPercentageOpacity(0);
      setTimeout(() => {
        setDisplayedPercentage(newPercentage);
        setPercentageOpacity(1);
      }, 150);
    }
  }, [displayedPercentage]);

  const chartData = useMemo(() => ({
    labels: data.labels,
    datasets: [
      {
        data: data.values,
        backgroundColor: data.colors,
        borderWidth: 0,
        hoverBorderWidth: 0,
      },
    ],
  }), [data.labels, data.values, data.colors]);

  const handleHover = useCallback((event: any, activeElements: any[]) => {
    if (activeElements.length > 0) {
      const segmentIndex = activeElements[0].index;
      const currentHovered = hoveredSegment;
      
      // Only update if the hovered segment actually changed
      if (currentHovered !== segmentIndex) {
        setHoveredSegment(segmentIndex);
        
        // Update the displayed percentage to the hovered segment's percentage
        updatePercentageWithFade(`${segmentPercentages[segmentIndex]}%`);

        // Get companies for this segment
        const label = data.labels[segmentIndex];
        let companyList: string[] = [];

        if (companies) {
          // Map label to company list
          if (label === "Yes" && companies.yes) {
            companyList = companies.yes;
          } else if (label === "No" && companies.no) {
            companyList = companies.no;
          } else if (companies[label]) {
            companyList = companies[label];
          }
        }

        setSegmentTooltip({
          show: true,
          content: companyList,
          x: 0,
          y: 0,
          label: label,
        });
      }
    } else if (hoveredSegment !== null) {
      setHoveredSegment(null);
      // Reset to original percentage when not hovering
      updatePercentageWithFade(defaultPercentage);
      setSegmentTooltip((prev) => ({ ...prev, show: false }));
    }
  }, [hoveredSegment, data.labels, companies, segmentPercentages, defaultPercentage, updatePercentageWithFade]);

  const options = useMemo(() => ({
    cutout: "70%",
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: false, // Disable default tooltip since we'll use custom one
      },
    },
    maintainAspectRatio: true,
    onHover: handleHover,
  }), [handleHover]);

  return (
    <Card className="bg-white border-[1.2px] border-[#c6cbcd] rounded-2xl">
      <CardHeader className="pb-2 pt-4 px-6">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg font-medium font-['Figtree',Helvetica] text-black">
              {title}
            </CardTitle>
            <p className="text-xs text-[#6c6c6c] font-['Figtree',Helvetica] mt-1">
              {subtitle}
            </p>
          </div>
          <div className="flex items-center gap-2 relative">
            <div
              className="relative"
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            >
              <InfoIcon className="w-5 h-5 text-gray-400 cursor-pointer" />
              {showTooltip && (question || weight) && (
                <div className="absolute top-6 left-[-200px] bg-white border border-gray-200 rounded-lg shadow-lg p-3 w-64 z-20">
                  {question && (
                    <p className="text-sm text-gray-700 mb-2">{question}</p>
                  )}
                  {weight && (
                    <p className="text-sm font-medium text-black">
                      <span className="font-semibold">
                        Weight used for score:
                      </span>{" "}
                      {weight}
                    </p>
                  )}
                </div>
              )}
            </div>
            <img 
              src="/iconoir_expand.svg" 
              alt="Expand" 
              className="w-4 h-4 cursor-pointer"
              onClick={onExpand}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-2 pb-4 px-6">
        <div className="flex items-center gap-6">
          <div 
            className="relative w-[160px] h-[160px]"
            onMouseLeave={() => {
              setHoveredSegment(null);
              updatePercentageWithFade(defaultPercentage);
              setSegmentTooltip((prev) => ({ ...prev, show: false }));
            }}
          >
            <Doughnut data={chartData} options={options} />
            <div className="absolute w-[105px] h-[105px] top-[27.5px] left-[27.5px] bg-[#f5f7fa] rounded-full flex items-center justify-center">
              <div 
                className="font-['Figtree',Helvetica] font-medium text-black text-2xl transition-opacity duration-300 ease-in-out"
                style={{ opacity: percentageOpacity }}
              >
                {displayedPercentage}
              </div>
            </div>

            {/* Custom segment tooltip */}
            {segmentTooltip.show && segmentTooltip.content.length > 0 && (
              <div
                className="absolute bg-white border border-gray-200 rounded-lg shadow-lg p-3 z-30 pointer-events-none"
                style={{
                  left: "180px",
                  top: "20px",
                  minWidth: "120px",
                  maxWidth: "200px",
                }}
              >
                <div className="text-sm font-medium text-gray-800 mb-2">
                  {segmentTooltip.label}
                </div>
                <div className="space-y-1">
                  {segmentTooltip.content.map((company, index) => (
                    <div key={index} className="text-xs text-gray-600">
                      {company}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="flex flex-col gap-3">
            {data.labels.map((label, index) => (
              <div key={index} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-sm"
                  style={{ backgroundColor: data.colors[index] }}
                />
                <div className="font-['Figtree',Helvetica] font-normal text-black text-sm whitespace-nowrap">
                  {label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
