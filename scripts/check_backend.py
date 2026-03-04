"""
Quick script to check if VeriSight backend is running
"""
import sys

try:
    import requests
except ImportError:
    print("'requests' module not installed")
    print("   Install with: pip install requests")
    sys.exit(1)

def check_backend():
    """Check if backend is running"""
    base_url = "http://localhost:8000"
    
    print("Checking VeriSight backend...\n")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        if response.status_code == 200:
            print(f"OK: Backend is running!")
            print(f"   Health: {response.json()}")
        else:
            print(f"Backend responded with status {response.status_code}")
            print(f"   Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend!")
        print("\n   Backend is NOT running. Start it with:")
        print("   cd backend")
        print("   python main.py")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=2)
        print(f"\nRoot endpoint: {response.json()}")
    except Exception as e:
        print(f"\nRoot endpoint error: {e}")
    
    # Test check-scam endpoint
    print("\nTesting check-scam endpoint with fake site...")
    try:
        response = requests.post(
            f"{base_url}/api/check-scam",
            json={"url": "http://localhost:8000/fake-paypal.html"},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            print(f"API working!")
            print(f"   Score: {result['score']}/100")
            print(f"   Is Scam: {result['is_scam']}")
            print(f"   Recommendation: {result['recommendation']}")
            if result['is_scam']:
                print(f"\n   Fake site would be BLOCKED!")
            else:
                print(f"\n   Fake site would be ALLOWED (might need adjustment)")
        else:
            print(f"API returned status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"Error testing API: {e}")
    
    return True

if __name__ == '__main__':
    check_backend()
