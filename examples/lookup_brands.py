"""
Example: Using VeriSight Brand Lookup API
Demonstrates how to dynamically add and manage brands
"""
import requests
import json

API_BASE = "http://localhost:8000"

def example_lookup_brand():
    """Example: Automatically scrape and add a brand"""
    print("Looking up brand from GitHub...")
    
    response = requests.post(f"{API_BASE}/api/brands/lookup", json={
        "url": "https://github.com"
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"{result['message']}")
        print(f"   Brand: {result['brand']['brand_name']}")
        print(f"   Domains: {', '.join(result['brand']['official_domains'])}")
        if result['brand'].get('logo_hash'):
            print(f"   Logo hash extracted: {result['brand']['logo_hash'][:30]}...")
    else:
        print(f"Error: {response.text}")

def example_lookup_and_check():
    """Example: Lookup brand and immediately check if it's a scam"""
    print("\nLooking up and checking suspicious site...")
    
    response = requests.post(f"{API_BASE}/api/brands/lookup-and-check", json={
        "url": "https://suspicious-site.com"
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"Lookup: {result['lookup']['message']}")
        print(f"   Scam Score: {result['scam_check']['score']}/100")
        print(f"   Recommendation: {result['scam_check']['recommendation']}")
    else:
        print(f"Error: {response.text}")

def example_search_brands():
    """Example: Search for brands"""
    print("\nSearching for 'paypal' brands...")
    
    response = requests.get(f"{API_BASE}/api/brands/search", params={"q": "paypal"})
    
    if response.status_code == 200:
        result = response.json()
        print(f"Found {result['count']} brand(s)")
        for key, brand in result['results'].items():
            print(f"   - {brand['brand_name']} ({', '.join(brand['official_domains'])})")
    else:
        print(f"Error: {response.text}")

def example_add_brand_manually():
    """Example: Manually add a brand"""
    print("\nManually adding a brand...")
    
    response = requests.post(f"{API_BASE}/api/brands", json={
        "brand_name": "ExampleBrand",
        "official_domains": ["example.com", "example.org"],
        "primary_color": "#FF5733",
        "font_family": "Arial, sans-serif"
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"{result['message']}")
    else:
        print(f"Error: {response.text}")

def example_list_all_brands():
    """Example: List all brands in database"""
    print("\nListing all brands...")
    
    response = requests.get(f"{API_BASE}/api/brands")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Found {len(result['brands'])} brand(s) in database:")
        for key, brand in result['brands'].items():
            print(f"   - {brand['brand_name']} ({', '.join(brand['official_domains'])})")
    else:
        print(f"Error: {response.text}")

if __name__ == '__main__':
    print("VeriSight Brand Lookup Examples\n")
    
    try:
        # Test if backend is running
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code != 200:
            print("Backend server is not running!")
            print("   Start it with: cd backend && python main.py")
            exit(1)
    except requests.exceptions.RequestException:
        print("Cannot connect to backend server!")
        print("   Make sure it's running on http://localhost:8000")
        exit(1)
    
    # Run examples
    example_list_all_brands()
    example_lookup_brand()
    example_search_brands()
    example_add_brand_manually()
    example_list_all_brands()
    
    print("\nExamples completed!")
