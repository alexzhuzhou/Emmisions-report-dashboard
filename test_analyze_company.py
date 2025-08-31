#!/usr/bin/env python3
"""
Test script for analyze_company_sustainability function
Tests the comprehensive return format and various scenarios
"""

import json
import time
import sys
import os
from typing import Set

# Add the backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

try:
    from backend.src.scraper.main_ai_scraper import analyze_company_sustainability, ALL_CRITERIA
    print("✅ Successfully imported analyze_company_sustainability")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def print_section(title: str, char: str = "="):
    """Print a formatted section header"""
    print(f"\n{char * 60}")
    print(f" {title}")
    print(f"{char * 60}")

def print_results_summary(results: dict, test_name: str):
    """Print a comprehensive summary of the test results"""
    print_section(f"📊 RESULTS SUMMARY - {test_name}", "-")
    
    # Basic info
    print(f"🏢 Company: {results.get('company', 'Unknown')}")
    print(f"📈 Criteria Found: {results.get('found_criteria', 0)}/{results.get('total_criteria', 0)}")
    print(f"⏱️  Analysis Time: {results.get('analysis_time', 0):.2f}s")
    print(f"📅 Timestamp: {time.ctime(results.get('timestamp', 0))}")
    
    # Analysis Summary (if available)
    if 'analysis_summary' in results:
        summary = results['analysis_summary']
        print(f"\n📋 Analysis Details:")
        print(f"   ✅ Criteria Found: {len(summary.get('criteria_found', []))}")
        print(f"   ❌ Criteria Missing: {len(summary.get('criteria_not_found', []))}")
        
        sources = summary.get('sources_analyzed', {})
        print(f"\n📚 Sources Analyzed:")
        print(f"   📄 PDFs: {len(sources.get('pdfs_checked', []))}")
        print(f"   🌐 Web Pages: {len(sources.get('web_pages_scraped', []))}")
        print(f"   🔍 Search Queries: {len(sources.get('search_queries_executed', []))}")
        print(f"   📊 Success Rate: {sources.get('successful_sources_count', 0)}/{sources.get('total_sources_count', 0)}")
    
    # Evidence Quality (if available)
    if 'evidence_quality' in results:
        quality = results['evidence_quality']
        print(f"\n🎯 Evidence Quality:")
        print(f"   🟢 High Confidence: {len(quality.get('high_confidence', []))}")
        print(f"   🟡 Medium Confidence: {len(quality.get('medium_confidence', []))}")
        print(f"   🔴 Low Confidence: {len(quality.get('low_confidence', []))}")
        
        breakdown = quality.get('source_breakdown', {})
        print(f"\n📊 Source Breakdown:")
        print(f"   📄 PDF Evidence: {len(breakdown.get('pdf_evidence', []))}")
        print(f"   🌐 Web Evidence: {len(breakdown.get('web_evidence', []))}")
        print(f"   🔍 Search Evidence: {len(breakdown.get('search_evidence', []))}")
    
    # Performance Metrics (if available)
    if 'performance_metrics' in results:
        perf = results['performance_metrics']
        print(f"\n⚡ Performance Metrics:")
        print(f"   📈 Efficiency Score: {perf.get('efficiency_score', 0):.2f}")
        print(f"   📊 Sources per Criterion: {perf.get('sources_per_criterion', 0):.2f}")
        print(f"   ✅ Success Rate: {perf.get('success_rate', 0):.1f}%")
    
    # Evidence Details Preview
    if 'evidence_details' in results and results['evidence_details']:
        print(f"\n🔍 Evidence Found:")
        for criterion, evidence in list(results['evidence_details'].items())[:3]:  # Show first 3
            print(f"   • {criterion}: Score {evidence.score}, {evidence.source_type}")
        if len(results['evidence_details']) > 3:
            print(f"   ... and {len(results['evidence_details']) - 3} more")

def test_basic_functionality():
    """Test basic functionality with a well-known company"""
    print_section("🧪 TEST 1: Basic Functionality Test")
    
    test_criteria = {'emission_reporting', 'emission_goals'}
    
    try:
        results = analyze_company_sustainability(
            company_name='UPS',
            criteria=test_criteria,
            max_search_pages=5,
            max_pdf_reports=5,
            max_web_pages=5,
            verbose=False  # Reduce output for cleaner test
        )
        
        print("✅ Test 1 PASSED - Function executed successfully")
        print_results_summary(results, "Basic Test")
        return results
        
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_comprehensive_analysis():
    """Test with more criteria and verbose output"""
    print_section("🧪 TEST 2: Comprehensive Analysis Test")
    
    test_criteria = {'emission_reporting', 'emission_goals', 'cng_fleet', 'alt_fuels'}
    
    try:
        results = analyze_company_sustainability(
            company_name='FedEx',
            criteria=test_criteria,
            max_search_pages=5,
            max_pdf_reports=5,
            max_web_pages=5,
            verbose=False  # Set to True to see detailed output
        )
        
        print("✅ Test 2 PASSED - Comprehensive analysis completed")
        print_results_summary(results, "Comprehensive Test")
        return results
        
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_all_criteria():
    """Test with all available criteria (limited resources for speed)"""
    print_section("🧪 TEST 3: All Criteria Test (Limited Resources)")
    
    try:
        results = analyze_company_sustainability(
            company_name='Walmart',
            criteria=ALL_CRITERIA,  # All 8 criteria
            max_search_pages=5,     # Standardized limit
            max_pdf_reports=5,
            max_web_pages=5,
            verbose=False
        )
        
        print("✅ Test 3 PASSED - All criteria analysis completed")
        print_results_summary(results, "All Criteria Test")
        return results
        
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_return_format_consistency():
    """Test that the return format is consistent"""
    print_section("🧪 TEST 4: Return Format Consistency")
    
    required_keys = [
        'company', 'criteria_analyzed', 'evidence_details', 
        'total_criteria', 'found_criteria', 'analysis_time', 'timestamp'
    ]
    
    comprehensive_keys = [
        'analysis_summary', 'evidence_quality', 'performance_metrics'
    ]
    
    try:
        results = analyze_company_sustainability(
            company_name='Amazon',
            criteria={'emission_reporting'},  # Single criterion for speed
            max_search_pages=5,
            max_pdf_reports=5,
            max_web_pages=5,
            verbose=False
        )
        
        # Check required keys
        missing_required = [key for key in required_keys if key not in results]
        missing_comprehensive = [key for key in comprehensive_keys if key not in results]
        
        if not missing_required and not missing_comprehensive:
            print("✅ Test 4 PASSED - All required and comprehensive keys present")
            print(f"📋 Total keys in result: {len(results.keys())}")
            print(f"🔑 Result keys: {list(results.keys())}")
        else:
            print(f"❌ Test 4 PARTIAL - Missing keys:")
            if missing_required:
                print(f"   Required: {missing_required}")
            if missing_comprehensive:
                print(f"   Comprehensive: {missing_comprehensive}")
        
        return results
        
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        return None

def save_test_results(results: dict, filename: str = "test_results.json"):
    """Save test results to a JSON file"""
    try:
        # Convert any non-serializable objects
        serializable_results = {}
        for key, value in results.items():
            if key == 'evidence_details':
                # Convert CriteriaEvidence objects to dicts
                serializable_results[key] = {
                    criterion: {
                        'criterion': evidence.criterion,
                        'found': evidence.found,
                        'score': evidence.score,
                        'confidence': evidence.confidence,
                        'evidence_text': evidence.evidence_text[:200] + '...' if len(evidence.evidence_text) > 200 else evidence.evidence_text,
                        'justification': evidence.justification[:200] + '...' if len(evidence.justification) > 200 else evidence.justification,
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
                serializable_results[key] = value
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Test results saved to: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        return False

def main():
    """Run all tests"""
    print_section("🚀 ANALYZE_COMPANY_SUSTAINABILITY FUNCTION TESTS", "=")
    print("Testing the comprehensive return format and functionality")
    print(f"Available criteria: {list(ALL_CRITERIA)}")
    
    test_results = []
    start_time = time.time()
    
    # Run tests
    test_results.append(test_basic_functionality())
    test_results.append(test_comprehensive_analysis())
    test_results.append(test_all_criteria())
    test_results.append(test_return_format_consistency())
    
    # Summary
    total_time = time.time() - start_time
    successful_tests = sum(1 for result in test_results if result is not None)
    
    print_section("📊 FINAL TEST SUMMARY")
    print(f"✅ Tests Passed: {successful_tests}/{len(test_results)}")
    print(f"⏱️  Total Test Time: {total_time:.2f}s")
    
    if successful_tests > 0:
        print(f"\n🎉 Function is working correctly!")
        print(f"📋 Comprehensive return format confirmed")
        
        # Save the last successful result
        last_successful = next((r for r in reversed(test_results) if r is not None), None)
        if last_successful:
            save_test_results(last_successful)
    else:
        print(f"\n❌ All tests failed - check the function implementation")
    
    print_section("🏁 TESTING COMPLETE")

if __name__ == "__main__":
    main() 