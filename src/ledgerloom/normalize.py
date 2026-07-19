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
    # Scotia CSV tx-type words (P3 generalization: combined description is
    # "{Description} {Sub-description}", e.g. "pos purchase Apos Marche...").
    r"Payroll Deposit\s*",
    r"Pos Purchase\s*",
    r"Withdrawal\s*",
    r"Deposit\s*",
    # Scotia POS sub-description artifact, e.g. "Apos Marche Tharsini".
    r"Apos\s+",
]
_PREFIX_RE = re.compile("|".join(f"^(?:{p})" for p in _TX_PREFIXES), re.IGNORECASE)


def extract_merchant(raw_description: str) -> str | None:
    """Strip transaction prefix(es) and return the merchant portion.

    The prefix list (_TX_PREFIXES) started RBC-PDF-statement-format-bound and
    has been generalized (P3) to also cover Scotia's CSV format, which stacks
    two prefixes ("pos purchase" tx-type word, then "Apos" POS artifact) on
    one combined description. The regex is applied repeatedly until a pass
    makes no further change, so stacked prefixes are all stripped.
    """
    cleaned = raw_description.strip()
    while True:
        new_cleaned = _PREFIX_RE.sub("", cleaned).strip()
        if new_cleaned == cleaned:
            break
        cleaned = new_cleaned
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
