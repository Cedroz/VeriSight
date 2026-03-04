"""
Test VeriSight detection on notrealtwitter.com
This is a real suspicious site that should be flagged
"""
import requests
import json

API_BASE = "http://localhost:8000/api/check-scam"

def test_notrealtwitter():
    print("Testing: https://notrealtwitter.com/")
    print("=" * 70)
    print("\nThis site should be flagged because:")
    print("  1. Domain contains 'notreal' (obvious fake indicator)")
    print("  2. Domain contains 'twitter' but isn't twitter.com")
    print("  3. Should get high scam score\n")
    
    try:
        response = requests.post(API_BASE, json={"url": "https://notrealtwitter.com/"}, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"Score: {result['score']}/100")
            print(f"Is Scam: {result['is_scam']}")
            print(f"Recommendation: {result['recommendation']}")
            print(f"\nReasons:")
            for reason in result['reasons']:
                print(f"  - {reason}")
            
            if result['is_scam']:
                print(f"\n>>> CORRECTLY FLAGGED AS SUSPICIOUS!")
            else:
                print(f"\n>>> NOT FLAGGED (might need backend restart or improvements)")
                print(f"   Current score: {result['score']}/100 (threshold: 80)")
        else:
            print(f"ERROR: API returned {response.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    test_notrealtwitter()
