import { X } from "lucide-react";
import React, { useMemo, useEffect, useState } from "react";
import { Card, CardContent } from "./card";
import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

interface ExpandedChartProps {
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
  onClose: () => void;
}

export const ExpandedChart = ({
  title,
  percentage,
  data,
  question,
  weight,
  companies,
  onClose,
}: ExpandedChartProps): JSX.Element => {
  const [windowDimensions, setWindowDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const updateWindowDimensions = () => {
      setWindowDimensions({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    // Set initial dimensions
    updateWindowDimensions();

    // Add event listener for window resize
    window.addEventListener('resize', updateWindowDimensions);

    // Cleanup
    return () => window.removeEventListener('resize', updateWindowDimensions);
  }, []);

  // Calculate responsive scale based on window size
  const getResponsiveScale = () => {
    if (!windowDimensions.width || !windowDimensions.height) return 0.48; // fallback

    // Base dimensions of the component
    const baseWidth = 1156;
    const baseHeight = 772;
    
    // Calculate maximum scale that fits both width and height with padding
    const widthScale = (windowDimensions.width * 0.9) / baseWidth; // 90% of viewport width
    const heightScale = (windowDimensions.height * 0.9) / baseHeight; // 90% of viewport height
    
    // Use the smaller scale to ensure it fits
    const scale = Math.min(widthScale, heightScale);
    
    // Ensure minimum scale for readability and maximum scale for performance
    return Math.max(0.3, Math.min(scale, 1.2));
  };

  const scale = getResponsiveScale();

  // Dynamically get companies for each label
  const getCompaniesForLabel = (label: string) => {
    if (!companies) return [];
    if (companies[label]) return companies[label];
    // Handle case-insensitive matching for legacy data
    const lowerLabel = label.toLowerCase();
    const matchingKey = Object.keys(companies).find(key => key.toLowerCase() === lowerLabel);
    if (matchingKey) return companies[matchingKey];
    return [];
  };

  // Build company lists for all categories
  const categorizedCompanies = useMemo(() => {
    return data.labels.map(label => ({
      label,
      companies: getCompaniesForLabel(label),
      color: data.colors[data.labels.indexOf(label)]
    }));
  }, [data.labels, companies, data.colors]);

  // Calculate total companies
  const totalCompanies = categorizedCompanies.reduce((total, category) => total + category.companies.length, 0);

  // Calculate dynamic positioning for percentages based on chart segments
  const getPercentagePosition = (index: number, values: number[]) => {
    const totalValue = values.reduce((sum, val) => sum + val, 0);
    
    // Calculate cumulative angles based on actual values
    let cumulativeAngle = 0;
    for (let i = 0; i < index; i++) {
      cumulativeAngle += (values[i] / totalValue) * 360;
    }
    
    // Get the current segment's angle
    const segmentAngle = (values[index] / totalValue) * 360;
    
    // Position at the center of the current segment
    const centerAngle = cumulativeAngle + (segmentAngle / 2);
    
    // Chart.js starts at top (-90 degrees) and goes clockwise
    const adjustedAngle = centerAngle - 90;
    const angleRad = (adjustedAngle * Math.PI) / 180;
    
    const radius = 180; // Increased radius to position labels in the middle of donut segments
    const centerX = 246;
    const centerY = 246;
    
    const x = centerX + radius * Math.cos(angleRad);
    const y = centerY + radius * Math.sin(angleRad);
    
    return { x: Math.round(x), y: Math.round(y) };
  };

  const filteredChartData = useMemo(() => {
    const nonZeroIndices = data.values
      .map((value, index) => ({ value, index }))
      .filter(item => item.value > 0)
      .map(item => item.index);

    return {
      labels: nonZeroIndices.map(i => data.labels[i]),
      values: nonZeroIndices.map(i => data.values[i]),
      colors: nonZeroIndices.map(i => data.colors[i]),
      originalIndices: nonZeroIndices
    };
  }, [data.labels, data.values, data.colors]);

  const chartData = useMemo(() => ({
    labels: filteredChartData.labels,
    datasets: [
      {
        data: filteredChartData.values,
        backgroundColor: filteredChartData.colors,
        borderWidth: 0,
        hoverBorderWidth: 0,
      },
    ],
  }), [filteredChartData.labels, filteredChartData.values, filteredChartData.colors]);

  const options = useMemo(() => ({
    cutout: "46%",
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false },
    },
    maintainAspectRatio: false,
  }), []);

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      <div className="absolute inset-0 bg-black/20" onClick={onClose} />
      <div
        className="origin-center"
        style={{
          transform: `scale(${scale})`,
          width: "1156px",
          height: "772px",
          pointerEvents: "auto",
          transformOrigin: "center center",
        }}
      >
        <Card className="relative w-full h-full rounded-2xl border-2 border-solid border-[#c6cbcd] bg-white">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-full transition-colors z-10"
            style={{ right: 16, top: 16 }}
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
          <CardContent className="p-0">
            <header className="pt-[46px] px-[63px]">
              <div className="flex items-center">
                <h1 className="font-['Figtree',Helvetica] font-normal text-black text-4xl tracking-[-0.68px] leading-[54px]">
                  {title}
                </h1>
              </div>
              <p className="font-['Figtree',Helvetica] font-normal text-black text-[15px] tracking-[-0.28px] leading-[22.5px] mt-2">
                Based on {totalCompanies} companies
              </p>
            </header>

            <div className="absolute top-14 right-[63px] font-['Figtree',Helvetica] font-normal text-black text-[15px] text-right tracking-[-0.28px] leading-[22.5px]">
              {question && (
                <span className="tracking-[-0.04px]">
                  {question}
                  <br />
                </span>
              )}
              {weight && (
                <>
                  <span className="font-bold tracking-[-0.04px]">
                    Weight used for score:{" "}
                  </span>
                  <span className="tracking-[-0.04px]">{weight}</span>
                </>
              )}
            </div>

            <div className="flex flex-row items-center mt-[40px]">
              {/* Pie chart section */}
              <div className="relative w-[492px] h-[492px] ml-[91px]">
                <Doughnut data={chartData} options={options} width={492} height={492} />
                {/* Center circle */}
                <div className="absolute w-[227px] h-[227px] top-[133px] left-[133px] bg-[#f5f7fa] rounded-[113.5px]" />
                
                {/* Dynamic percentage positioning */}
                {filteredChartData.labels.map((label, index) => {
                  const position = getPercentagePosition(index, filteredChartData.values);
                  const value = filteredChartData.values[index];
                  const isLightBackground = filteredChartData.colors[index] === '#c6cbcd' || filteredChartData.colors[index] === '#5bb3d9';
                  
                  return (
                    <div
                      key={`percentage-${index}`}
                      className={`absolute font-['Figtree',Helvetica] font-light text-2xl ${
                        isLightBackground ? 'text-black' : 'text-white'
                      }`}
                      style={{
                        left: `${position.x - 20}px`, // Offset to center text
                        top: `${position.y - 12}px`,  // Offset to center text
                      }}
                    >
                      {value}%
                    </div>
                  );
                })}
              </div>

              <div className="flex flex-col ml-[117px]">
                {/* Categories with companies */}
                <div className="flex gap-4 mt-0 max-w-[456px] flex-wrap">
                  {categorizedCompanies.map((category, index) => (
                    <div key={`category-${index}`} className="flex flex-col min-w-0" style={{ flex: `1 1 ${100 / Math.min(categorizedCompanies.length, 4)}%` }}>
                      {/* Category header */}
                      <div className="flex items-center gap-2 mb-3">
                        <div 
                          className="w-[20px] h-[20px] rounded-[3px] flex-shrink-0" 
                          style={{ backgroundColor: category.color }}
                        />
                        <span className="font-['Figtree',Helvetica] font-normal text-black text-lg leading-tight">
                          {category.label}
                        </span>
                      </div>
                      
                      {/* Companies for this category */}
                      {category.companies.length > 0 && (
                        <div className="ml-[24px]">
                          {category.companies.map((company: string, companyIndex: number) => (
                            <div key={`${category.label}-${companyIndex}`} className="mb-3">
                              <div className="font-['Figtree',Helvetica] font-normal text-[#6c6c6c] text-sm leading-tight truncate" title={company}>
                                {company}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}; 