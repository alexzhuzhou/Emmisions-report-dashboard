"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/sidebar";
import { ApiService } from "@/services/api";

export default function LoadingPage() {
  const router = useRouter();
  const [loadingMessage, setLoadingMessage] = useState("Initializing search...");

  useEffect(() => {
    // Check if there's a search in progress
    const searchQuery = localStorage.getItem('searchQuery');
    const searchStartTime = localStorage.getItem('searchStartTime');

    if (!searchQuery) {
      // No search in progress, redirect to home
      router.push('/home');
      return;
    }

    // Start the search process
    const performSearch = async () => {
      try {
        const searchResults = await ApiService.searchCompanies(searchQuery);
        
        // The backend returns the structured data directly, not wrapped in success/scraper_results
        // Check if we have the expected structure (company data)
        if (searchResults && (searchResults.company || searchResults.company_name)) {
          // Store the complete search results for dashboard to access
          const dataToStore = {
            company_name: searchResults.company?.company_name || searchResults.company_name,
            scraper_results: searchResults,
            from_database: searchResults.from_database || false
          };
          
          localStorage.setItem('currentCompanyData', JSON.stringify(dataToStore));
          // Clear search query since we're done
          localStorage.removeItem('searchQuery');
          localStorage.removeItem('searchStartTime');
          // Redirect to dashboard to show the company data
          router.push('/dashboard');
        } else {
          // Clear search data and show error
          localStorage.removeItem('searchQuery');
          localStorage.removeItem('searchStartTime');
          router.push(`/home?q=${encodeURIComponent(searchQuery)}&error=no_results`);
        }
      } catch (error) {
        console.error('Search error:', error);
        // Clear search data and redirect to search page with error
        localStorage.removeItem('searchQuery');
        localStorage.removeItem('searchStartTime');
        router.push(`/home?q=${encodeURIComponent(searchQuery)}&error=search_failed`);
      }
    };

    // Start the search
    performSearch();

    // Update loading message based on elapsed time
    const startTime = parseInt(searchStartTime || '0');
    const updateMessage = () => {
      const elapsed = Date.now() - startTime;
      if (elapsed < 5000) {
        setLoadingMessage("Searching database...");
      } else if (elapsed < 15000) {
        setLoadingMessage("Running AI analysis...");
      } else if (elapsed < 30000) {
        setLoadingMessage("Gathering sustainability data...");
      } else {
        setLoadingMessage("Finalizing analysis...");
      }
    };

    // Update message every 2 seconds
    const messageInterval = setInterval(updateMessage, 2000);
    updateMessage(); // Call immediately

    // Cleanup on unmount
    return () => {
      clearInterval(messageInterval);
    };
  }, [router]);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = '';
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  return (
    <div className="flex min-h-screen bg-white">
      {/* Sidebar removed for loading screen */}
      <div className="flex-1 flex flex-col relative">
        {/* Blue background - extends to truck wheels */}
        <div className="h-[60%]" style={{ backgroundColor: '#E8F4F8' }}>
        </div>
        
        {/* White background - lower portion */}
        <div className="h-[40%] bg-white">
        </div>
        
        {/* Centered truck - positioned absolutely to be in the middle, made bigger */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-[800px] h-[500px] relative flex items-center justify-center">
            <img
              src="/loading.gif"
              alt="Loading truck animation"
              className="max-w-full max-h-full object-contain"
            />
          </div>
        </div>

        {/* Loading message overlay */}
        <div className="absolute bottom-20 left-0 right-0 flex justify-center">
          <div className="bg-white/90 backdrop-blur-sm rounded-lg px-6 py-3 shadow-lg">
            <p className="text-gray-700 font-medium text-center">
              {loadingMessage}
            </p>
            <p className="text-gray-500 text-sm text-center mt-1">
              You can leave me running in the background, and I'll email you when the report is ready!
            </p>
          </div>
        </div>
      </div>
    </div>
    
  );
}
