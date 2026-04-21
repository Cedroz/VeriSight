"""
Lightweight URL phishing risk model (TF-IDF char n-grams + logistic regression).
Loads a pre-trained bundle from backend/models/; safe no-op if missing.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_REL = Path("models") / "url_phishing_bundle.joblib"


def normalize_url_for_ml(url: str) -> str:
    """Single string for vectorization: lowercase host + path, no scheme noise."""
    u = url.strip().lower()
    if not u.startswith(("http://", "https://")):
        u = "http://" + u
    u = re.sub(r"^https?://", "", u)
    u = u.split("#", 1)[0]
    return u[:2048]


class UrlPhishingClassifier:
    """Wraps sklearn pipeline trained on URL strings."""

    def __init__(self, pipeline: Any, version: str = "1.0.0") -> None:
        self.pipeline = pipeline
        self.version = version

    @classmethod
    def load(cls, path: Optional[Path] = None) -> Optional["UrlPhishingClassifier"]:
        try:
            import joblib
        except ImportError:
            logger.warning("joblib/sklearn not installed; URL ML disabled.")
            return None
        p = path or (Path(__file__).resolve().parent / _DEFAULT_MODEL_REL)
        if not p.is_file():
            logger.info("URL ML bundle not found at %s; URL ML disabled.", p)
            return None
        try:
            bundle = joblib.load(p)
            pipeline = bundle["pipeline"]
            version = str(bundle.get("version", "1.0.0"))
            return cls(pipeline=pipeline, version=version)
        except Exception as e:
            logger.warning("Failed to load URL ML bundle: %s", e)
            return None

    def predict(self, url: str) -> Dict[str, Any]:
        text = normalize_url_for_ml(url)
        try:
            proba = float(self.pipeline.predict_proba([text])[0, 1])
            return {
                "phishing_probability": round(proba, 4),
                "model_version": self.version,
                "enabled": True,
                "error": None,
            }
        except Exception as e:
            return {
                "phishing_probability": None,
                "model_version": self.version,
                "enabled": True,
                "error": str(e),
            }
