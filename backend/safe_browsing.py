"""
Google Safe Browsing API Integration
Checks URLs against Google's Safe Browsing database in real-time
"""
import requests
import json
from typing import Optional, Dict, List
from urllib.parse import urlparse

try:
    from .config import GOOGLE_SAFE_BROWSING_API_KEY
except ImportError:
    try:
        from config import GOOGLE_SAFE_BROWSING_API_KEY
    except ImportError:
        GOOGLE_SAFE_BROWSING_API_KEY = None

class SafeBrowsingChecker:
    """Checks URLs against Google Safe Browsing API"""
    
    # Google Safe Browsing API v4 endpoint
    API_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    
    # Threat types to check for
    THREAT_TYPES = [
        "MALWARE",
        "SOCIAL_ENGINEERING",  # Phishing
        "UNWANTED_SOFTWARE",
        "POTENTIALLY_HARMFUL_APPLICATION"
    ]
    
    # Platform types
    PLATFORM_TYPES = ["ANY_PLATFORM"]
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Safe Browsing checker
        
        Args:
            api_key: Google Safe Browsing API key. If None, uses from config.
        """
        self.api_key = api_key or GOOGLE_SAFE_BROWSING_API_KEY
        self.enabled = self.api_key is not None and len(self.api_key.strip()) > 0
        
        if not self.enabled:
            print("Warning: Google Safe Browsing API key not configured. Safe Browsing checks will be skipped.")
    
    def check_url(self, url: str) -> Dict:
        """
        Check a single URL against Google Safe Browsing
        
        Args:
            url: URL to check
            
        Returns:
            Dict with:
                - is_threat: bool - Whether URL is flagged as threat
                - threat_types: List[str] - Types of threats detected
                - platform_types: List[str] - Platform types affected
                - cache_duration: str - How long to cache this result
                - error: Optional[str] - Error message if check failed
        """
        if not self.enabled:
            return {
                "is_threat": False,
                "threat_types": [],
                "platform_types": [],
                "cache_duration": None,
                "error": "Safe Browsing API not configured"
            }
        
        # Normalize URL
        normalized_url = self._normalize_url(url)
        
        try:
            # Prepare request payload
            payload = {
                "client": {
                    "clientId": "verisight",
                    "clientVersion": "1.0.0"
                },
                "threatInfo": {
                    "threatTypes": self.THREAT_TYPES,
                    "platformTypes": self.PLATFORM_TYPES,
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [
                        {"url": normalized_url}
                    ]
                }
            }
            
            # Make API request
            params = {"key": self.api_key}
            response = requests.post(
                self.API_URL,
                params=params,
                json=payload,
                timeout=5  # 5 second timeout
            )
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                
                # Check if any matches found
                if "matches" in data and len(data["matches"]) > 0:
                    matches = data["matches"]
                    threat_types = [match.get("threatType", "") for match in matches]
                    platform_types = [match.get("platformType", "") for match in matches]
                    
                    return {
                        "is_threat": True,
                        "threat_types": threat_types,
                        "platform_types": platform_types,
                        "cache_duration": matches[0].get("cacheDuration", None),
                        "error": None
                    }
                else:
                    # No threats found
                    return {
                        "is_threat": False,
                        "threat_types": [],
                        "platform_types": [],
                        "cache_duration": None,
                        "error": None
                    }
            else:
                # API error
                error_msg = f"Safe Browsing API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data["error"].get("message", error_msg)
                except:
                    pass
                
                return {
                    "is_threat": False,
                    "threat_types": [],
                    "platform_types": [],
                    "cache_duration": None,
                    "error": error_msg
                }
                
        except requests.exceptions.Timeout:
            return {
                "is_threat": False,
                "threat_types": [],
                "platform_types": [],
                "cache_duration": None,
                "error": "Safe Browsing API request timed out"
            }
        except requests.exceptions.RequestException as e:
            return {
                "is_threat": False,
                "threat_types": [],
                "platform_types": [],
                "cache_duration": None,
                "error": f"Safe Browsing API request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "is_threat": False,
                "threat_types": [],
                "platform_types": [],
                "cache_duration": None,
                "error": f"Unexpected error checking Safe Browsing: {str(e)}"
            }
    
    def check_urls(self, urls: List[str]) -> Dict[str, Dict]:
        """
        Check multiple URLs (batch request)
        
        Args:
            urls: List of URLs to check
            
        Returns:
            Dict mapping URL to check result
        """
        if not self.enabled:
            return {url: {
                "is_threat": False,
                "threat_types": [],
                "platform_types": [],
                "cache_duration": None,
                "error": "Safe Browsing API not configured"
            } for url in urls}
        
        # Normalize URLs
        normalized_urls = [self._normalize_url(url) for url in urls]
        
        try:
            # Prepare batch request payload
            payload = {
                "client": {
                    "clientId": "verisight",
                    "clientVersion": "1.0.0"
                },
                "threatInfo": {
                    "threatTypes": self.THREAT_TYPES,
                    "platformTypes": self.PLATFORM_TYPES,
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [
                        {"url": url} for url in normalized_urls
                    ]
                }
            }
            
            # Make API request
            params = {"key": self.api_key}
            response = requests.post(
                self.API_URL,
                params=params,
                json=payload,
                timeout=10  # Longer timeout for batch requests
            )
            
            if response.status_code == 200:
                data = response.json()
                results = {}
                
                # Initialize all URLs as safe
                for url in urls:
                    results[url] = {
                        "is_threat": False,
                        "threat_types": [],
                        "platform_types": [],
                        "cache_duration": None,
                        "error": None
                    }
                
                # Process matches
                if "matches" in data:
                    for match in data["matches"]:
                        threat_url = match.get("threat", {}).get("url", "")
                        # Find original URL (before normalization)
                        original_url = None
                        for url in urls:
                            if self._normalize_url(url) == threat_url:
                                original_url = url
                                break
                        
                        if original_url:
                            results[original_url] = {
                                "is_threat": True,
                                "threat_types": [match.get("threatType", "")],
                                "platform_types": [match.get("platformType", "")],
                                "cache_duration": match.get("cacheDuration", None),
                                "error": None
                            }
                
                return results
            else:
                # API error - return error for all URLs
                error_msg = f"Safe Browsing API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data["error"].get("message", error_msg)
                except:
                    pass
                
                return {url: {
                    "is_threat": False,
                    "threat_types": [],
                    "platform_types": [],
                    "cache_duration": None,
                    "error": error_msg
                } for url in urls}
                
        except Exception as e:
            # Return error for all URLs
            return {url: {
                "is_threat": False,
                "threat_types": [],
                "platform_types": [],
                "cache_duration": None,
                "error": f"Error checking Safe Browsing: {str(e)}"
            } for url in urls}
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for Safe Browsing API
        Ensures URL has proper scheme
        """
        if not url.startswith(('http://', 'https://')):
            # Default to https if no scheme
            url = f'https://{url}'
        
        return url
