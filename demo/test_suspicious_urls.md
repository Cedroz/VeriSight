# Testing VeriSight with Suspicious URL Patterns

## How to Test Detection Without Real Scam Sites

Since visiting actual scam sites is unsafe, here's how to test VeriSight's detection logic:

## Method 1: Test Suspicious URL Patterns

### Create Test HTML Files with Suspicious URLs

The backend checks URL patterns. You can test this by:

1. **Create a file** with suspicious name:
   - Save as: `demo/paypal-secure-verify.html`
   - Visit: `http://localhost:8080/paypal-secure-verify.html`
   - Should trigger: "Suspicious pattern detected: paypal-secure" (+20 points)

2. **Test with our demo Amazon file:**
   - Save as: `demo/arnazon-test.html` (typo)
   - Visit: `http://localhost:8080/arnazon-test.html`
   - Should trigger: "Suspicious pattern detected: arnazon" (+20 points)

## Method 2: Test with Modified Host Headers (Advanced)

If you want to simulate different domains:

```bash
# Use a local hosts file entry to simulate typosquatting
# Edit C:\Windows\System32\drivers\etc\hosts (as admin)
# Add: 127.0.0.1 paypa1.local
# Then visit: http://paypa1.local:8080/fake-paypal.html
```

## Method 3: API Testing with Suspicious URLs

Test the backend directly with suspicious URL patterns:

```python
import requests

# Test suspicious patterns
test_urls = [
    "http://paypal-secure-login.net/fake-page",  # Pattern: "paypal-secure"
    "http://arnazon.com/login",  # Pattern: "arnazon"
    "http://amazon-verify-secure.net",  # Pattern: "amazon-verify"
]

for url in test_urls:
    r = requests.post('http://localhost:8000/api/check-scam', json={'url': url})
    result = r.json()
    print(f"{url}: Score {result['score']}, Is Scam: {result['is_scam']}")
```

## Method 4: Simulate Domain Age (New Domains)

The backend checks domain age. To test this:

1. **Find a newly registered domain** (< 30 days old):
   - Use WHOIS lookup: `whois example.com`
   - Find domains registered recently
   - Visit with VeriSight
   - Should get points for new domain age

2. **Use a test domain you control:**
   - Register a new test domain
   - Create a simple page
   - Visit with VeriSight
   - Should detect new domain age

## Method 5: Brand Database Testing

Test brand matching:

```bash
# Add a brand
python scripts/add_brand.py https://github.com

# Test real site (should be safe)
# Visit: https://github.com → Should be safe

# Test fake pattern
# Visit URL with suspicious pattern: github-secure-login.net
# Should trigger pattern detection
```

## Test Scenarios Checklist

### Scenario 1: Suspicious URL Pattern
- [ ] Create `demo/paypal-secure-test.html`
- [ ] Visit: `http://localhost:8080/paypal-secure-test.html`
- [ ] Check: Should detect pattern "paypal-secure" (+20 points)
- [ ] Console: Should show "Suspicious domain pattern detected"

### Scenario 2: Typo Pattern
- [ ] Create `demo/arnazon-test.html`  
- [ ] Visit: `http://localhost:8080/arnazon-test.html`
- [ ] Check: Should detect pattern "arnazon" (+20 points)

### Scenario 3: Combined (Pattern + Localhost)
- [ ] Visit: `http://localhost:8080/fake-paypal.html`
- [ ] Should detect:
  - Localhost domain
  - "paypal" keyword in URL
  - Total: Score 100 (CRITICAL)

### Scenario 4: New Domain (if available)
- [ ] Find domain registered < 30 days
- [ ] Visit with VeriSight
- [ ] Should add +50 points for new domain age

### Scenario 5: Brand Match Test
- [ ] Add brand: `python scripts/add_brand.py https://github.com`
- [ ] Visit real GitHub: Should be safe
- [ ] Test with pattern: Should detect suspicious pattern

## What to Look For

### Console Output for Suspicious Sites:
```
[VeriSight] Response details: {
  score: 20-100,
  is_scam: true/false,
  reasons: [
    "Suspicious domain pattern detected: 'paypal-secure'",
    "Domain created X days ago (very new)"
  ]
}
```

### Popup Shows:
- Red "DANGER DETECTED" if score ≥ 80
- Orange "Unblock Inputs" button appears
- Score displayed

### Page Behavior:
- Red overlay if score ≥ 80
- Inputs blocked if score ≥ 80

## Key Point

**The detection logic works the same way for:**
- Localhost demo sites (for testing)
- Real suspicious domains (in production)

The only difference is:
- Localhost = special test case (auto-flags)
- Real domains = uses WHOIS, URL patterns, visual matching

Both use the **same scoring system** - so if it works on localhost, it will work on real suspicious sites!
