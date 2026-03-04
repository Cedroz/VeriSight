"""
Test VeriSight detection with various suspicious URL patterns
This simulates how detection would work on real fake sites
"""
import requests
import json

API_BASE = "http://localhost:8000/api/check-scam"

# Test URLs that simulate real suspicious patterns
# These aren't real domains, but test the detection logic
SUSPICIOUS_PATTERNS = [
    ("http://paypal-secure-login.net", "PayPal secure pattern"),
    ("http://arnazon.com/login", "Amazon typo (arnazon)"),
    ("http://paypa1.com", "PayPal typo (paypa1)"),
    ("http://n1ke.com/shop", "Nike typo (n1ke)"),
    ("http://chase-bank-secure.com", "Chase bank pattern"),
    ("http://amazon-verify-account.com", "Amazon verify pattern"),
    ("http://paypal-secure-account-update.net", "PayPal secure pattern"),
]

# Legitimate patterns (should be safe)
SAFE_PATTERNS = [
    ("https://www.paypal.com", "Real PayPal"),
    ("https://www.amazon.com", "Real Amazon"),
]

def test_pattern(url, description):
    """Test a URL pattern"""
    print(f"\nTesting: {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.post(API_BASE, json={"url": url}, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"  Score: {result['score']}/100")
            print(f"  Is Scam: {result['is_scam']}")
            print(f"  Reasons:")
            for reason in result['reasons'][:2]:
                print(f"    - {reason}")
            
            if result['is_scam']:
                print(f"  >>> DETECTED AS SUSPICIOUS")
            else:
                print(f"  >>> Would be allowed")
        else:
            print(f"  ERROR: API returned {response.status_code}")
    except Exception as e:
        print(f"  ERROR: {e}")

def main():
    print("=" * 70)
    print("Testing VeriSight Suspicious Pattern Detection")
    print("=" * 70)
    print("\nThese tests simulate how VeriSight would detect real fake sites")
    print("using URL pattern matching (works on any domain).\n")
    
    # Test suspicious patterns
    print("\n" + "=" * 70)
    print("SUSPICIOUS PATTERNS (Should be flagged)")
    print("=" * 70)
    for url, desc in SUSPICIOUS_PATTERNS:
        test_pattern(url, desc)
    
    # Test safe patterns
    print("\n" + "=" * 70)
    print("LEGITIMATE PATTERNS (Should be safe)")
    print("=" * 70)
    for url, desc in SAFE_PATTERNS:
        test_pattern(url, desc)
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("\nIf suspicious patterns get high scores, VeriSight will work")
    print("on real fake sites with similar URL patterns!")
    print("\nReal fake sites often use these exact patterns:")
    print("  - Typos: paypa1.com, arnazon.com")
    print("  - Suspicious strings: paypal-secure, amazon-verify")
    print("  - New domains: registered days before phishing campaign")

if __name__ == '__main__':
    main()
