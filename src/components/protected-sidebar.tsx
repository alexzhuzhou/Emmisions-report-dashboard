"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import Image from "next/image";
import { useRouter } from "next/navigation";

const navItems = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: "dashboard",
  },
  {
    name: "Search",
    href: "/",
    icon: "search",
  },
  {
    name: "Saved",
    href: "/saved",
    icon: "bookmark",
  },
  {
    name: "Compare",
    href: "/compare",
    icon: "bar_chart",
  },
];

interface ProtectedSidebarProps {
  onNavigationAttempt?: (href: string) => void;
  shouldIntercept?: boolean;
}

export default function ProtectedSidebar({
  onNavigationAttempt, 
  shouldIntercept,
}: ProtectedSidebarProps) {
  const pathname = usePathname();
  const [isHovered, setIsHovered] = useState<string | null>(null);
  const router = useRouter();

  const handleNavClick = (href: string) => {
    if (onNavigationAttempt && shouldIntercept) {
      onNavigationAttempt(href);
    } else {
      router.push(href);
    }
  };

  return (
    <aside className="w-[72px] border-r border-border bg-card flex flex-col items-center py-4 h-screen sticky top-0">
      <div className="mb-8">
        <div className="w-[40px] h-[40px] relative">
          <Image
            src="https://upload.wikimedia.org/wikipedia/commons/8/86/Chevron_Logo.svg"
            alt="Chevron Logo"
            width={40}
            height={40}
            priority
          />
        </div>
      </div>

      <nav className="flex flex-col items-center justify-center space-y-20 flex-1 w-full">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === item.href
              : pathname.startsWith(item.href);

          return (
            <button
              key={item.name}
              onClick={() => handleNavClick(item.href)}
              className={cn(
                "flex flex-col items-center justify-center w-[60px] h-[60px] rounded-md relative transition-all duration-200 group cursor-pointer",
                isActive
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
              onMouseEnter={() => setIsHovered(item.name)}
              onMouseLeave={() => setIsHovered(null)}
            >
              <div className="flex flex-col items-center justify-center">
                <span
                  className={cn(
                    "material-symbols-outlined mb-1 text-xl transition-transform duration-200",
                    isActive
                      ? "text-[#2BA2D4]"
                      : "text-[#757575] group-hover:text-[#2BA2D4]",
                    isHovered === item.name && "scale-110"
                  )}
                  style={{ lineHeight: "1.25rem" }}
                >
                  {item.icon}
                </span>
                <span
                  className={cn(
                    "text-xs font-medium transition-colors duration-200",
                    isActive
                      ? "text-[#2BA2D4]"
                      : "text-[#757575] group-hover:text-[#2BA2D4]"
                  )}
                >
                  {item.name}
                </span>
              </div>
              {isActive && (
                <span className="absolute left-0 w-[3px] h-full bg-primary rounded-r-md" />
              )}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
