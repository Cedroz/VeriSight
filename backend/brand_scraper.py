"""
Brand Scraper - Extracts brand fingerprints from websites
Can be used to dynamically add brands to the database
"""
import requests
from urllib.parse import urlparse
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    print("Warning: BeautifulSoup4 not installed. Install with: pip install beautifulsoup4")

from typing import Optional, Dict, List
from PIL import Image
import imagehash
import io
import re

class BrandScraper:
    """Scrapes brand information from websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_domain(self, url: str) -> str:
        """Extract clean domain from URL"""
        parsed = urlparse(url if url.startswith('http') else f'http://{url}')
        domain = parsed.netloc or parsed.path.split('/')[0]
        return domain.replace('www.', '').lower()
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse HTML page"""
        if BeautifulSoup is None:
            raise ImportError("BeautifulSoup4 is required for scraping. Install with: pip install beautifulsoup4")
        
        try:
            if not url.startswith('http'):
                url = f'https://{url}'
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return None
    
    def extract_logo(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """
        Extract logo from page and return as base64 hash
        Tries multiple strategies:
        1. Open Graph image (og:image)
        2. Favicon
        3. First large image in header
        4. Logo class/id patterns
        """
        logo_url = None
        
        # Strategy 1: Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            logo_url = og_image['content']
        
        # Strategy 2: Favicon
        if not logo_url:
            favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            if favicon and favicon.get('href'):
                logo_url = favicon['href']
        
        # Strategy 3: Logo class/id patterns
        if not logo_url:
            logo_patterns = [
                soup.find(class_=re.compile('logo', re.I)),
                soup.find(id=re.compile('logo', re.I)),
                soup.find('img', class_=re.compile('logo', re.I)),
                soup.find('img', id=re.compile('logo', re.I))
            ]
            for elem in logo_patterns:
                if elem and elem.get('src'):
                    logo_url = elem['src']
                    break
        
        # Strategy 4: First large image in header
        if not logo_url:
            header = soup.find('header') or soup.find('nav')
            if header:
                img = header.find('img')
                if img and img.get('src'):
                    logo_url = img['src']
        
        if not logo_url:
            return None
        
        # Make absolute URL
        parsed_base = urlparse(base_url if base_url.startswith('http') else f'https://{base_url}')
        if logo_url.startswith('//'):
            logo_url = f'{parsed_base.scheme}:{logo_url}'
        elif logo_url.startswith('/'):
            logo_url = f'{parsed_base.scheme}://{parsed_base.netloc}{logo_url}'
        elif not logo_url.startswith('http'):
            logo_url = f'{parsed_base.scheme}://{parsed_base.netloc}/{logo_url}'
        
        # Download and hash logo
        try:
            img_response = self.session.get(logo_url, timeout=5)
            img_response.raise_for_status()
            image = Image.open(io.BytesIO(img_response.content))
            logo_hash = str(imagehash.phash(image))
            return logo_hash
        except Exception as e:
            print(f"Failed to process logo from {logo_url}: {e}")
            return None
    
    def extract_colors(self, soup: BeautifulSoup) -> List[str]:
        """Extract primary colors from page (CSS, meta tags)"""
        colors = []
        
        # Check meta theme-color
        theme_color = soup.find('meta', name='theme-color')
        if theme_color and theme_color.get('content'):
            colors.append(theme_color['content'])
        
        # Extract from inline styles and CSS
        style_tags = soup.find_all('style')
        color_pattern = re.compile(r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b|rgb\([^)]+\)')
        for style in style_tags:
            matches = color_pattern.findall(str(style.string or ''))
            if matches:
                colors.extend(matches[:3])  # Top 3 colors
        
        return colors[:1] if colors else [None]
    
    def extract_fonts(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract primary font family from page"""
        # Check body/font-family in style tags
        style_tags = soup.find_all('style')
        font_pattern = re.compile(r'font-family:\s*([^;]+)')
        for style in style_tags:
            matches = font_pattern.findall(str(style.string or ''))
            if matches:
                return matches[0].strip()
        
        # Check inline styles
        body = soup.find('body')
        if body and body.get('style'):
            font_match = font_pattern.search(body['style'])
            if font_match:
                return font_match.group(1).strip()
        
        return None
    
    def scrape_brand(self, url: str) -> Optional[Dict]:
        """
        Scrape brand information from a URL
        Returns dict with brand_name, domains, logo_hash, etc.
        """
        soup = self.fetch_page(url)
        if not soup:
            return None
        
        domain = self.extract_domain(url)
        
        # Extract brand name from title or domain
        title = soup.find('title')
        brand_name = None
        if title and title.string:
            brand_name = title.string.strip().split(' - ')[0].split(' | ')[0]
            brand_name = re.sub(r'\s+', ' ', brand_name).strip()
        
        # Fallback to domain-based name
        if not brand_name:
            brand_name = domain.split('.')[0].title()
        
        # Extract logo
        logo_hash = self.extract_logo(soup, url)
        
        # Extract colors
        colors = self.extract_colors(soup)
        primary_color = colors[0] if colors else None
        
        # Extract fonts
        font_family = self.extract_fonts(soup)
        
        return {
            'brand_name': brand_name,
            'official_domains': [domain],
            'logo_hash': logo_hash,
            'primary_color': primary_color,
            'font_family': font_family
        }
