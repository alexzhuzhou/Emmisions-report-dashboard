import { useEffect, useRef, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { ApiService } from '@/services/api';
import { saveOrDeleteCompany } from '@/utils/companySaveUtils';

export function useNavigationWarning(companyDataFromPage?: any) {
  const router = useRouter();
  const pathname = usePathname();
  const [showWarning, setShowWarning] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState<string | null>(null);
  const isNavigatingRef = useRef(false);
  // Local state for save/delete operations
  const [companyData, setCompanyData] = useState<any>(companyDataFromPage);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const companyDataRef = useRef(companyData);

  useEffect(() => {
    companyDataRef.current = companyData;
  }, [companyData]);

  useEffect(() => {
    // Optionally update local state if companyDataFromPage changes
    if (companyDataFromPage) {
      setCompanyData(companyDataFromPage);
    }
  }, [companyDataFromPage]);

  useEffect(() => {
    const loadAndCheckCompanyData = async () => {
      // Load company data from localStorage
      const storedData = localStorage.getItem('currentCompanyData');
      if (storedData) {
        try {
          const parsedData = JSON.parse(storedData);
          // Check if company exists in database
          try {
            const companyName = parsedData.company_name || parsedData.scraper_results?.company?.company_name;
            if (companyName) {
              const checkResult = await ApiService.checkCompanyInDatabase(companyName);
              parsedData.from_database = checkResult.exists;
            } else {
              parsedData.from_database = false;
            }
          } catch (error) {
            parsedData.from_database = false;
          }
          setCompanyData(parsedData);
          localStorage.setItem('currentCompanyData', JSON.stringify(parsedData));
        } catch (error) {
          router.push('/home');
        }
      } else {
        router.push('/home');
      }
    };
    loadAndCheckCompanyData();
  }, [router]);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (!companyDataRef.current || companyDataRef.current.from_database === false) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  const interceptNavigation = (href: string) => {
    if (href === pathname) {
      return;
    }
    setPendingNavigation(href);
    setShowWarning(true);
  };

  const handleSaveAndContinue = async () => {
    await saveOrDeleteCompany({
      companyData,
      setCompanyData,
      setSaveMessage,
      setSaving,
      ApiService
    });
    if (pendingNavigation) {
      isNavigatingRef.current = true;
      router.push(pendingNavigation);
      setShowWarning(false);
      setPendingNavigation(null);
    }
  };

  const handleLeaveWithoutSaving = () => {
    if (pendingNavigation) {
      isNavigatingRef.current = true;
      router.push(pendingNavigation);
      setShowWarning(false);
      setPendingNavigation(null);
    }
  };

  const handleCancelNavigation = () => {
    setShowWarning(false);
    setPendingNavigation(null);
  };

  return {
    showWarning,
    pendingNavigation,
    interceptNavigation,
    handleSaveAndContinue,
    handleLeaveWithoutSaving,
    handleCancelNavigation,
    saving,
    saveMessage,
    companyData
  };
} 