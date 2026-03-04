"""
Test script to verify VeriSight extension is working
Checks if backend is running and tests the detection
"""
import requests
import sys
import json

API_BASE = "http://localhost:8000"

def test_backend_running():
    """Test if backend is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code == 200:
            print("Backend server is running")
            return True
        else:
            print(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("Backend server is NOT running!")
        print("   Start it with: cd backend && python main.py")
        return False
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return False

def test_fake_site_detection():
    """Test if fake PayPal site would be detected"""
    print("\nTesting fake site detection...")
    
    test_urls = [
        "http://localhost:8000/fake-paypal.html",
        "http://127.0.0.1:8000/fake-paypal.html"
    ]
    
    for url in test_urls:
        try:
            response = requests.post(f"{API_BASE}/api/check-scam", json={"url": url}, timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"\nResults for {url}:")
                print(f"   Score: {result['score']}/100")
                print(f"   Is Scam: {result['is_scam']}")
                print(f"   Recommendation: {result['recommendation']}")
                print(f"   Reasons:")
                for reason in result['reasons']:
                    print(f"     - {reason}")
                
                if result['is_scam']:
                    print(f"\nSite would be BLOCKED by VeriSight")
                else:
                    print(f"\nSite would be ALLOWED (might need adjustment)")
            else:
                print(f"API returned status {response.status_code}")
        except Exception as e:
            print(f"Error testing {url}: {e}")

def print_extension_setup():
    """Print instructions for extension setup"""
    print("\n" + "="*60)
    print("EXTENSION SETUP CHECKLIST")
    print("="*60)
    print("\n1. Backend is running (you verified this)")
    print("\n2. Load Extension in Chrome:")
    print("   - Open Chrome → chrome://extensions/")
    print("   - Enable 'Developer mode' (top-right toggle)")
    print("   - Click 'Load unpacked'")
    print("   - Select the 'frontend' folder")
    print("\n3. Check Extension is Active:")
    print("   - Look for VeriSight icon in Chrome toolbar")
    print("   - Click it to open popup")
    print("   - Should show 'Checking...' or status")
    print("\n4. Debug Extension:")
    print("   - Press F12 on any webpage")
    print("   - Check Console tab for [VeriSight] messages")
    print("   - Should see 'Analyzing page...' on page load")
    print("\n5. Test on Fake Site:")
    print("   - Visit: http://localhost:8000/fake-paypal.html")
    print("   - Open Console (F12)")
    print("   - Should see [VeriSight] logs")
    print("   - If blocked, you'll see red overlay")
    print("\n6. If Extension Still Not Working:")
    print("   - Check background.js console:")
    print("     * Go to chrome://extensions/")
    print("     * Find VeriSight")
    print("     * Click 'service worker' (if shown)")
    print("   - Check content script console (F12 on page)")
    print("   - Verify backend URL in extension files matches")
    print("     * background.js line 6: API_URL")
    print("="*60)

if __name__ == '__main__':
    print("VeriSight Extension Test\n")
    
    # Test backend
    if not test_backend_running():
        print("\nBackend must be running for extension to work!")
        print("   Fix this first, then rerun this script.")
        sys.exit(1)
    
    # Test fake site detection
    test_fake_site_detection()
    
    # Print setup instructions
    print_extension_setup()
