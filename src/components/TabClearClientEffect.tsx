'use client';
import { useClearTabsOnRouteChange } from '@/hooks/useClearTabsOnRouteChange';

export default function TabClearClientEffect() {
  useClearTabsOnRouteChange();
  return null;
} 
