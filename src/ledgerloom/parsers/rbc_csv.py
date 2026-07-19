"""Parser for RBC online-banking CSV exports (as opposed to statement PDFs).

Header (BOM-prefixed): Account Type,Account Number,Transaction Date,Cheque
Number,Description 1,Description 2,CAD$,USD$

Dates look like "7/7/2026" (M/D/YYYY, not zero-padded) and are normalized to
YYYY-MM-DD.

Sign convention: CAD$ is already signed (negative = out, positive = in) per
LedgerLoom's convention — used as-is, no negation. USD$ is ignored (foreign-
currency rows are out of scope for this pipeline; the column is also often
empty).

raw_description joins Description 1 and Description 2 with two spaces when
Description 2 is non-empty, else falls back to Description 1 alone.
"""

import csv
from datetime import datetime

from ledgerloom.parsers import ParseResult, RawTransaction


def _parse_date(raw: str | None) -> str | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_rbc_csv(csv_path: str) -> ParseResult:
    """Parse an RBC online-banking CSV export into a ParseResult.

    Skips rows with an unparseable date, empty description, or unparseable
    CAD$ amount rather than raising. summary is always {} (activity exports
    carry no statement summary).
    """
    transactions: list[RawTransaction] = []

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return ParseResult()

        for row in reader:
            date = _parse_date(row.get("Transaction Date"))
            if date is None:
                continue

            desc1 = (row.get("Description 1") or "").strip()
            desc2 = (row.get("Description 2") or "").strip()
            if not desc1 and not desc2:
                continue
            raw_description = f"{desc1}  {desc2}" if desc2 else desc1

            amount_str = (row.get("CAD$") or "").strip()
            if not amount_str:
                continue
            try:
                amount = float(amount_str)
            except ValueError:
                continue

            transactions.append(
                RawTransaction(
                    date=date,
                    raw_description=raw_description,
                    amount=amount,
                )
            )

    if not transactions:
        return ParseResult()

    dates = [t.date for t in transactions]
    return ParseResult(
        transactions=transactions,
        summary={},
        period=(min(dates), max(dates)),
    )
