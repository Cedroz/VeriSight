#!/usr/bin/env python3
"""
CLI tool to search brands in VeriSight database
Usage: python search_brands.py <query>
"""
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from backend.brand_fingerprints import BrandDatabase
except ImportError:
    from brand_fingerprints import BrandDatabase

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_brands.py <query>")
        print("Example: python search_brands.py paypal")
        return 1
    
    query = ' '.join(sys.argv[1:])
    
    db = BrandDatabase()
    results = db.search_brands(query)
    
    if not results:
        print(f"No brands found matching '{query}'")
        return 1
    
    print(f"Found {len(results)} brand(s) matching '{query}':\n")
    
    for key, brand in results.items():
        print(f"📌 {brand['brand_name']}")
        print(f"   Key: {key}")
        print(f"   Domains: {', '.join(brand['official_domains'])}")
        if brand.get('logo_hash'):
            print(f"   Logo hash: {brand['logo_hash'][:30]}...")
        if brand.get('primary_color'):
            print(f"   Primary color: {brand['primary_color']}")
        print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
