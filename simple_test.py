#!/usr/bin/env python3
"""
Simple test to run analyze_company_sustainability function
"""

import sys
import os

# Add the backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from backend.src.scraper.main_ai_scraper import analyze_company_sustainability, ALL_CRITERIA

def main():
    print("🧪 Testing analyze_company_sustainability function...")
    print("=" * 50)
    
    # Simple test with limited scope for faster execution
    try:
        results = analyze_company_sustainability(
            company_name='UPS',
            criteria=ALL_CRITERIA,  # All 8 criteria
                          max_search_pages=20,
              max_pdf_reports=7,
              max_web_pages=15,
            verbose=True
        )
        
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Function completed successfully")
        print("=" * 50)
        print("📋 FUNCTION RETURN VALUE:")
        print("=" * 50)
        
        # Print the actual return value
        import json
        
        # Convert CriteriaEvidence objects to readable format for printing
        printable_results = {}
        for key, value in results.items():
            if key == 'evidence_details':
                                    printable_results[key] = {
                    criterion: {
                        'criterion': evidence.criterion,
                        'found': evidence.found,
                        'score': evidence.score,
                        'confidence': evidence.confidence,
                        'evidence_text': evidence.evidence_text[:100] + '...' if len(evidence.evidence_text) > 100 else evidence.evidence_text,
                        'justification': evidence.justification[:150] + '...' if len(evidence.justification) > 150 else evidence.justification,
                        'source_type': evidence.source_type,
                        'url': evidence.url,
                        'verified': evidence.verified,
                        'full_context': evidence.full_context[:1000] + '...' if len(evidence.full_context) > 1000 else evidence.full_context,
                        'potential_issues': evidence.potential_issues,
                        'extracted_number': evidence.extracted_number,
                        'extracted_unit': evidence.extracted_unit,
                        'numeric_range': evidence.numeric_range
                    }
                    for criterion, evidence in value.items()
                }
            else:
                printable_results[key] = value
        
        print(json.dumps(printable_results, indent=2, default=str))
        
        print("\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 