// src/app/saved/layout.tsx
'use client';

import React, { useState, useRef, useEffect } from 'react';
import Sidebar from '@/components/sidebar';
import Tabbar from '@/components/tabbar';
import SavedContext from './SavedContext';
import { usePathname } from 'next/navigation';

export default function SavedLayout({ children }: { children: React.ReactNode }) {
  const [openTabs, setOpenTabs] = useState<string[]>(['saved']);
  const [currentTab, setCurrentTab] = useState<string>('saved');
  const containerRef = useRef<HTMLDivElement>(null);
  const [barSize, setBarSize] = useState<number>();
  const pathname = usePathname();

  const setOpenTabsHandler = (newOpenTabs: string[]) => {
    setOpenTabs(newOpenTabs);
    console.log(newOpenTabs)
    localStorage.setItem('openTabs', JSON.stringify(newOpenTabs));
  };

  const setCurrentTabHandler = (newCurrentTab: string) => {
    setCurrentTab(newCurrentTab);
    localStorage.setItem('currentTab', newCurrentTab);
  }

  useEffect(() => {
    const temp = localStorage.getItem('openTabs');
    const currTemp = localStorage.getItem('currentTab');
    if (!temp) setOpenTabs(['saved']);
    else setOpenTabs(JSON.parse(temp));
    if (!currTemp) setCurrentTab('saved');
    else setCurrentTab(currTemp);
  }, []);

  // Reset currentTab to 'saved' when on main saved page
  useEffect(() => {
    // Only reset if we're on the main saved page (/saved) and currentTab in localStorage is not 'saved'
    if (pathname === '/saved') {
      const storedCurrentTab = localStorage.getItem('currentTab');
      if (storedCurrentTab && storedCurrentTab !== 'saved') {
        console.log('Resetting currentTab to saved because on main saved page');
        setCurrentTab('saved');
        localStorage.setItem('currentTab', 'saved');
      }
    }
  }, [pathname]); // Only depend on pathname, not currentTab

  useEffect(() => {
    if (containerRef.current) {
      setBarSize(containerRef.current.clientWidth);
    }
  }, []);

  return (
    <SavedContext.Provider
      value={{
        barSize,
        openTabs,
        currentTab,
        setOpenTabsHandler,
        setCurrentTabHandler,
      }}
    >
      <div className="w-full h-full bg-white flex">
        <Sidebar />
        <div ref={containerRef} className="flex flex-col w-full">
          <Tabbar
            openTabs={openTabs}
            currentTab={currentTab}
            setCurrentTab={setCurrentTabHandler}
            setOpenTabs={setOpenTabsHandler}
          />
          {children}
        </div>
      </div>
    </SavedContext.Provider>
  );
}