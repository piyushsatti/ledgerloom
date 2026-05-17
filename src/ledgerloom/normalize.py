"""Merchant name extraction and normalization."""

import re

from ledgerloom.config import load_merchants

# Prefixes to strip from raw descriptions to get the merchant name
_TX_PREFIXES = [
    r"Contactless Interac purchase - \w+\s*",
    r"Contactless Interac Transit - \w+\s*",
    r"Interac purchase - \w+\s*",
    r"Interac Transit - \w+\s*",
    r"Visa Debit purchase - \w+\s*",
    r"Visa Debit refund - \w+\s*",
    r"Visa Debit correction - \w+\s*",
    r"Online Banking payment - \w+\s*",
    r"Misc Payment\s*",
]
_PREFIX_RE = re.compile("|".join(f"^(?:{p})" for p in _TX_PREFIXES), re.IGNORECASE)


def extract_merchant(raw_description: str) -> str | None:
    """Strip transaction prefix and return the merchant portion.

    The prefix list (_TX_PREFIXES) is RBC-statement-format-bound.
    Generalizing to other statement formats is P3 parser-skill scope.
    """
    cleaned = _PREFIX_RE.sub("", raw_description).strip()
    return cleaned if cleaned else None


def normalize_merchant(merchant: str | None) -> str | None:
    """Map a raw merchant string to its canonical name.

    Merchant map is loaded from config/merchants.yaml via load_merchants().
    Iteration order is yaml document order; first match wins.

    - merchant is None  -> returns None
    - load_merchants() == {} -> returns merchant.strip()
    - otherwise: matches pattern.upper() in merchant.upper(); first hit wins;
      fallback merchant.strip()
    """
    if merchant is None:
        return None
    mapping = load_merchants()
    if not mapping:
        return merchant.strip()
    upper = merchant.upper()
    for pattern, canonical in mapping.items():
        if pattern.upper() in upper:
            return canonical
    return merchant.strip()
