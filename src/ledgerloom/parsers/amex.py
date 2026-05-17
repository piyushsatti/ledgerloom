"""American Express Cobalt statement parser."""

import re
from datetime import datetime as dt

from ledgerloom.parsers import ParseResult, RawTransaction

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

AMEX_TXN_RE = re.compile(
    r"^((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})\s+"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})\s+"
    r"(.+?)\s+"
    r"(-?[\d,]+\.\d{2})\s*$"
)


def parse_amex_statement(text: str) -> ParseResult:
    """Parse an Amex Cobalt statement from extracted text."""

    # Extract period
    period = None
    m = re.search(
        r"Opening Date\s+Closing Date.*?"
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})\s+"
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})",
        text,
        re.DOTALL,
    )
    if m:
        for fmt in ("%b %d, %Y", "%b %d %Y"):
            try:
                start = dt.strptime(m.group(1).replace(",", ""), fmt.replace(",", ""))
                end = dt.strptime(m.group(2).replace(",", ""), fmt.replace(",", ""))
                period = (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                break
            except ValueError:
                continue

    year = 2026
    if period:
        year = int(period[1][:4])

    # Extract summary
    summary = {}
    m = re.search(r"Purchases\s+\$([\d,]+\.\d{2})", text)
    if m:
        summary["purchases"] = float(m.group(1).replace(",", ""))
    m = re.search(r"Fees\s+\$([\d,]+\.\d{2})", text)
    if m:
        summary["fees"] = float(m.group(1).replace(",", ""))
    m = re.search(r"New Balance\s+\$([\d,]+\.\d{2})", text)
    if m:
        summary["new_balance"] = float(m.group(1).replace(",", ""))

    transactions: list[RawTransaction] = []
    lines = text.split("\n")

    for line in lines:
        match = AMEX_TXN_RE.match(line.strip())
        if not match:
            continue

        txn_date_str = match.group(1)
        desc = match.group(3).strip()
        amount = float(match.group(4).replace(",", ""))

        # Parse date
        month_str, day_str = txn_date_str.split()
        month_num = MONTH_MAP.get(month_str, 1)
        day = int(day_str)
        date = f"{year}-{month_num:02d}-{day:02d}"

        # Skip "Total of" summary lines
        if desc.startswith("Total of"):
            continue

        transactions.append(RawTransaction(
            date=date,
            raw_description=desc,
            amount=-abs(amount),   # purchases are money out
            balance=None,
            tx_method="credit_card",
        ))

    # Handle membership fee separately (it's in "Other Account Transactions")
    m = re.search(r"MEMBERSHIP FEE\s+([\d,]+\.\d{2})", text)
    if m:
        fee = float(m.group(1).replace(",", ""))
        fee_date = period[1] if period else f"{year}-04-20"
        transactions.append(RawTransaction(
            date=fee_date,
            raw_description="MEMBERSHIP FEE",
            amount=-fee,
            balance=None,
            tx_method="credit_card",
        ))

    return ParseResult(transactions=transactions, summary=summary, period=period)
