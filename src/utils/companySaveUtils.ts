// Utility for saving or deleting a company and updating state/localStorage
interface SaveOrDeleteCompanyParams {
  companyData: any;
  setCompanyData: (data: any) => void;
  setSaveMessage: (msg: string | null) => void;
  setSaving: (saving: boolean) => void;
  ApiService: any;
}

export async function saveOrDeleteCompany({ companyData, setCompanyData, setSaveMessage, setSaving, ApiService }: SaveOrDeleteCompanyParams) {
  if (!companyData) return;

  setSaving(true);
  setSaveMessage(null);
  
  try {
    if (companyData.from_database) {
      // Delete from database
      const result = await ApiService.deleteCompanyFromDatabase(companyData.company_name);
      if (result.success) {
        setSaveMessage('Company removed from database successfully!');
        // Update the data to indicate it's no longer in database
        const updatedData = { ...companyData, from_database: false };
        setCompanyData(updatedData);
        localStorage.setItem('currentCompanyData', JSON.stringify(updatedData));
      }
    } else {
      // Save to database
      const dataToSave = companyData.scraper_results || companyData;
      const result = await ApiService.saveCompanyToDatabase(dataToSave);
      if (result.success) {
        setSaveMessage(`Company saved successfully! (ID: ${result.company_id}, Score: ${result.cng_adoption_score}%)`);
        // Update the data to indicate it's now in database
        const updatedData = { ...companyData, from_database: true };
        setCompanyData(updatedData);
        localStorage.setItem('currentCompanyData', JSON.stringify(updatedData));
      }
    }
  } catch (error) {
    console.error('Save/Delete error:', error);
    const action = companyData.from_database ? 'remove' : 'save';
    
    // Handle specific error cases
    if (error instanceof Error) {
      if (error.message.includes('409') || error.message.includes('already exists') || error.message.includes('Conflict')) {
        setSaveMessage('Company already exists in database');
        // Update the data to indicate it's in database
        const updatedData = { ...companyData, from_database: true };
        setCompanyData(updatedData);
        localStorage.setItem('currentCompanyData', JSON.stringify(updatedData));
      } else {
        setSaveMessage(`Failed to ${action} company: ${error.message}`);
      }
    } else {
      setSaveMessage(`Failed to ${action} company: Please try again.`);
    }
  } finally {
    setSaving(false);
    setTimeout(() => setSaveMessage(null), 5000);
  }
} 