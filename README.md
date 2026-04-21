# VeriSight

Protect yourself from fake websites by detecting visual clones and suspicious domains

VeriSight is a fullstack application consisting of a Python FastAPI backend and a Chrome extension frontend that analyzes websites in real-time to detect scams, phishing attempts, and fake sites that clone legitimate brands. When it detects a suspicious site, it automatically blocks input fields to prevent credential theft.

## Key Features

- **Google Safe Browsing Integration**: Real-time checks against Google's threat database for malware, phishing, and unwanted software
- **Fuzzy Brand Matching**: Advanced Levenshtein distance algorithm detects misspelled brand names (e.g., `pand0ra.com`, `arnazon.com`)
- **Visual Fingerprint Matching**: Uses perceptual hashing to detect when a site visually matches a known brand (Amazon, PayPal, Nike, Pandora, etc.)
- **Domain Age Detection**: Flags newly registered domains (< 30 days) that are high-risk
- **Enhanced Typosquatting Detection**: Identifies character substitutions and suspicious domain patterns
- **SSL Certificate Validation**: Checks for valid SSL certificates on payment/login sites
- **Optional URL phishing ML**: Lightweight scikit-learn model (character n-gram TF-IDF + logistic regression) scores URL strings for phishing-like patterns when a trained bundle is present
- **Automatic Input Blocking**: Blocks password, credit card, and other sensitive input fields on flagged sites
- **Red Screen Warning**: Shows a clear, alarming warning overlay when danger is detected

## Architecture

### Backend
- **FastAPI Server**: Python-based REST API for scam detection
- **Brand Database**: JSON storage of brand fingerprints (logos, colors, official domains)
- **Scam Detection Engine**: Multi-factor scoring algorithm (0-100)
- **Google Safe Browsing API**: Real-time threat detection integration
- **WHOIS Integration**: Domain age verification
- **URL ML (`url_ml.py`)**: Loads `backend/models/url_phishing_bundle.joblib` at startup if available; otherwise detection runs without it

### Browser Extension
- **Chrome Extension (Manifest V3)**: Content scripts, background service worker
- **Screenshot Capture**: Captures page viewport for visual analysis
- **Input Blocking**: DOM manipulation to disable form fields
- **API Integration**: Communicates with backend for analysis

### UI & Testing
- **Warning Overlay**: "Red Screen of Death" with detailed reasons
- **Demo Site**: Fake PayPal page for testing
- **Safe Indicator**: Green indicator for verified safe sites

## Design Decisions

### Why FastAPI?
- **Fast, modern Python framework** perfect for real-time API responses
- **Built-in async support** for handling concurrent requests efficiently
- **Automatic API documentation** (Swagger/OpenAPI) for easy testing and integration
- **Type hints and validation** ensure data integrity
- **Lightweight** compared to Django/Flask for API-only services

### Why Chrome Extension?
- **Runs client-side** for immediate protection without server round-trips for every page
- **Can intercept page loads** before user interaction occurs
- **Direct DOM manipulation** allows for seamless input blocking
- **Wide adoption** - Chrome has the largest browser market share
- **Manifest V3** ensures future compatibility and security

### Why Multi-Factor Scoring?
- **Single detection method limitations**: URL-only checks miss visual clones; visual-only checks miss typosquatting
- **Reduced false positives**: Combining multiple signals provides higher confidence
- **Weighted scoring** allows fine-tuning sensitivity for different threat levels
- **Transparency**: Users can see exactly why a site was flagged through detailed reasons
- **Adaptability**: Easy to adjust weights or add new detection methods

### Architecture Tradeoffs

#### JSON File Storage vs Database
- **Chose JSON**: Simple, no setup required, perfect for development and small-scale deployments
- **Tradeoff**: Not suitable for high-volume production; would need migration to SQLite/PostgreSQL for scale
- **Future**: Database migration path is straightforward given the modular design

#### Screenshot-Based Detection
- **Chose screenshots**: More accurate than URL-only analysis, catches visual clones
- **Tradeoff**: Adds latency (~200-500ms) and requires image processing
- **Mitigation**: Screenshots are optional; system works with URL-only analysis
- **Future**: Could implement caching or background processing for better performance

#### Client-Side Blocking
- **Chose extension-based blocking**: Immediate protection, works offline after initial check
- **Tradeoff**: Requires user installation and trust
- **Alternative considered**: Server-side proxy would work but adds complexity and latency
- **Future**: Could add server-side API for other clients (mobile apps, etc.)

#### Real-Time Analysis vs Batch Processing
- **Chose real-time**: Immediate protection when user visits suspicious site
- **Tradeoff**: Higher server load, requires fast API responses
- **Mitigation**: Async processing, efficient algorithms, optional caching
- **Future**: Could add background queue for non-critical checks

### Security Considerations
- **No data storage**: Extension doesn't store user browsing history or credentials
- **Local API**: Backend runs locally by default, keeping data private
- **Override mechanism**: Users can bypass warnings if needed (with clear warnings)
- **API key security**: Google Safe Browsing API key stored in environment variables
- **Input blocking**: Prevents credential theft even if user ignores warnings

## Installation

### Prerequisites
- Python 3.8+
- Chrome or Chromium-based browser
- Internet connection (for WHOIS lookups and Safe Browsing API)
- Google Safe Browsing API Key (optional, but recommended)

### Backend Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment (Optional):**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_SAFE_BROWSING_API_KEY=your_api_key_here
   PORT=8001
   ```

3. **Start the API Server:**
   ```bash
   cd backend
   python main.py
   ```
   Server will run on `http://localhost:8001` (default)

### Frontend Setup (Chrome Extension)

1. **Load Extension in Chrome:**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)
   - Click "Load unpacked"
   - Select the `frontend` folder

2. **Update API URL (if needed):**
   - Edit `frontend/background.js` or `frontend/config.js`
   - Update the API URL to match your backend server

## Usage

### Normal Flow

1. **Visit any website** - VeriSight automatically analyzes it
2. **Safe Site**: Shows green "Site appears safe" indicator
3. **Suspicious Site**: 
   - Red warning overlay appears
   - Input fields are blocked (grayed out with padlock icon)
   - Detailed reasons displayed

### Testing with Demo Site

1. **Start Demo Server:**
   ```bash
   cd demo
   python -m http.server 8080
   ```

2. **Visit Fake PayPal:**
   - Navigate to `http://localhost:8080/fake-paypal.html`
   - VeriSight should immediately flag it as suspicious
   - Try to type in the password field - it should be blocked!

## How It Works

### Scam Score Calculation

The backend calculates a **Scam Score (0-100)** based on:

1. **Google Safe Browsing API** (CRITICAL - 100 points if threat detected)
2. **Fuzzy Brand Matching** (0-70 points): Detects misspelled brand names
3. **Domain Age** (0-50 points):
   - < 30 days = 50 points
   - < 90 days = 30 points
   - < 180 days = 15 points
4. **Visual Match on Wrong Domain** (CRITICAL - 100 points):
   - Site looks like Amazon/PayPal/etc.
   - But domain is NOT official
   - **This triggers immediate blocking**
5. **Suspicious Patterns** (20-40 points):
   - Typosquatting: `paypa1.com`, `arnazon.com`, `pand0ra.com`
   - Suspicious substrings: `paypal-secure`, `amazon-verify`
6. **SSL Certificate Validation** (0-30 points):
   - Missing SSL on payment sites = 30 points
   - Invalid/expired SSL = 25 points
7. **URL phishing ML (optional, 0-25 points)**:
   - Only active when `backend/models/url_phishing_bundle.joblib` is installed and scikit-learn loads successfully
   - Adds up to 25 points when the model’s phishing probability is high (see [URL phishing ML model](#url-phishing-ml-model))

### Detection Flow

```
User visits site
Extension captures screenshot
Sends to backend API
Backend:
  - Checks Google Safe Browsing API
  - Extracts logo hash from screenshot
  - Compares against brand database
  - Checks domain age (WHOIS)
  - Detects typos and misspellings
  - Validates SSL certificate
  - Optionally runs URL phishing classifier on the normalized URL string
  - Calculates scam score
Returns result to extension
If score ≥ 80:
  - Show red warning overlay
  - Block all input fields
```

## URL phishing ML model

This component is **optional**. The backend can load a **small supervised classifier** trained on URL-like strings. If the model file is missing or sklearn cannot be imported, the API still works and other signals drive the score.

### What it does

- **Technique**: `TfidfVectorizer` with character n-grams (`char_wb`, n-gram range 3–5) plus **logistic regression** in a single sklearn `Pipeline`.
- **Input**: The URL is normalized (lowercase host + path, scheme stripped) before vectorization, matching `normalize_url_for_ml` in `backend/url_ml.py`.
- **Output**: `phishing_probability` between 0 and 1 (estimated probability of the “phishing-like” class), bundled with `model_version` from the joblib file.
- **Effect on scam score**: High probabilities add **up to 25** points (scaled from a probability threshold; see `ScamDetector` in `backend/scam_detector.py`). Reasons mention the model version when points are added.

### Artifact location

- Trained bundle (default): `backend/models/url_phishing_bundle.joblib`
- Loader: `backend/url_ml.py` (`UrlPhishingClassifier`)

### Training the bundle

From the repository root (requires `scikit-learn` from `requirements.txt`):

```bash
python scripts/train_url_phishing_model.py
```

This script fits the pipeline on synthetic benign vs. phishing-style URL examples and writes `url_phishing_bundle.joblib`. For production-quality behavior you would replace or extend the training data with a real dataset; the bundled script is a minimal baseline.

### API

`POST /api/check-scam` responses include an optional `ml_url_risk` object: `phishing_probability`, `model_version`, `enabled`, and `error` (if prediction failed while the model was loaded).

## Brand Database

### Default Brands

Pre-loaded brands:
- **Amazon** (amazon.com)
- **Nike** (nike.com)
- **Apple** (apple.com)
- **Chase Bank** (chase.com)
- **PayPal** (paypal.com)
- **Pandora** (pandora.com, pandora.net)
- **Twitter/X** (twitter.com, x.com)

### Adding Brands

#### Method 1: API Lookup (Auto-Scrape)

Automatically scrape a website to extract brand information:

```bash
curl -X POST http://localhost:8001/api/brands/lookup \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com"}'
```

#### Method 2: CLI Tool

```bash
python scripts/add_brand.py https://github.com
```

#### Method 3: Manual API

```bash
curl -X POST http://localhost:8001/api/brands \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "MyBrand",
    "official_domains": ["mybrand.com"]
  }'
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Health check
- `POST /api/check-scam` - Main scam detection endpoint
  ```json
  {
    "url": "https://example.com",
    "logo_hash": "optional_hash_string",
    "screenshot_base64": "optional_base64_image"
  }
  ```
  Response may include `ml_url_risk` when the optional URL model is loaded (see [URL phishing ML model](#url-phishing-ml-model)).
- `GET /api/brands` - List all brands in database
- `POST /api/brands` - Add a new brand
- `POST /api/brands/lookup` - Auto-scrape brand from URL
- `GET /api/brands/search?q=query` - Search brands

## Testing

### Test API Directly

```bash
# Test with fake site
curl -X POST http://localhost:8001/api/check-scam \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:8080/fake-paypal.html"}'

# Test with real site
curl -X POST http://localhost:8001/api/check-scam \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.paypal.com"}'
```

### Test Phishing Detection

```bash
python test_phishing_detection.py
```

This tests various misspelled brand names to verify detection works.

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8001

# Google Safe Browsing API (optional but recommended)
GOOGLE_SAFE_BROWSING_API_KEY=your_api_key_here

# Environment
ENVIRONMENT=development
```

### Getting Google Safe Browsing API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "Safe Browsing API" in the API Library
4. Create an API Key in Credentials
5. Add it to your `.env` file

## Limitations & Notes

- **WHOIS Rate Limits**: Some domains may fail WHOIS lookup due to rate limiting
- **Screenshot Quality**: Logo detection depends on screenshot quality and page layout
- **False Positives**: Very new legitimate sites may be flagged; users can override
- **API Key Required**: Google Safe Browsing API key is optional but recommended for best protection
