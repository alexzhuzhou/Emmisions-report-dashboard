"use client";

import { useState } from "react";
import { SearchInput } from "@/components/ui/search-input";
import Button from "@/components/ui/button";
import { FilterDropdown } from "@/components/ui/filter-dropdown";
import { SortDropdown } from "@/components/ui/sort-dropdown";
import { cn } from "@/lib/utils";

interface FilterState {
  sustainabilityScore: {
    min: number;
    max: number;
  };
  metrics: string[];
}

interface SavedReportsBarProps {
  onSearch?: (value: string) => void;
  onFilter?: (filters: FilterState) => void;
  onApplySort?: (selectedSorts: string[]) => void;
  className?: string;
}

export function SavedReportsBar({ 
  onSearch, 
  onFilter, 
  onApplySort,
  className 
}: SavedReportsBarProps) {
  const [showSortDropdown, setShowSortDropdown] = useState(false);
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [selectedSorts, setSelectedSorts] = useState<string[]>([]);
  const [activeFilters, setActiveFilters] = useState<FilterState>({
    sustainabilityScore: { min: 0, max: 100 },
    metrics: []
  });

  const handleFilterToggle = () => {
    setShowFilterDropdown(!showFilterDropdown);
    setShowSortDropdown(false);
  };

  const handleSortToggle = () => {
    setShowSortDropdown(!showSortDropdown);
    setShowFilterDropdown(false);
  };

  const handleApplyFilters = (filters: FilterState) => {
    setActiveFilters(filters);
    setShowFilterDropdown(false);
    if (onFilter) onFilter(filters);
  };

  const handleApplySort = (sorts: string[]) => {
    setSelectedSorts(sorts);
    if (onApplySort) onApplySort(sorts);
  };

  const hasActiveFilters = activeFilters.metrics.length > 0 || 
    activeFilters.sustainabilityScore.min > 0 || 
    activeFilters.sustainabilityScore.max < 100;

  const hasActiveSorts = selectedSorts.length > 0;

  return (
    <div className={cn("bg-white border-b border-gray-200", className)}>
      <div className="flex items-center justify-between px-6 py-4">
        {/* Left side - Title and Info Icons */}
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-semibold text-gray-900">Saved Reports</h1>
          
        </div>

        {/* Right side - Search, Filter, Sort */}
        <div className="flex items-center gap-4 mr-8">
          {/* Search Input */}
          <SearchInput
            placeholder="Search"
            className="w-64 [&>input]:h-10 [&>input]:rounded-xl [&>input]:border-2 [&>input]:border-[#2BA2D4] [&>input]:bg-blue-50/30 [&>input]:text-gray-700 [&>input]:placeholder-[#2BA2D4] [&>input]:font-medium [&>input]:focus:border-[#2BA2D4] [&>input]:focus:bg-blue-50/50 [&>input]:focus:outline-none [&>input]:focus:ring-0 [&>input]:focus:shadow-none [&>input]:focus-visible:border-[#2BA2D4] [&>input]:focus-visible:outline-none"
            onSearch={onSearch}
          />

          {/* Filter Button with Dropdown */}
          <div className="relative">
            <Button
              variant="outline"
              onClick={handleFilterToggle}
              className={cn(
                "h-10 px-4 rounded-xl border-2 border-[#2BA2D4] bg-blue-50/30 hover:bg-blue-50/50 flex items-center gap-2",
                hasActiveFilters && "border-[#2BA2D4] bg-blue-50/50"
              )}
            >
              <span className="material-symbols-outlined text-[#2BA2D4] text-sm">
                filter_alt
              </span>
              <span className={cn(
                "text-[#2BA2D4] font-medium",
                hasActiveFilters && "text-[#2BA2D4] font-medium"
              )}>
                Filter
              </span>
              {hasActiveFilters && (
                <span className="bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {activeFilters.metrics.length || '•'}
                </span>
              )}
            </Button>

            <FilterDropdown
              isOpen={showFilterDropdown}
              onClose={() => setShowFilterDropdown(false)}
              onApplyFilters={handleApplyFilters}
            />
          </div>

          {/* Sort Dropdown */}
          <div className="relative">
            <Button
              variant="outline"
              onClick={handleSortToggle}
              className={cn(
                "h-10 px-4 rounded-xl border-2 border-[#2BA2D4] bg-blue-50/30 hover:bg-blue-50/50 flex items-center gap-2",
                hasActiveSorts && "border-[#2BA2D4] bg-blue-50/50"
              )}
            >
              <span className="material-symbols-outlined text-[#2BA2D4] text-sm">
                sort
              </span>
              <span className="text-[#2BA2D4] font-medium">Sort by</span>
              <span className="material-symbols-outlined text-[#2BA2D4] text-sm">
                keyboard_arrow_down
              </span>
              {hasActiveSorts && (
                <span className="bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {selectedSorts.length}
                </span>
              )}
            </Button>

            <SortDropdown
              isOpen={showSortDropdown}
              onClose={() => setShowSortDropdown(false)}
              onApplySort={handleApplySort}
              selectedSorts={selectedSorts}
            />
          </div>
        </div>
      </div>
    </div>
  );
} 