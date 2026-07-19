"""Parser for AMEX activity CSV exports.

Header: Date,Date Processed,Description,Amount,Foreign Spend Amount,Commission,
Exchange Rate,Additional Information,Merchant,Address,City / Province,
Postal Code,Country,Reference

Dates look like "18 Jul 2026" and are normalized to YYYY-MM-DD.

Sign convention: the file's Amount is POSITIVE for a charge (money out) and
NEGATIVE for a credit/refund/payment (money in) — the opposite of LedgerLoom's
convention (negative = out, positive = in). Amount is negated on the way in.

Some rows contain embedded newlines inside quoted fields (e.g. "City /
Province" spans two physical lines like "TORONTO\\nON"); the stdlib csv
module parses these correctly as long as the file is read in a single pass
(not line-by-line), which is what csv.DictReader does here.
"""

import csv
from datetime import datetime

from ledgerloom.parsers import ParseResult, RawTransaction


def _parse_date(raw: str | None) -> str | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%d %b %Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_amex_csv(csv_path: str) -> ParseResult:
    """Parse an AMEX activity CSV export into a ParseResult.

    Skips rows with an unparseable date, empty description, or unparseable
    amount rather than raising. summary is always {} (activity exports carry
    no statement summary).
    """
    transactions: list[RawTransaction] = []

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return ParseResult()

        for row in reader:
            date = _parse_date(row.get("Date"))
            if date is None:
                continue

            desc = (row.get("Description") or "").strip()
            if not desc:
                continue

            amount_str = (row.get("Amount") or "").strip()
            if not amount_str:
                continue
            try:
                amount = -float(amount_str)
            except ValueError:
                continue

            transactions.append(
                RawTransaction(
                    date=date,
                    raw_description=desc,
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
