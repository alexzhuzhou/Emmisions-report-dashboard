"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";

interface SearchInputProps {
  placeholder?: string;
  className?: string;
  onSearch?: (value: string) => void;
  disabled?: boolean;
}

export function SearchInput({ 
  placeholder = "Search", 
  className,
  onSearch,
  disabled = false
}: SearchInputProps) {
  const [value, setValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);

  const handleSearch = () => {
    if (onSearch && !disabled) onSearch(value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div
      className={cn(
        "flex items-center w-full relative max-w-2xl transition-all duration-200",
        isFocused ? "ring-2 ring-primary/20 rounded-full" : "",
        className
      )}
    >
      <span
        className="material-symbols-outlined absolute left-4 h-5 w-5 text-xl leading-none"
        style={{ lineHeight: "1.25rem", color: "#2BA2D4"}}
      >
        search
      </span>
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        onKeyDown={handleKeyDown}
        type="text"
        placeholder={placeholder}
        disabled={disabled}
        className="pl-11 h-12 rounded-full border border-gray-300 bg-white text-black placeholder-[#757575] disabled:opacity-50 disabled:cursor-not-allowed"
      />
    </div>
  );
}