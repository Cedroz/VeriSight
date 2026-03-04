"""
Brand Fingerprint Database Generator
Creates visual fingerprints for major brands (logos, colors, fonts)
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import imagehash
from PIL import Image

class BrandFingerprint:
    """Stores visual fingerprint data for a brand"""
    def __init__(self, brand_name: str, official_domains: List[str], 
                 logo_hash: Optional[str] = None, 
                 primary_color: Optional[str] = None,
                 font_family: Optional[str] = None):
        self.brand_name = brand_name
        self.official_domains = official_domains
        self.logo_hash = logo_hash
        self.primary_color = primary_color
        self.font_family = font_family
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return {
            'brand_name': self.brand_name,
            'official_domains': self.official_domains,
            'logo_hash': self.logo_hash,
            'primary_color': self.primary_color,
            'font_family': self.font_family
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BrandFingerprint':
        """Create from dictionary"""
        return cls(
            brand_name=data['brand_name'],
            official_domains=data['official_domains'],
            logo_hash=data.get('logo_hash'),
            primary_color=data.get('primary_color'),
            font_family=data.get('font_family')
        )

class BrandDatabase:
    """Manages brand fingerprint database"""
    def __init__(self, db_path: str = "brands.db.json"):
        self.db_path = db_path
        self.brands: Dict[str, BrandFingerprint] = {}
        self.load_database()
    
    def load_database(self):
        """Load brand database from JSON file"""
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                self.brands = {
                    name: BrandFingerprint.from_dict(brand_data)
                    for name, brand_data in data.items()
                }
        else:
            # Initialize with default brands (manually curated data)
            self._initialize_default_brands()
            self.save_database()
    
    def _initialize_default_brands(self):
        """Initialize database with 5 major brands"""
        # These would normally be scraped from real sites
        # For MVP, we'll use manual entries
        
        # Amazon
        self.brands['amazon'] = BrandFingerprint(
            brand_name='Amazon',
            official_domains=['amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.ca'],
            primary_color='#FF9900',  # Amazon's signature orange
            font_family='Arial, sans-serif'
        )
        
        # Nike
        self.brands['nike'] = BrandFingerprint(
            brand_name='Nike',
            official_domains=['nike.com'],
            primary_color='#000000',  # Nike's black
            font_family='Helvetica Neue, Arial, sans-serif'
        )
        
        # Apple
        self.brands['apple'] = BrandFingerprint(
            brand_name='Apple',
            official_domains=['apple.com', 'apple.com.cn'],
            primary_color='#000000',
            font_family='SF Pro Display, Helvetica Neue, sans-serif'
        )
        
        # Chase Bank
        self.brands['chase'] = BrandFingerprint(
            brand_name='Chase',
            official_domains=['chase.com'],
            primary_color='#1E69B8',  # Chase blue
            font_family='Arial, sans-serif'
        )
        
        # PayPal
        self.brands['paypal'] = BrandFingerprint(
            brand_name='PayPal',
            official_domains=['paypal.com', 'paypal.com/us'],
            primary_color='#0070BA',  # PayPal blue
            font_family='Arial, sans-serif'
        )
        
        # Twitter/X
        self.brands['twitter'] = BrandFingerprint(
            brand_name='Twitter',
            official_domains=['twitter.com', 'x.com'],
            primary_color='#1DA1F2',  # Twitter blue
            font_family='Helvetica Neue, Arial, sans-serif'
        )
        
        # Pandora
        self.brands['pandora'] = BrandFingerprint(
            brand_name='Pandora',
            official_domains=['pandora.com', 'pandora.net'],
            primary_color='#005483',  # Pandora blue
            font_family='Arial, sans-serif'
        )
    
    def save_database(self):
        """Save brand database to JSON file"""
        data = {
            name: brand.to_dict()
            for name, brand in self.brands.items()
        }
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_logo_hash(self, brand_name: str, logo_path: str):
        """Generate and store logo hash for a brand"""
        if brand_name.lower() not in self.brands:
            raise ValueError(f"Brand {brand_name} not found in database")
        
        try:
            # Load and hash the logo
            img = Image.open(logo_path)
            hash_value = str(imagehash.phash(img))
            self.brands[brand_name.lower()].logo_hash = hash_value
            self.save_database()
            return hash_value
        except Exception as e:
            raise ValueError(f"Failed to process logo: {e}")
    
    def find_brand_by_domain(self, domain: str) -> Optional[BrandFingerprint]:
        """Find brand by domain match"""
        domain_lower = domain.lower().replace('www.', '')
        for brand in self.brands.values():
            for official_domain in brand.official_domains:
                if official_domain in domain_lower or domain_lower in official_domain:
                    return brand
        return None
    
    def add_brand(self, brand_name: str, official_domains: List[str],
                  logo_hash: Optional[str] = None,
                  primary_color: Optional[str] = None,
                  font_family: Optional[str] = None,
                  overwrite: bool = False) -> bool:
        """
        Add a new brand to the database
        Returns True if added, False if already exists (unless overwrite=True)
        """
        key = brand_name.lower().replace(' ', '_')
        
        if key in self.brands and not overwrite:
            return False
        
        self.brands[key] = BrandFingerprint(
            brand_name=brand_name,
            official_domains=official_domains,
            logo_hash=logo_hash,
            primary_color=primary_color,
            font_family=font_family
        )
        self.save_database()
        return True
    
    def update_brand(self, brand_name: str, **updates) -> bool:
        """Update brand properties"""
        key = brand_name.lower().replace(' ', '_')
        if key not in self.brands:
            return False
        
        brand = self.brands[key]
        if 'official_domains' in updates:
            brand.official_domains = updates['official_domains']
        if 'logo_hash' in updates:
            brand.logo_hash = updates['logo_hash']
        if 'primary_color' in updates:
            brand.primary_color = updates['primary_color']
        if 'font_family' in updates:
            brand.font_family = updates['font_family']
        
        self.save_database()
        return True
    
    def delete_brand(self, brand_name: str) -> bool:
        """Delete a brand from database"""
        key = brand_name.lower().replace(' ', '_')
        if key in self.brands:
            del self.brands[key]
            self.save_database()
            return True
        return False
    
    def search_brands(self, query: str) -> Dict[str, Dict]:
        """Search brands by name or domain"""
        query_lower = query.lower()
        results = {}
        
        for key, brand in self.brands.items():
            if (query_lower in brand.brand_name.lower() or
                any(query_lower in domain.lower() for domain in brand.official_domains)):
                results[key] = brand.to_dict()
        
        return results
    
    def compare_logo_hash(self, image_hash: str, threshold: int = 5) -> Optional[str]:
        """
        Compare image hash against all brands
        Returns brand name if match found, None otherwise
        threshold: maximum hamming distance (lower = stricter match)
        """
        if not image_hash:
            return None
        
        best_match = None
        best_distance = float('inf')
        
        for brand_name, brand in self.brands.items():
            if brand.logo_hash:
                try:
                    hash1 = imagehash.hex_to_hash(image_hash)
                    hash2 = imagehash.hex_to_hash(brand.logo_hash)
                    distance = hash1 - hash2
                    
                    if distance < best_distance and distance <= threshold:
                        best_distance = distance
                        best_match = brand_name
                except:
                    continue
        
        return best_match
