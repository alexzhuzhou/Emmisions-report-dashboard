"use client";

import ExcelJS from "exceljs";

export default function ExportPage() {
  const handleExport = async () => {
    try {
      const res = await fetch("http://localhost:8000/company_card/2");
      if (!res.ok) throw new Error("Failed to fetch data");

      const data = await res.json();

      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet("Company Card");

      worksheet.columns = [
        { header: "Field", key: "field", width: 30 },
        { header: "Value", key: "value", width: 70 },
      ];

      // Flattened structure
      const rows = [
        ["Company Name", data.company_name],
        ["Has Emission Goals", data.sustainability_metrics?.has_emission_goals],
        [
          "Emission Report Available",
          data.sustainability_metrics?.emission_report_available,
        ],
        [
          "Reduction Strategies",
          data.sustainability_metrics?.reduction_strategies,
        ],
        ["RNG Mentions", data.sustainability_metrics?.rng_mentions],
        ["Owns RNG Trucks", data.sustainability_metrics?.owns_rng_trucks],
        ["LLM Summary", data.llm_summary?.summary_text],
        ["CNG Score", data.cng_adoption_score?.score],
        ["CNG Score Explanation", data.cng_adoption_score?.score_explanation],
      ];

      rows.forEach(([field, value]) => {
        worksheet.addRow({ field, value });
      });

      const buffer = await workbook.xlsx.writeBuffer();

      const blob = new Blob([buffer], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = "test_company_data.xlsx";
      link.click();

      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
    }
  };

  return (
    <main style={{ padding: "2rem" }}>
      <h1>Export Company Card (ExcelJS)</h1>
      <button
        onClick={handleExport}
        style={{ padding: "1rem", fontSize: "1rem", cursor: "pointer" }}
      >
        export test_company_card
      </button>
    </main>
  );
}
