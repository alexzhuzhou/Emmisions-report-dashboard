"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import Button from "@/components/ui/button";

interface SortOption {
  id: string;
  label: string;
  icon: string;
}

interface SortDropdownProps {
  isOpen: boolean;
  onClose: () => void;
  onApplySort: (selectedSorts: string[]) => void;
  selectedSorts?: string[];
  className?: string;
}

export function SortDropdown({ 
  isOpen, 
  onClose, 
  onApplySort,
  selectedSorts = [],
  className 
}: SortDropdownProps) {
  const [localSelectedSorts, setLocalSelectedSorts] = useState<string[]>(selectedSorts);

  const sortOptions: SortOption[] = [
    {
      id: "sustainability-score",
      label: "Sustainability Score",
      icon: "north"
    },
    {
      id: "companies-a-z", 
      label: "Companies: A to Z",
      icon: "sort_by_alpha"
    }
  ];

  const handleSortSelect = (option: SortOption) => {
    setLocalSelectedSorts(prev => {
      if (prev.includes(option.label)) {
        return [];
      } else {
        return [option.label];
      }
    });
  };

  const handleApplySort = () => {
    onApplySort(localSelectedSorts);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      <div 
        className="fixed inset-0 z-40"
        onClick={onClose}
      />
      
      <div className={cn(
        "absolute right-0 top-full mt-1 w-64 bg-white border border-gray-200 rounded-2xl shadow-lg z-50 p-6",
        className
      )}>
        <div className="space-y-3 mb-6">
          {sortOptions.map((option) => (
            <button
              key={option.id}
              onClick={() => handleSortSelect(option)}
              className={cn(
                "w-full px-4 py-2 text-left text-sm transition-colors flex items-center gap-3 rounded-xl border-2",
                localSelectedSorts.includes(option.label)
                  ? "text-white bg-[#2BA2D4] border-[#2BA2D4]" 
                  : "text-gray-700 hover:bg-gray-50 border-gray-300"
              )}
            >
              <span className={cn(
                "material-symbols-outlined",
                localSelectedSorts.includes(option.label) ? "text-white" : "text-gray-500",
                option.id === "sustainability-score" ? "text-base" : "text-lg"
              )}>
                {option.icon}
              </span>
              <span className="flex-1">{option.label}</span>
              {localSelectedSorts.includes(option.label) && (
                <span className="material-symbols-outlined text-white text-sm">
                  check
                </span>
              )}
            </button>
          ))}
        </div>
        
        <Button
          onClick={handleApplySort}
          className={cn(
            "w-full h-12 rounded-lg font-semibold text-lg py-2.5 px-5 gap-2.5",
            localSelectedSorts.length === 0
              ? "bg-gray-500 hover:bg-gray-600 text-white"
              : "bg-[#2BA2D4] hover:bg-[#2BA2D4]/90 text-white"
          )}
        >
          {localSelectedSorts.length === 0 ? "Clear Sorting" : "Sort Companies"}
        </Button>
      </div>
    </>
  );
} 