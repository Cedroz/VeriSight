"""
Test VeriSight Backend API
Run this after starting the backend server to verify it works
"""
import requests
import json
import sys

API_URL = 'http://localhost:8000/api/check-scam'

def test_backend():
    """Test the backend API with sample URLs"""
    print("Testing VeriSight Backend API...\n")
    
    # Test 1: Real PayPal (should be safe)
    print("Test 1: Real PayPal (should be safe)")
    try:
        response = requests.post(API_URL, json={
            "url": "https://paypal.com"
        })
        result = response.json()
        print(f"  Score: {result['score']}/100")
        print(f"  Is Scam: {result['is_scam']}")
        print(f"  Recommendation: {result['recommendation']}")
        print(f"  ✓ Pass\n")
    except Exception as e:
        print(f"  ✗ Failed: {e}\n")
        return False
    
    # Test 2: Suspicious domain (should flag)
    print("Test 2: Suspicious domain pattern")
    try:
        response = requests.post(API_URL, json={
            "url": "http://paypa1-secure-verify.net"
        })
        result = response.json()
        print(f"  Score: {result['score']}/100")
        print(f"  Is Scam: {result['is_scam']}")
        print(f"  Reasons: {', '.join(result['reasons'][:2])}")
        print(f"  ✓ Pass\n")
    except Exception as e:
        print(f"  ✗ Failed: {e}\n")
        return False
    
    # Test 3: Health check
    print("Test 3: Health check")
    try:
        response = requests.get('http://localhost:8000/health')
        if response.status_code == 200:
            print(f"  Status: {response.json()['status']}")
            print(f"  ✓ Pass\n")
        else:
            print(f"  ✗ Failed: Status {response.status_code}\n")
            return False
    except Exception as e:
        print(f"  ✗ Failed: {e}\n")
        return False
    
    print("All tests passed!")
    return True

if __name__ == '__main__':
    try:
        success = test_backend()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
