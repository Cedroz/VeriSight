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
- **Automatic Input Blocking**: Blocks password, credit card, and other sensitive input fields on flagged sites
- **Red Screen Warning**: Shows a clear, alarming warning overlay when danger is detected

## Architecture

### Backend (The "Brain")
- **FastAPI Server**: Python-based REST API for scam detection
- **Brand Database**: JSON storage of brand fingerprints (logos, colors, official domains)
- **Scam Detection Engine**: Multi-factor scoring algorithm (0-100)
- **Google Safe Browsing API**: Real-time threat detection integration
- **WHOIS Integration**: Domain age verification

### Browser Extension (The "Body")
- **Chrome Extension (Manifest V3)**: Content scripts, background service worker
- **Screenshot Capture**: Captures page viewport for visual analysis
- **Input Blocking**: DOM manipulation to disable form fields
- **API Integration**: Communicates with backend for analysis

### UI & Testing
- **Warning Overlay**: "Red Screen of Death" with detailed reasons
- **Demo Site**: Fake PayPal page for testing
- **Safe Indicator**: Green indicator for verified safe sites

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
  - Calculates scam score
Returns result to extension
If score ≥ 80:
  - Show red warning overlay
  - Block all input fields
```

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
