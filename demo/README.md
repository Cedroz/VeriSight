# VeriSight Demo Sites

Multiple fake sites to test VeriSight's detection capabilities.

## Available Demo Sites

### 1. Fake PayPal (`fake-paypal.html`)
**URL:** `http://localhost:8080/fake-paypal.html`

**What it tests:**
- Localhost detection
- Brand keyword detection ("paypal" in URL)
- Input blocking

**Expected Result:** Score 100, BLOCKED

### 2. Fake Amazon Typo (`fake-amazon-typo.html`)
**URL:** `http://localhost:8080/fake-amazon-typo.html`

**What it tests:**
- Localhost detection
- Brand keyword detection ("amazon" in URL)
- Amazon-style login page

**Expected Result:** Score 100, BLOCKED

### 3. Fake Amazon Verify (`fake-amazon-verify.html`)
**URL:** `http://localhost:8080/fake-amazon-verify.html`

**What it tests:**
- Localhost detection
- Brand keyword detection
- Credit card input field (should be blocked)

**Expected Result:** Score 100, BLOCKED

### 4. Fake Chase Bank (`fake-chase-bank.html`)
**URL:** `http://localhost:8080/fake-chase-bank.html`

**What it tests:**
- Localhost detection
- Brand keyword detection ("chase" in URL)
- Banking-style login

**Expected Result:** Score 100, BLOCKED

## Testing Different Scenarios

### Scenario 1: Test Pattern Detection Only

Create a file with suspicious pattern in name:
- `paypal-secure-test.html` → Should detect "paypal-secure" pattern
- `arnazon-test.html` → Should detect "arnazon" typo

**Note:** These won't get score 100 (only +20 for pattern), but prove pattern detection works.

### Scenario 2: Test with Different Brands

1. Create `fake-nike.html` with Nike branding
2. Create `fake-apple.html` with Apple branding
3. Visit each - should all be blocked on localhost

### Scenario 3: Test Input Types

Different input fields to test blocking:
- Email inputs
- Password inputs
- Credit card inputs
- CVV inputs
- SSN inputs

## Quick Test Checklist

- [ ] `fake-paypal.html` → Blocks inputs, shows red overlay
- [ ] `fake-amazon-typo.html` → Blocks inputs
- [ ] `fake-amazon-verify.html` → Blocks inputs (including credit card)
- [ ] `fake-chase-bank.html` → Blocks inputs
- [ ] Extension popup shows "DANGER DETECTED" for all
- [ ] Emergency override closes overlay (keeps blocking)
- [ ] Extension popup can unblock inputs

## How to Test

1. **Start demo server:**
   ```bash
   cd demo
   python -m http.server 8080
   ```

2. **Visit each demo site:**
   - `http://localhost:8080/fake-paypal.html`
   - `http://localhost:8080/fake-amazon-typo.html`
   - `http://localhost:8080/fake-amazon-verify.html`
   - `http://localhost:8080/fake-chase-bank.html`

3. **Check VeriSight:**
   - Should show red overlay on all
   - Should block all input fields
   - Should show score 100/100

4. **Test override:**
   - Click "Emergency Override" on overlay → Closes overlay, keeps blocking
   - Use extension popup "Unblock Inputs" → Actually unblocks

## Creating Your Own Test Sites

1. Copy one of the existing demo files
2. Modify the branding (colors, logo text)
3. Change the brand keyword in the filename/URL
4. Test with VeriSight

Example:
- `fake-github.html` → Should trigger if "github" is in URL
- `fake-microsoft.html` → Should trigger if "microsoft" is in URL

## What Each Test Proves

| Demo Site | Tests | Validation |
|-----------|-------|------------|
| fake-paypal.html | Localhost + brand keyword | Works |
| fake-amazon-typo.html | Localhost + brand keyword | Works |
| fake-amazon-verify.html | Localhost + brand + CC input | Works |
| fake-chase-bank.html | Localhost + brand keyword | Works |

All use the same detection logic that would work on real suspicious domains!
