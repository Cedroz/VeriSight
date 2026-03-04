"""
VeriSight Backend API Server
FastAPI server that provides scam detection endpoints
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import base64
import io
import logging
import sys
from PIL import Image
import imagehash

try:
    # Try relative imports (when used as package)
    from .brand_fingerprints import BrandDatabase
    from .scam_detector import ScamDetector
    from .brand_scraper import BrandScraper
    from .config import (
        HOST, PORT, ENVIRONMENT, CORS_ORIGINS, DB_PATH,
        LOG_LEVEL, LOG_FILE, get_cors_origins
    )
except ImportError:
    # Fallback to absolute imports (when running directly)
    from brand_fingerprints import BrandDatabase
    from scam_detector import ScamDetector
    from brand_scraper import BrandScraper
    # Try to import config, fallback to defaults if not available
    try:
        from config import (
            HOST, PORT, ENVIRONMENT, CORS_ORIGINS, DB_PATH,
            LOG_LEVEL, LOG_FILE, get_cors_origins
        )
    except ImportError:
        # Default config if config.py not available
        HOST = "0.0.0.0"
        PORT = 8001  # Updated default port
        ENVIRONMENT = "development"
        CORS_ORIGINS = ["*"]
        DB_PATH = "brands.db.json"
        LOG_LEVEL = "INFO"
        LOG_FILE = None
        def get_cors_origins():
            return ["*"]

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE) if LOG_FILE else logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VeriSight API",
    version="1.0.0",
    description="Backend API for VeriSight scam detection browser extension"
)

# Enable CORS for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
try:
    brand_db = BrandDatabase(db_path=DB_PATH)
    
    # Initialize Safe Browsing checker
    try:
        from .safe_browsing import SafeBrowsingChecker
        safe_browsing_checker = SafeBrowsingChecker()
    except ImportError:
        try:
            from safe_browsing import SafeBrowsingChecker
            safe_browsing_checker = SafeBrowsingChecker()
        except ImportError:
            logger.warning("SafeBrowsingChecker not available. Safe Browsing checks will be disabled.")
            safe_browsing_checker = None
    
    scam_detector = ScamDetector(brand_db, safe_browsing_checker=safe_browsing_checker)
    brand_scraper = BrandScraper()
    logger.info(f"VeriSight API initialized (Environment: {ENVIRONMENT})")
    if safe_browsing_checker and safe_browsing_checker.enabled:
        logger.info("Google Safe Browsing API enabled")
    else:
        logger.info("Google Safe Browsing API disabled (no API key configured)")
except Exception as e:
    logger.error(f"Failed to initialize VeriSight components: {e}")
    raise

class ScamCheckRequest(BaseModel):
    url: str
    logo_hash: Optional[str] = None
    screenshot_base64: Optional[str] = None

class SafeBrowsingResult(BaseModel):
    is_threat: bool
    threat_types: List[str]
    platform_types: List[str]
    error: Optional[str] = None

class ScamCheckResponse(BaseModel):
    score: int
    is_scam: bool
    reasons: List[str]
    recommendation: str
    domain_age_days: Optional[int]
    detected_brand: Optional[str]
    domain: str
    safe_browsing: Optional[SafeBrowsingResult] = None

@app.get("/")
async def root():
    return {"message": "VeriSight API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/check-scam", response_model=ScamCheckResponse)
async def check_scam(request: ScamCheckRequest):
    """
    Main endpoint: Check if a website is a scam
    Accepts URL, optional logo hash, and optional screenshot
    """
    try:
        detected_brand = None
        logo_match = False
        
        # If logo hash provided, compare against brand database
        if request.logo_hash:
            detected_brand = brand_db.compare_logo_hash(request.logo_hash, threshold=5)
            logo_match = detected_brand is not None
        
        # If screenshot provided but no hash, extract hash from image
        if request.screenshot_base64 and not request.logo_hash:
            try:
                image_data = base64.b64decode(request.screenshot_base64)
                image = Image.open(io.BytesIO(image_data))
                logo_hash = str(imagehash.phash(image))
                detected_brand = brand_db.compare_logo_hash(logo_hash, threshold=5)
                logo_match = detected_brand is not None
                request.logo_hash = logo_hash
            except Exception as e:
                print(f"Failed to process screenshot: {e}")
        
        # Calculate scam score (includes Safe Browsing check)
        result = scam_detector.calculate_scam_score(
            url=request.url,
            detected_brand=detected_brand,
            logo_match=logo_match
        )
        
        # Convert safe_browsing dict to SafeBrowsingResult if present
        if result.get('safe_browsing'):
            result['safe_browsing'] = SafeBrowsingResult(**result['safe_browsing'])
        
        return ScamCheckResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking scam: {str(e)}")

@app.post("/api/upload-screenshot")
async def upload_screenshot(file: UploadFile = File(...), url: str = Form(...)):
    """
    Alternative endpoint: Upload screenshot file directly
    """
    try:
        # Read image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Generate hash
        logo_hash = str(imagehash.phash(image))
        detected_brand = brand_db.compare_logo_hash(logo_hash, threshold=5)
        logo_match = detected_brand is not None
        
        # Calculate scam score (includes Safe Browsing check)
        result = scam_detector.calculate_scam_score(
            url=url,
            detected_brand=detected_brand,
            logo_match=logo_match
        )
        
        # Convert safe_browsing dict to SafeBrowsingResult if present
        if result.get('safe_browsing'):
            result['safe_browsing'] = SafeBrowsingResult(**result['safe_browsing'])
        
        return ScamCheckResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing screenshot: {str(e)}")

@app.get("/api/brands")
async def list_brands():
    """List all brands in database"""
    return {
        "brands": {
            name: brand.to_dict()
            for name, brand in brand_db.brands.items()
        }
    }

class AddBrandRequest(BaseModel):
    brand_name: str
    official_domains: List[str]
    logo_hash: Optional[str] = None
    primary_color: Optional[str] = None
    font_family: Optional[str] = None

@app.post("/api/brands")
async def add_brand(request: AddBrandRequest):
    """Add a new brand to the database"""
    try:
        success = brand_db.add_brand(
            brand_name=request.brand_name,
            official_domains=request.official_domains,
            logo_hash=request.logo_hash,
            primary_color=request.primary_color,
            font_family=request.font_family,
            overwrite=False
        )
        if not success:
            raise HTTPException(status_code=400, detail="Brand already exists")
        
        return {"success": True, "message": f"Brand '{request.brand_name}' added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/brands/{brand_name}")
async def update_brand(brand_name: str, updates: dict):
    """Update an existing brand"""
    try:
        success = brand_db.update_brand(brand_name, **updates)
        if not success:
            raise HTTPException(status_code=404, detail="Brand not found")
        return {"success": True, "message": f"Brand '{brand_name}' updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/brands/{brand_name}")
async def delete_brand(brand_name: str):
    """Delete a brand from database"""
    try:
        success = brand_db.delete_brand(brand_name)
        if not success:
            raise HTTPException(status_code=404, detail="Brand not found")
        return {"success": True, "message": f"Brand '{brand_name}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/brands/search")
async def search_brands(q: str):
    """Search brands by name or domain"""
    results = brand_db.search_brands(q)
    return {"results": results, "count": len(results)}

class LookupBrandRequest(BaseModel):
    url: str

@app.post("/api/brands/lookup")
async def lookup_brand(request: LookupBrandRequest):
    """
    Lookup and automatically add a brand from a URL
    Scrapes the website to extract brand information
    """
    try:
        # Scrape brand information
        brand_data = brand_scraper.scrape_brand(request.url)
        
        if not brand_data:
            raise HTTPException(status_code=400, detail="Failed to scrape brand information")
        
        # Add to database
        success = brand_db.add_brand(
            brand_name=brand_data['brand_name'],
            official_domains=brand_data['official_domains'],
            logo_hash=brand_data.get('logo_hash'),
            primary_color=brand_data.get('primary_color'),
            font_family=brand_data.get('font_family'),
            overwrite=True  # Allow updating existing brands
        )
        
        return {
            "success": True,
            "message": f"Brand '{brand_data['brand_name']}' added/updated",
            "brand": brand_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error looking up brand: {str(e)}")

@app.post("/api/brands/lookup-and-check")
async def lookup_and_check(request: LookupBrandRequest):
    """
    Convenience endpoint: Lookup a brand from URL and immediately check if it's a scam
    Useful for one-off checks of unknown sites
    """
    try:
        # First, lookup the brand
        lookup_result = await lookup_brand(request)
        
        # Then check if the site is a scam
        check_request = ScamCheckRequest(url=request.url)
        check_result = await check_scam(check_request)
        
        return {
            "lookup": lookup_result,
            "scam_check": check_result.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting VeriSight API server on {HOST}:{PORT}")
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level=LOG_LEVEL.lower()
    )
