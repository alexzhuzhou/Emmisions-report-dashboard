"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { SearchInput } from "@/components/ui/search-input";
import Sidebar from "@/components/sidebar";
import { ApiService } from "@/services/api";
import { useLocation } from "react-router-dom";



export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const [searchValue, setSearchValue] = useState(query);


  useEffect(() => {
    setSearchValue(query);
  }, [query]);

  const handleSearch = async (value: string) => {
    if (value.trim()) {
      // Store the search query and immediately redirect to loading page
      localStorage.setItem('searchQuery', value.trim());
      localStorage.setItem('searchStartTime', Date.now().toString());
      // Redirect to loading page - the loading page will handle the API call
      router.push('/loading');
    }
  };

  return (
    <div className="flex min-h-screen bg-white">
      <Sidebar/>
      <main className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center justify-center text-center max-w-3xl w-full px-4">
          <h1 
            className="text-4xl font-bold mb-8"
            style={{ color: "#000000" }}
          >
            Emissions Report
          </h1>

          <SearchInput
            placeholder="Search Company"
            onSearch={handleSearch}
            className="w-full max-w-xl mb-12"
          />

          {query && (
            <div className="w-full max-w-4xl mx-auto">
              <h2 className="text-xl font-medium mb-4">
                Search results for &quot;{query}&quot;
              </h2>
              <div className="bg-card rounded-lg border p-8 text-center text-muted-foreground">
                {searchParams.get("error") === "no_results" && "No emissions reports found for this search term."}
                {searchParams.get("error") === "search_failed" && "Search failed. Please try again."}
                {!searchParams.get("error") && "No emissions reports found for this search term."}
              </div>
            </div>
          )}
        </div>
      </main>


    </div>
  );
}

