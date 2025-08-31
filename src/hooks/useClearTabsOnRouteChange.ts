"use client";

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';

export function useClearTabsOnRouteChange() {
  const pathname = usePathname();

  useEffect(() => {
    if (!pathname.startsWith('/saved')) {
      localStorage.setItem('openTabs', JSON.stringify([]));
      localStorage.setItem('currentTab', '');
    }
  }, [pathname]);
}
