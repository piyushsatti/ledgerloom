"""Transaction categorization — rules loaded from config/categories.yaml."""

import sqlite3

from ledgerloom.config import load_categories


def categorize(merchant: str | None, raw_description: str) -> tuple[str, str]:
    """Assign (category, subcategory) based on normalized merchant name.

    Rules are read from load_categories() in yaml document order; first
    matching keyword wins.  Falls back to matching raw_description for
    income/transfer/fee patterns.

    If load_categories() returns an empty list, returns ("Uncategorized", "")
    for any input without raising.
    """
    rules = load_categories()
    if not rules:
        return "Uncategorized", ""

    if merchant:
        for rule in rules:
            for keyword in rule.keywords:
                if keyword.lower() in merchant.lower():
                    return rule.category, rule.subcategory

    upper = raw_description.upper()
    for rule in rules:
        for keyword in rule.keywords:
            if keyword.upper() in upper:
                return rule.category, rule.subcategory

    return "Uncategorized", ""


def recategorize_all(conn: sqlite3.Connection) -> int:
    """Re-run categorization on all transactions in the DB."""
    rows = conn.execute(
        "SELECT id, merchant, raw_description FROM transactions"
    ).fetchall()
    count = 0
    for tid, merchant, raw_desc in rows:
        cat, subcat = categorize(merchant, raw_desc)
        conn.execute(
            "UPDATE transactions SET category = ?, subcategory = ? WHERE id = ?",
            (cat, subcat, tid),
        )
        count += 1
    conn.commit()
    return count
