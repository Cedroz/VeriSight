"""
Train a small URL phishing classifier and save to backend/models/url_phishing_bundle.joblib.

Run from repo root:
  python scripts/train_url_phishing_model.py
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

# Repo root
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
MODEL_DIR = BACKEND / "models"
OUT = MODEL_DIR / "url_phishing_bundle.joblib"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from url_ml import normalize_url_for_ml  # noqa: E402


def _benign_urls() -> list[str]:
    bases = [
        "https://www.google.com/search?q=weather",
        "https://github.com/microsoft/vscode",
        "https://www.wikipedia.org/wiki/Python_(programming_language)",
        "https://www.mozilla.org/en-US/firefox/new/",
        "https://developer.chrome.com/docs/extensions/mv3/",
        "https://www.nytimes.com/",
        "https://www.reddit.com/r/programming/",
        "https://stackoverflow.com/questions/tagged/python",
        "https://www.apple.com/iphone/",
        "https://www.amazon.com/gp/help/customer/display.html",
        "https://paypal.com/us/home",
        "https://www.chase.com/",
        "https://www.nike.com/t/air-max-270",
        "https://www.pandora.net/en",
        "https://twitter.com/",
        "https://www.facebook.com/",
        "https://www.linkedin.com/feed/",
        "https://www.netflix.com/browse",
        "https://www.spotify.com/us/",
        "https://www.bbc.com/news",
        "https://www.gov.uk/",
        "https://www.mit.edu/",
        "https://www.stanford.edu/",
        "https://cloud.google.com/",
        "https://aws.amazon.com/console/",
        "https://www.microsoft.com/en-us/microsoft-365",
        "https://www.adobe.com/products/photoshop.html",
        "https://www.shopify.com/",
        "https://www.etsy.com/",
        "https://www.target.com/",
        "https://www.costco.com/",
        "https://www.homedepot.com/",
        "https://www.wikipedia.org/wiki/Open_source",
        "https://gitlab.com/gitlab-org/gitlab",
        "https://bitbucket.org/product",
        "https://www.cloudflare.com/",
        "https://www.digitalocean.com/",
        "https://www.heroku.com/",
        "https://fastapi.tiangolo.com/",
        "https://www.python.org/downloads/",
    ]
    out = list(bases)
    # Variants (same distribution, different paths)
    for b in bases[:15]:
        out.append(b.rstrip("/") + "/about")
        out.append(b + "?ref=home")
    return [normalize_url_for_ml(u) for u in out]


def _phish_urls() -> list[str]:
    raw = [
        "https://paypa1-secure-verify.com/signin",
        "https://paypal-secure-login.net/account/update",
        "https://arnazon-signin.co.uk/ap/signin",
        "https://amaz0n-billing-support.xyz/checkout",
        "https://app1e-id-locked.com/verify",
        "https://secure-chase-update.com/auth",
        "https://chase-verify-secure.net/login",
        "https://n1ke-outlet-sale.ru/cart",
        "https://pand0ra-jewelry-official.tk/shop",
        "https://tw1tter-help-locked.com/confirm",
        "https://faceb00k-security.com/login.php",
        "https://netf1ix-billing-update.com/payment",
        "https://microsoft365-verify.com/outlook",
        "https://google-security-alert.com/verify-account",
        "https://dropb0x-document-share.com/dl",
        "https://dhl-package-pending.com/track",
        "https://usps-reschedule-delivery.xyz/form",
        "https://coinbase-wallet-restore.io/seed",
        "https://binance-support-verify.com/wallet",
        "https://wellsfargo-secure-login.com/signon",
        "https://bankofamerica-secure-update.net/online",
        "https://icloud-findmy-locked.com/unlock",
        "https://office365-password-reset.com/auth",
        "https://zoom-meeting-invite-verify.com/join",
        "https://linkedin-security-confirm.com/login",
        "https://instagram-help-center-locked.com/",
        "https://whatsapp-web-qr-verify.com/",
        "https://telegram-premium-offer.com/join",
        "https://steamcommunity-gift.com/trade",
        "https://roblox-free-robux-generator.com/",
        "https://discord-nitro-gift-free.com/claim",
        "https://ebay-buyer-protection-case.com/respond",
        "https://ups-invoice-payment-required.com/pay",
        "https://fedex-delivery-fee.com/confirm",
        "https://irs-tax-refund-pending.com/submit",
        "https://social-security-suspended.com/restore",
        "https://amazon-prime-renewal-billing.com/update",
        "https://secure-paypal-com-accounts.com/cgi-bin",
        "https://login-microsoftonline-com-verify.com/",
        "https://signin-amazon-com-secure.co/ap/signin",
    ]
    out = list(raw)
    for host in ["verify-billing", "secure-login", "account-update", "auth-confirm"]:
        for tld in [".tk", ".ml", ".ga", ".cf", ".xyz", ".ru", ".top"]:
            out.append(f"https://{host}-service{tld}/index.php")
    combos = itertools.product(
        ["paypal", "amazon", "apple", "chase"],
        ["-secure", "-verify", "-update", "-billing"],
        [".tk", ".xyz", ".ru"],
    )
    for a, b, c in list(combos)[:24]:
        out.append(f"https://{a}{b}{c}/login")
    return [normalize_url_for_ml(u) for u in out]


def main() -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    import joblib

    X_bad = _phish_urls()
    X_good = _benign_urls()
    X = X_good + X_bad
    y = [0] * len(X_good) + [1] * len(X_bad)

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, max_features=8000),
            ),
            (
                "clf",
                LogisticRegression(max_iter=400, class_weight="balanced", random_state=42),
            ),
        ]
    )
    pipeline.fit(X, y)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "version": "1.0.0"}, OUT)
    print(f"Wrote {OUT} ({len(X)} samples)")


if __name__ == "__main__":
    main()
