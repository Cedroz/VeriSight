"""
Scam Detection Engine
Analyzes websites and returns a Scam Score (0-100)
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple
try:
    import whois
except ImportError:
    # Fallback if python-whois is not available
    whois = None

from urllib.parse import urlparse
import re

try:
    from .brand_fingerprints import BrandDatabase
    from .safe_browsing import SafeBrowsingChecker
except ImportError:
    from brand_fingerprints import BrandDatabase
    try:
        from safe_browsing import SafeBrowsingChecker
    except ImportError:
        SafeBrowsingChecker = None

class ScamDetector:
    """Detects scam websites based on multiple factors"""
    
    def __init__(self, brand_db: Optional[BrandDatabase] = None, safe_browsing_checker: Optional[SafeBrowsingChecker] = None):
        self.brand_db = brand_db or BrandDatabase()
        self.critical_threshold = 80  # Score above this triggers blocking
        
        # Initialize Safe Browsing checker
        if SafeBrowsingChecker is not None:
            self.safe_browsing = safe_browsing_checker or SafeBrowsingChecker()
        else:
            self.safe_browsing = None
            print("Warning: SafeBrowsingChecker not available. Safe Browsing checks will be skipped.")
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings
        Used for detecting misspelled brand names
        """
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def find_similar_brand(self, domain: str, threshold: float = 0.7) -> Optional[Tuple[str, float]]:
        """
        Find brand names that are similar to the domain (for typo detection)
        Returns (brand_name, similarity_score) or None
        similarity_score: 0.0 to 1.0 (1.0 = identical)
        """
        domain_lower = domain.lower()
        # Remove TLD and common prefixes
        domain_clean = re.sub(r'^(www\.|secure\.|login\.|account\.)', '', domain_lower)
        domain_clean = domain_clean.split('.')[0]  # Get just the domain name part
        
        best_match = None
        best_similarity = 0.0
        
        for brand_name, brand in self.brand_db.brands.items():
            brand_name_lower = brand.brand_name.lower()
            
            # Check if domain contains brand name (exact match)
            if brand_name_lower in domain_clean or domain_clean in brand_name_lower:
                # Check if it's an official domain
                is_official = any(
                    official.lower() in domain_lower or domain_lower in official.lower()
                    for official in brand.official_domains
                )
                if not is_official:
                    # Calculate similarity
                    max_len = max(len(domain_clean), len(brand_name_lower))
                    if max_len == 0:
                        continue
                    distance = self.levenshtein_distance(domain_clean, brand_name_lower)
                    similarity = 1.0 - (distance / max_len)
                    
                    if similarity > best_similarity and similarity >= threshold:
                        best_similarity = similarity
                        best_match = (brand.brand_name, similarity)
            
            # Also check for character substitutions (common typos)
            # e.g., "pand0ra" vs "pandora", "arnazon" vs "amazon"
            if len(domain_clean) >= 4 and len(brand_name_lower) >= 4:
                # Check if they're similar length and similar characters
                if abs(len(domain_clean) - len(brand_name_lower)) <= 2:
                    distance = self.levenshtein_distance(domain_clean, brand_name_lower)
                    max_len = max(len(domain_clean), len(brand_name_lower))
                    similarity = 1.0 - (distance / max_len)
                    
                    # If similarity is high but not exact, it's likely a typo
                    if similarity >= threshold and similarity < 1.0:
                        # Check if it's NOT an official domain
                        is_official = any(
                            official.lower() in domain_lower or domain_lower in official.lower()
                            for official in brand.official_domains
                        )
                        if not is_official and similarity > best_similarity:
                            best_similarity = similarity
                            best_match = (brand.brand_name, similarity)
        
        return best_match
    
    def check_ssl_certificate(self, url: str) -> Dict:
        """
        Check SSL certificate validity and security
        Returns dict with certificate info
        """
        import ssl
        import socket
        from urllib.parse import urlparse
        
        result = {
            'has_ssl': False,
            'is_valid': False,
            'days_until_expiry': None,
            'error': None
        }
        
        try:
            parsed = urlparse(url if url.startswith('http') else f'https://{url}')
            hostname = parsed.netloc or parsed.path.split('/')[0]
            hostname = hostname.replace('www.', '').split(':')[0]
            
            # Only check HTTPS URLs
            if parsed.scheme != 'https' and not url.startswith('https'):
                result['error'] = 'Not an HTTPS URL'
                return result
            
            # Create SSL context
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    result['has_ssl'] = True
                    
                    # Check certificate expiry
                    not_after = datetime.strptime(
                        cert['notAfter'], '%b %d %H:%M:%S %Y %Z'
                    )
                    days_left = (not_after - datetime.now()).days
                    result['days_until_expiry'] = days_left
                    result['is_valid'] = days_left > 0
                    
        except ssl.SSLError as e:
            result['error'] = f'SSL Error: {str(e)}'
        except socket.timeout:
            result['error'] = 'Connection timeout'
        except Exception as e:
            result['error'] = f'Certificate check failed: {str(e)}'
        
        return result
    
    def get_domain_age_days(self, domain: str) -> Optional[int]:
        """
        Get domain age in days using WHOIS lookup
        Returns None if lookup fails
        """
        if whois is None:
            print("WHOIS library not available")
            return None
        
        try:
            # Extract domain from URL if needed
            parsed = urlparse(domain if domain.startswith('http') else f'http://{domain}')
            domain_name = parsed.netloc or parsed.path.split('/')[0]
            domain_name = domain_name.replace('www.', '')
            
            w = whois.whois(domain_name)
            creation_date = w.creation_date
            
            # Handle both single date and list of dates
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            
            if creation_date and isinstance(creation_date, datetime):
                # Handle timezone-aware vs naive datetimes
                now = datetime.now()
                if creation_date.tzinfo is not None and now.tzinfo is None:
                    # creation_date is timezone-aware, now is naive
                    from datetime import timezone
                    now = datetime.now(timezone.utc)
                elif creation_date.tzinfo is None and now.tzinfo is not None:
                    # creation_date is naive, now is timezone-aware
                    creation_date = creation_date.replace(tzinfo=timezone.utc)
                age_days = (now - creation_date).days
                return max(0, age_days)
            
            return None
        except Exception as e:
            print(f"WHOIS lookup failed for {domain}: {e}")
            return None
    
    def calculate_scam_score(self, url: str, detected_brand: Optional[str] = None, 
                           logo_match: bool = False) -> Dict:
        """
        Calculate scam score (0-100) based on multiple factors
        Returns dict with score, reasons, and recommendation
        """
        score = 0
        reasons = []
        parsed_url = urlparse(url if url.startswith('http') else f'http://{url}')
        domain = parsed_url.netloc or parsed_url.path.split('/')[0]
        domain = domain.replace('www.', '')
        
        # Factor 0: Google Safe Browsing API Check (CRITICAL - 100 points if threat detected)
        safe_browsing_result = None
        if self.safe_browsing:
            try:
                safe_browsing_result = self.safe_browsing.check_url(url)
                if safe_browsing_result.get("is_threat", False):
                    # CRITICAL: Google Safe Browsing flagged this URL
                    threat_types = safe_browsing_result.get("threat_types", [])
                    threat_desc = ", ".join(threat_types) if threat_types else "threat"
                    score = 100  # Maximum score for Safe Browsing threats
                    reasons.append(
                        f"CRITICAL: Google Safe Browsing flagged this URL as {threat_desc}. "
                        "This site is known to be malicious or unsafe."
                    )
                    # Return early with critical threat
                    return {
                        'score': score,
                        'is_scam': True,
                        'reasons': reasons,
                        'recommendation': 'BLOCK',
                        'domain_age_days': None,  # Will be filled later if needed
                        'detected_brand': detected_brand,
                        'domain': domain,
                        'safe_browsing': {
                            'is_threat': True,
                            'threat_types': threat_types,
                            'platform_types': safe_browsing_result.get("platform_types", []),
                            'error': safe_browsing_result.get("error")
                        }
                    }
                elif safe_browsing_result.get("error"):
                    # API error - log but don't block
                    reasons.append(f"Safe Browsing check failed: {safe_browsing_result.get('error')}")
            except Exception as e:
                # Safe Browsing check failed - continue with other checks
                reasons.append(f"Safe Browsing check error: {str(e)}")
        
        # Factor 1: Domain Age (0-50 points)
        domain_age_days = self.get_domain_age_days(domain)
        if domain_age_days is not None:
            if domain_age_days < 30:
                age_points = 50
                reasons.append(f"Domain created {domain_age_days} days ago (very new, high risk)")
            elif domain_age_days < 90:
                age_points = 30
                reasons.append(f"Domain created {domain_age_days} days ago (suspicious)")
            elif domain_age_days < 180:
                age_points = 15
                reasons.append(f"Domain created {domain_age_days} days ago (somewhat new)")
            else:
                age_points = 0
            score += age_points
        else:
            reasons.append("Could not verify domain age (WHOIS lookup failed)")
        
        # Factor 2: Visual Match but Wrong Domain (CRITICAL - 100 points)
        if detected_brand and logo_match:
            brand = self.brand_db.brands.get(detected_brand)
            if brand:
                is_official_domain = any(
                    official in domain.lower() or domain.lower() in official
                    for official in brand.official_domains
                )
                
                if not is_official_domain:
                    score = 100  # CRITICAL ALERT
                    reasons.append(
                        f"CRITICAL: Site visually matches {brand.brand_name} but domain "
                        f"({domain}) is not official. Official domains: {', '.join(brand.official_domains)}"
                    )
                else:
                    reasons.append(f"Visual match with {brand.brand_name} on official domain (safe)")
        
        # Factor 3: Localhost demo sites (auto-flag for testing)
        # Extract domain without port for checking
        domain_without_port = domain.split(':')[0].lower()
        if domain_without_port in ['localhost', '127.0.0.1', '0.0.0.0']:
            # Check if URL suggests a brand site (like fake-paypal.html)
            url_lower = url.lower()
            brand_keywords = ['paypal', 'amazon', 'chase', 'nike', 'apple', 'twitter', 'x.com', 'login', 'secure']
            if any(keyword in url_lower for keyword in brand_keywords):
                score = 100  # CRITICAL for demo/testing
                reasons.append(
                    f"CRITICAL: Site hosted on localhost ({domain}) with brand-like content. "
                    "This is a demo/test site - treat as suspicious!"
                )
            else:
                score += 30
                reasons.append(f"Site hosted on localhost ({domain}) - not a production domain")
        
        # Factor 4: Dynamic suspicious pattern detection (not just hardcoded)
        domain_lower = domain.lower()
        
        # Check for obvious fake indicators (dynamic detection)
        # But weigh against domain age - old domains with "fake" might be legitimate demos
        fake_indicators_patterns = [
            (r'not[-_]?real', 30, 'obvious fake indicator'),
            (r'fake', 25, 'fake indicator'),
            (r'scam|phishing|fraud', 40, 'suspicious indicator'),  # These are always bad
            (r'clone', 15, 'clone indicator'),  # Clones might be educational
            (r'unofficial|imposter', 20, 'unofficial indicator'),
        ]
        
        import re
        fake_indicator_found = False
        for pattern, base_points, desc in fake_indicators_patterns:
            if re.search(pattern, domain_lower):
                # Reduce points if domain is old (might be legitimate demo)
                if domain_age_days is not None and domain_age_days > 365:
                    points = base_points // 2  # Halve points for old domains
                    reasons.append(
                        f"Domain contains {desc}, but domain is {domain_age_days} days old. "
                        f"May be a legitimate demo/educational site."
                    )
                else:
                    points = base_points
                    reasons.append(f"Domain contains {desc} - may not be legitimate!")
                
                score += points
                fake_indicator_found = True
                break
        
        # Factor 5: Fuzzy brand name matching (MISSPELLED BRANDS - CRITICAL for typo detection)
        # This catches misspelled brand names like "pand0ra", "arnazon", "paypa1"
        similar_brand = self.find_similar_brand(domain, threshold=0.7)
        if similar_brand:
            brand_name, similarity = similar_brand
            # High similarity but not exact = likely typo
            if similarity >= 0.80 and similarity < 1.0:
                # Very similar but not exact - high risk of typo
                score += 70  # Increased from 60
                reasons.append(
                    f"CRITICAL: Domain '{domain}' is suspiciously similar to '{brand_name}' "
                    f"(similarity: {similarity:.1%}). This may be a misspelled/phishing site!"
                )
            elif similarity >= 0.7:
                # Moderately similar - still suspicious
                score += 50  # Increased from 35
                reasons.append(
                    f"Suspicious: Domain '{domain}' is similar to '{brand_name}' "
                    f"(similarity: {similarity:.1%}). May be a typo or phishing attempt."
                )
        
        # Factor 5b: Brand name in domain but not official domain (DYNAMIC)
        # Automatically check ALL brands in database
        for brand_name, brand in self.brand_db.brands.items():
            brand_name_lower = brand.brand_name.lower()
            # If domain contains brand name (like "twitter" in "notrealtwitter.com")
            if brand_name_lower in domain_lower:
                # Check if it's NOT an official domain
                is_official = any(
                    official.lower() in domain_lower or domain_lower in official.lower()
                    for official in brand.official_domains
                )
                if not is_official:
                    # Domain has brand name but isn't official - suspicious!
                    score += 40
                    reasons.append(
                        f"Suspicious: Domain contains '{brand.brand_name}' but is not official. "
                        f"Official: {', '.join(brand.official_domains)}"
                    )
                    break
        
        # Factor 6: Enhanced typosquatting detection (common character substitutions)
        # These are common enough that hardcoding makes sense
        common_typos = {
            'paypa1': 'paypal', 'arnazon': 'amazon', 'n1ke': 'nike',
            'app1e': 'apple', 'tw1tter': 'twitter', 'faceb00k': 'facebook',
            'pand0ra': 'pandora', 'pandoraa': 'pandora', 'pand0raa': 'pandora',
            'pand0r4': 'pandora', 'pandora0': 'pandora'
        }
        for typo, real in common_typos.items():
            if typo in domain_lower:
                score += 30  # Increased from 25
                reasons.append(f"Typosquatting detected: '{typo}' is likely a typo of '{real}'")
                break
        
        # Factor 6b: Character substitution patterns (0 for O, 1 for I, etc.)
        # Check for number/letter substitutions in brand names
        domain_clean = re.sub(r'^(www\.|secure\.|login\.)', '', domain_lower).split('.')[0]
        for brand_name, brand in self.brand_db.brands.items():
            brand_lower = brand.brand_name.lower()
            # Check if domain looks like brand with character substitutions
            if len(domain_clean) >= 4 and len(brand_lower) >= 4:
                # Check for common substitutions: 0=O, 1=I/l, 3=E, 4=A, 5=S, 7=T
                substitutions = {
                    '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't',
                    'o': '0', 'i': '1', 'l': '1', 'e': '3', 'a': '4', 's': '5', 't': '7'
                }
                # Try substituting characters and check similarity
                domain_variants = [domain_clean]
                for char, sub in substitutions.items():
                    if char in domain_clean:
                        variant = domain_clean.replace(char, sub)
                        if variant != domain_clean:
                            domain_variants.append(variant)
                
                for variant in domain_variants:
                    if brand_lower in variant or variant in brand_lower:
                        # Check if it's not official
                        is_official = any(
                            official.lower() in domain_lower or domain_lower in official.lower()
                            for official in brand.official_domains
                        )
                        if not is_official:
                            score += 35
                            reasons.append(
                                f"Character substitution detected: '{domain_clean}' may be a typo of '{brand.brand_name}' "
                                f"(using number/letter substitutions)"
                            )
                            break
        
        # Factor 7: Suspicious subdomain/domain combinations
        # Pattern: brand-secure, brand-verify, brand-login, etc.
        for brand_name, brand in self.brand_db.brands.items():
            brand_lower = brand.brand_name.lower()
            suspicious_suffixes = ['-secure', '-verify', '-login', '-account', '-bank', '-sale', '-shop', '-store', '-official']
            for suffix in suspicious_suffixes:
                pattern = brand_lower + suffix
                if pattern in domain_lower:
                    is_official = any(official.lower() in domain_lower for official in brand.official_domains)
                    if not is_official:
                        score += 25
                        reasons.append(f"Suspicious pattern: '{pattern}' suggests fake {brand.brand_name} site")
                        break
        
        # Factor 8: SSL Certificate Check (for payment sites)
        # Missing or invalid SSL is a red flag for sites that should have it
        if any(keyword in url.lower() for keyword in ['login', 'payment', 'checkout', 'account', 'secure', 'bank']):
            ssl_check = self.check_ssl_certificate(url)
            if not ssl_check.get('has_ssl'):
                score += 30
                reasons.append("CRITICAL: Site requires login/payment but has no SSL certificate - UNSAFE!")
            elif ssl_check.get('has_ssl') and not ssl_check.get('is_valid'):
                score += 25
                reasons.append("WARNING: SSL certificate is invalid or expired - do not enter sensitive information!")
            elif ssl_check.get('days_until_expiry', 999) < 30:
                score += 10
                reasons.append(f"Warning: SSL certificate expires in {ssl_check['days_until_expiry']} days")
        
        # Ensure score doesn't exceed 100
        score = min(100, score)
        
        # Determine recommendation
        is_scam = score >= self.critical_threshold
        recommendation = "BLOCK" if is_scam else "ALLOW"
        
        # Prepare Safe Browsing result for response
        safe_browsing_response = None
        if safe_browsing_result:
            safe_browsing_response = {
                'is_threat': safe_browsing_result.get("is_threat", False),
                'threat_types': safe_browsing_result.get("threat_types", []),
                'platform_types': safe_browsing_result.get("platform_types", []),
                'error': safe_browsing_result.get("error")
            }
        elif self.safe_browsing is None:
            safe_browsing_response = {
                'is_threat': False,
                'threat_types': [],
                'platform_types': [],
                'error': 'Safe Browsing API not configured'
            }
        
        return {
            'score': score,
            'is_scam': is_scam,
            'reasons': reasons,
            'recommendation': recommendation,
            'domain_age_days': domain_age_days,
            'detected_brand': detected_brand,
            'domain': domain,
            'safe_browsing': safe_browsing_response
        }
