// src/app/saved/SavedContext.tsx
'use client';

import { createContext, useContext } from 'react';

interface SavedContextValue {
  barSize?: number;
  openTabs: string[];
  currentTab: string;
  setOpenTabsHandler: (tabs: string[]) => void;
  setCurrentTabHandler: (tab: string) => void;
}

const SavedContext = createContext<SavedContextValue | undefined>(undefined);

export function useSaved() {
  const ctx = useContext(SavedContext);
  if (!ctx) throw new Error('useSaved must be used within SavedProvider');
  return ctx;
}

export default SavedContext;