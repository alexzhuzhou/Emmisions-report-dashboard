"use client";

import * as React from "react";

interface ProgressProps {
    value?: number; // 0-100
    className?: string;
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
    ({ value = 100, className }, ref) => {
        // SVG semicircle calculations
        // Dynamically set size and strokeWidth based on screen size
        const [dimensions, setDimensions] = React.useState({ size: 600, strokeWidth: 100 });

        React.useEffect(() => {
            function updateDimensions() {
                // Clamp size between 200 and 600, scale with window width
                const size = Math.max(200, Math.min(600, Math.floor(window.innerWidth * 0.25)));
                // Clamp strokeWidth between 24 and 100, scale with size
                const strokeWidth = Math.max(24, Math.min(100, Math.floor(size * 0.16)));
                setDimensions({ size, strokeWidth });
            }
            updateDimensions();
            window.addEventListener("resize", updateDimensions);
            return () => window.removeEventListener("resize", updateDimensions);
        }, []);

        const size = dimensions.size;
        const strokeWidth = dimensions.strokeWidth;
        const radius = (size - strokeWidth) / 2;
        const circumference = Math.PI * radius; // Half circle
        const progress = Math.max(0, Math.min(value, 100));
        const offset = circumference - (progress / 100) * circumference;

        return (
            <div 
                ref={ref}
                className={`bg-white rounded-2xl pt-12 pb-4 px-4 flex flex-col items-center justify-center w-full ${className}`}
            >

                {/* Semicircular Progress */}
                <div className="relative flex items-center justify-center">
                    <svg width={size} height={size/2 + 40} viewBox={`0 0 ${size} ${size/2 + 40}`}>
                        {/* Background semicircle */}
                        <path
                            d={`M ${strokeWidth/2} ${size/2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth/2} ${size/2}`}
                            fill="none"
                            stroke="#E5E7EB"
                            strokeWidth={strokeWidth}
                            strokeLinecap="butt"
                        />
                        {/* Progress semicircle */}
                        <path
                            d={`M ${strokeWidth/2} ${size/2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth/2} ${size/2}`}
                            fill="none"
                            stroke="#2BA2D4"
                            strokeWidth={strokeWidth}
                            strokeLinecap="butt"
                            strokeDasharray={circumference}
                            strokeDashoffset={offset}
                            style={{
                                transition: 'stroke-dashoffset 0.5s ease-in-out',
                            }}
                        />
                    </svg>
                    
                    {/* Center text */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-[clamp(4rem,_3vw,9rem)] font-bold leading-tight text-gray-900 mt-auto mb-5">
                            {value}%
                        </span>
                    </div>
                </div>
            </div>
        );
    }
);

Progress.displayName = "Progress";

export default Progress;
export { Progress as ProgressBar };