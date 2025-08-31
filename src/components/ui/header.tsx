"use client";

import { ReactNode, useState } from "react";

interface HeaderProps {
  companyName: string;
  actions?: ReactNode; // allows flexible button rendering
}

export default function Header({
  companyName,
  actions,
}: HeaderProps) {
  const [showCompanyNameTooltip, setShowCompanyNameTooltip] = useState(false);


  return (
    <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
      <div className="flex items-center gap-2">
        <h1 className="text-3xl font-bold text-black">{companyName}</h1>
        <div 
          className="relative w-6 h-6"
          onMouseEnter={() => setShowCompanyNameTooltip(true)}
          onMouseLeave={() => setShowCompanyNameTooltip(false)}
        >
        </div>
      </div>

      {actions && (
        <div className="flex items-center gap-2">
          {actions}
        </div>
      )}
    </div>
  );
}