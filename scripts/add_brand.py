#!/usr/bin/env python3
"""
CLI tool to add brands to VeriSight database
Usage: python add_brand.py <url> [--name NAME] [--domains DOMAIN1,DOMAIN2]
"""
import sys
import argparse
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from backend.brand_scraper import BrandScraper
    from backend.brand_fingerprints import BrandDatabase
except ImportError:
    from brand_scraper import BrandScraper
    from brand_fingerprints import BrandDatabase

def main():
    parser = argparse.ArgumentParser(description='Add a brand to VeriSight database')
    parser.add_argument('url', help='URL of the brand website')
    parser.add_argument('--name', help='Override brand name')
    parser.add_argument('--domains', help='Comma-separated list of official domains')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite if brand exists')
    parser.add_argument('--no-scrape', action='store_true', help='Skip scraping, use manual values only')
    
    args = parser.parse_args()
    
    print(f"Looking up brand from {args.url}...")
    
    scraper = BrandScraper()
    db = BrandDatabase()
    
    # Scrape brand information
    if not args.no_scrape:
        brand_data = scraper.scrape_brand(args.url)
        if not brand_data:
            print("Failed to scrape brand information")
            return 1
    else:
        # Manual entry
        domain = scraper.extract_domain(args.url)
        brand_data = {
            'brand_name': args.name or domain.split('.')[0].title(),
            'official_domains': args.domains.split(',') if args.domains else [domain],
            'logo_hash': None,
            'primary_color': None,
            'font_family': None
        }
    
    # Override with manual values if provided
    if args.name:
        brand_data['brand_name'] = args.name
    if args.domains:
        brand_data['official_domains'] = [d.strip() for d in args.domains.split(',')]
    
    # Add to database
    success = db.add_brand(
        brand_name=brand_data['brand_name'],
        official_domains=brand_data['official_domains'],
        logo_hash=brand_data.get('logo_hash'),
        primary_color=brand_data.get('primary_color'),
        font_family=brand_data.get('font_family'),
        overwrite=args.overwrite
    )
    
    if success:
        print(f"Brand '{brand_data['brand_name']}' added successfully!")
        print(f"   Domains: {', '.join(brand_data['official_domains'])}")
        if brand_data.get('logo_hash'):
            print(f"   Logo hash: {brand_data['logo_hash'][:20]}...")
        return 0
    else:
        print(f"Brand '{brand_data['brand_name']}' already exists. Use --overwrite to update.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
