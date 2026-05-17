"""RBC Cash Back Mastercard statement parser."""

import re
from datetime import datetime as dt

from ledgerloom.parsers import ParseResult, RawTransaction

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

# RBC credit card format: DATE  DATE  ACTIVITY DESCRIPTION  AMOUNT ($)
_CC_RE = re.compile(
    r"^((?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{1,2})\s+"
    r"((?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{1,2})\s+"
    r"(.+?)\s+"
    r"(-?\$?[\d,]+\.\d{2})\s*$",
    re.IGNORECASE,
)


def parse_rbc_credit(text: str) -> ParseResult:
    """Parse an RBC Cash Back Mastercard statement from extracted text."""

    # Extract period
    period = None
    m = re.search(
        r"STATEMENT FROM\s+(.*?)\s+TO\s+(.*?)$",
        text, re.MULTILINE | re.IGNORECASE,
    )
    if m:
        for fmt in ("%b %d, %Y", "%b %d %Y", "%B %d, %Y", "%B %d %Y"):
            try:
                start = dt.strptime(m.group(1).strip().replace(",", ""), fmt.replace(",", ""))
                end = dt.strptime(m.group(2).strip().replace(",", ""), fmt.replace(",", ""))
                period = (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                break
            except ValueError:
                continue

    year = 2026
    if period:
        year = int(period[1][:4])

    transactions: list[RawTransaction] = []

    for line in text.split("\n"):
        match = _CC_RE.match(line.strip())
        if not match:
            continue

        txn_date_str = match.group(1).strip()
        desc = match.group(3).strip()
        amount_str = match.group(4).replace("$", "").replace(",", "")
        amount = float(amount_str)

        parts = txn_date_str.split()
        month_str = parts[0].capitalize()[:3]
        day = int(parts[1])
        month_num = MONTH_MAP.get(month_str, 1)
        date = f"{year}-{month_num:02d}-{day:02d}"

        # Negative amounts on CC statements are credits/payments
        # Positive amounts are charges
        if amount < 0:
            signed_amount = abs(amount)   # credit = money coming back
        else:
            signed_amount = -amount       # charge = money going out

        transactions.append(RawTransaction(
            date=date,
            raw_description=desc,
            amount=signed_amount,
            balance=None,
            tx_method="credit_card",
        ))

    summary = {}
    m = re.search(r"Total Account Balance\s+(-?\$?[\d,]+\.\d{2})", text)
    if m:
        summary["balance"] = float(m.group(1).replace("$", "").replace(",", ""))

    return ParseResult(transactions=transactions, summary=summary, period=period)
