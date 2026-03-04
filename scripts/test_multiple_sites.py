#!/usr/bin/env python3
"""
Test VeriSight against multiple real websites
Verify detection works correctly
"""
import requests
import json
import sys
import time

API_BASE = "http://localhost:8000/api/check-scam"

# Test URLs - mix of safe and potentially suspicious
TEST_URLS = [
    # Should be SAFE (real legitimate sites)
    ("https://www.paypal.com", "Real PayPal", "safe"),
    ("https://www.amazon.com", "Real Amazon", "safe"),
    ("https://www.nike.com", "Real Nike", "safe"),
    ("https://www.chase.com", "Real Chase", "safe"),
    ("https://www.apple.com", "Real Apple", "safe"),
    ("https://github.com", "GitHub", "safe"),
    ("https://google.com", "Google", "safe"),
    
    # Should be FLAGGED (our demo site)
    ("http://localhost:8080/fake-paypal.html", "Fake PayPal (Demo)", "scam"),
]

def test_url(url, name, expected_result):
    """Test a single URL"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"Expected: {expected_result.upper()}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(API_BASE, json={"url": url}, timeout=10)
        
        if response.status_code != 200:
            print(f"ERROR: API Error: {response.status_code}")
            print(f"   {response.text}")
            return False
        
        result = response.json()
        
        score = result.get('score', 0)
        is_scam = result.get('is_scam', False)
        recommendation = result.get('recommendation', 'UNKNOWN')
        reasons = result.get('reasons', [])
        domain = result.get('domain', 'N/A')
        domain_age = result.get('domain_age_days', 'N/A')
        
        print(f"\nResults:")
        print(f"   Score: {score}/100")
        print(f"   Is Scam: {is_scam}")
        print(f"   Recommendation: {recommendation}")
        print(f"   Domain: {domain}")
        if domain_age != 'N/A' and domain_age is not None:
            print(f"   Domain Age: {domain_age} days")
        
        if reasons:
            print(f"\n   Reasons:")
            for reason in reasons[:3]:  # Show first 3 reasons
                print(f"     • {reason}")
        
        # Check if result matches expectation
        if expected_result == "safe":
            if is_scam:
                print(f"\nWARNING: UNEXPECTED - Site flagged as scam but should be safe!")
                print(f"   This might be a false positive or the site is actually suspicious")
                return False
            else:
                print(f"\nOK: CORRECT - Site correctly identified as safe")
                return True
        elif expected_result == "scam":
            if not is_scam:
                print(f"\nWARNING: UNEXPECTED - Site not flagged but should be suspicious!")
                print(f"   Score: {score}/100 (threshold: 80)")
                if score < 80:
                    print(f"   Score too low - might need adjustment")
                return False
            else:
                print(f"\nOK: CORRECT - Site correctly flagged as suspicious")
                return True
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to backend!")
        print(f"   Make sure backend is running: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("VeriSight Multi-Site Testing")
    print("=" * 60)
    print("\nThis script tests VeriSight against multiple real websites")
    print("Make sure the backend is running: cd backend && python main.py\n")
    
    # Test backend connection first
    try:
        health = requests.get("http://localhost:8000/health", timeout=2)
        if health.status_code != 200:
            print("ERROR: Backend is not responding correctly!")
            sys.exit(1)
    except:
        print("ERROR: Cannot connect to backend server!")
        print("   Start it with: cd backend && python main.py")
        sys.exit(1)
    
    print("OK: Backend is running\n")
    
    # Test all URLs
    results = []
    for url, name, expected in TEST_URLS:
        try:
            success = test_url(url, name, expected)
            results.append((name, success))
        except KeyboardInterrupt:
            print("\n\nWARNING: Test interrupted by user")
            break
        except Exception as e:
            print(f"\nERROR: Unexpected error testing {name}: {e}")
            results.append((name, False))
        
        time.sleep(0.5)  # Small delay between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nSUCCESS: All tests passed!")
        return 0
    else:
        print(f"\nWARNING: {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
