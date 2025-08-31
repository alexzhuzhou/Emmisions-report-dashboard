#!/usr/bin/env python3
"""
Quick test script for get_sustainability_reports function
"""
import sys
import os

# Add the backend src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def test_get_sustainability_reports():
    try:
        from search.google_search import get_sustainability_reports
        
        print("Testing get_sustainability_reports function...")
        
        # Test with IBM
        print("\n=== Testing with IBM ===")
        ibm_results = get_sustainability_reports("IBM", max_results=3)
        print(f"IBM results: {len(ibm_results)} URLs found")
        for i, url in enumerate(ibm_results, 1):
            print(f"  {i}. {url}")
        
        # Test with Microsoft
        print("\n=== Testing with Microsoft ===")
        msft_results = get_sustainability_reports("Microsoft", max_results=3)
        print(f"Microsoft results: {len(msft_results)} URLs found")
        for i, url in enumerate(msft_results, 1):
            print(f"  {i}. {url}")
            
        # Test with UPS
        print("\n=== Testing with UPS ===")
        ups_results = get_sustainability_reports("UPS", max_results=3)
        print(f"UPS results: {len(ups_results)} URLs found")
        for i, url in enumerate(ups_results, 1):
            print(f"  {i}. {url}")
            
        print("\n✅ Function executed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_get_sustainability_reports() 