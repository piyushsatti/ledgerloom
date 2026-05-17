"""RBC bank/savings statement parser."""

import re
from datetime import datetime as dt

from ledgerloom.parsers import ParseResult, RawTransaction


# ============================================================
# Constants
# ============================================================

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

DATE_RE = re.compile(
    r"^\s*(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s"
)
AMOUNT_RE = re.compile(r"(\d{1,3}(?:,\d{3})*\.\d{2})")
NEGATIVE_BALANCE_RE = re.compile(r"-\s+([\d,]+\.\d{2})\s*$")

SKIP_LINES = [
    "Opening Balance", "Closing Balance", "Details of your",
    "continued", "RBPDA", "Important information", "Royal Bank of Canada",
    "Your RBC", "personal banking", "personal savings", "account statement",
    "From ", "Protect your", "Never share", "Please check",
    "Here are four", "Don't pick up", "Never give", "Beware of",
    "Don't buy", "Stay Informed", "https://", "C.P. 6011",
    "Montreal QC", "How to reach", "1-800-ROYAL", "www.rbc",
    "Summary of your", "RBC Advantage", "RBC High Interest",
    "Find & SaveTM", "Your opening balance",
    "Total deposits", "Total withdrawals", "Your closing balance",
    "Your account number", "Registered trade-mark", "GST Registration",
    "Please retain", "If you opted", "account for this period",
    "No activity for this period",
    "HRI -",
]

# tx_method prefix mapping: (prefix_string, tx_method_value)
_TX_METHOD_PREFIXES = [
    ("Contactless Interac purchase", "interac"),
    ("Visa Debit purchase", "visa_debit"),
    ("Visa Debit refund", "visa_debit"),
    ("Visa Debit correction", "visa_debit"),
    ("Online Banking transfer", "online"),
    ("Online Transfer to Deposit", "online"),
    ("Online Banking payment", "online"),
    ("e-Transfer sent", "etransfer"),
    ("e-Transfer received", "etransfer"),
    ("e-Transfer - Autodeposit", "etransfer"),
    ("ATM withdrawal", "atm"),
    ("ATM deposit", "atm"),
    ("Misc Payment", "misc"),
    ("Interac Transit", "transit"),
    ("Contactless Interac Transit", "transit"),
    ("Payroll Deposit", "payroll"),
    ("International remittance", "remittance"),
    ("Telephone Bill", "online"),
    ("Monthly fee", "bank"),
    ("Overdraft", "bank"),
    ("NSF", "bank"),
    ("Deposit interest", "bank"),
]


# ============================================================
# Helpers
# ============================================================

def should_skip(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("*") and stripped.endswith("*"):
        return True
    for skip in SKIP_LINES:
        if skip in line:
            return True
    # Skip lines that are just page numbers
    if re.match(r"^\s*\d+\s+of\s+\d+\s*$", stripped):
        return True
    return False


def extract_summary(text: str) -> dict:
    """Extract opening/closing balance and totals from statement summary."""
    summary = {}
    m = re.search(r"opening balance.*?\$([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        summary["opening"] = float(m.group(1).replace(",", ""))
    m = re.search(r"Total deposits.*?\+\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        summary["deposits"] = float(m.group(1).replace(",", ""))
    m = re.search(r"Total withdrawals.*?-\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        summary["withdrawals"] = float(m.group(1).replace(",", ""))
    m = re.search(r"closing balance.*?=?\s*\$?([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        summary["closing"] = float(m.group(1).replace(",", ""))
    return summary


def extract_period(text: str) -> tuple[str, str] | None:
    """Extract statement period dates and return (start, end) as YYYY-MM-DD."""
    m = re.search(
        r"From\s+(\w+\s+\d{1,2},?\s+\d{4})\s+to\s+(\w+\s+\d{1,2},?\s+\d{4})",
        text,
    )
    if not m:
        return None
    for fmt in ("%B %d, %Y", "%B %d %Y"):
        try:
            start = dt.strptime(m.group(1).replace(",", ""), fmt.replace(",", ""))
            end = dt.strptime(m.group(2).replace(",", ""), fmt.replace(",", ""))
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _get_tx_method(description: str) -> str | None:
    """Determine tx_method from the description prefix."""
    for prefix, method in _TX_METHOD_PREFIXES:
        if description.startswith(prefix):
            return method
    return None


# ============================================================
# Parser
# ============================================================

def parse_rbc_statement(text: str) -> ParseResult:
    """Parse an RBC bank/savings statement from extracted text."""
    lines = text.split("\n")

    summary = extract_summary(text)
    period = extract_period(text)

    year_start = year_end = None
    if period:
        year_start = int(period[0][:4])
        year_end = int(period[1][:4])

    transactions: list[RawTransaction] = []
    w_col = d_col = b_col = None
    current_date = None
    pending_desc_parts: list[str] = []

    for line in lines:
        # Detect header row to find column positions
        if "Withdrawals ($)" in line and "Deposits ($)" in line and "Balance ($)" in line:
            w_col = line.index("Withdrawals")
            d_col = line.index("Deposits")
            b_col = line.index("Balance")
            pending_desc_parts = []
            continue

        if w_col is None:
            continue

        if should_skip(line):
            # Reset column positions on page breaks
            if "Your RBC" in line or "Royal Bank of Canada" in line:
                w_col = d_col = b_col = None
            continue

        # Check for date
        date_match = DATE_RE.match(line)
        if date_match:
            day = int(date_match.group(1))
            month_num = MONTH_MAP[date_match.group(2)]
            if year_start and year_end:
                year = year_start if month_num >= 10 and year_end > year_start else year_end
            else:
                year = 2026
            current_date = f"{year}-{month_num:02d}-{day:02d}"
            desc_offset = date_match.end()
        else:
            desc_offset = 0

        # Find amounts on this line
        amounts = list(AMOUNT_RE.finditer(line))
        # Also check for negative balance at end of line
        neg_match = NEGATIVE_BALANCE_RE.search(line)

        if not amounts:
            # Pure description line — accumulate
            desc_part = line[desc_offset:].strip()
            # Don't accumulate if it looks like noise
            if desc_part and len(desc_part) > 1 and not desc_part.startswith("*"):
                pending_desc_parts.append(desc_part)
            continue

        # Line has amounts — this is a transaction line
        first_amt_pos = amounts[0].start()
        desc_text = line[desc_offset:first_amt_pos].strip()

        # Build full description
        if pending_desc_parts:
            if desc_text:
                full_desc = " ".join(pending_desc_parts) + " " + desc_text
            else:
                full_desc = " ".join(pending_desc_parts)
            pending_desc_parts = []
        else:
            full_desc = desc_text

        # Clean description
        full_desc = re.sub(r"\s+", " ", full_desc).strip()

        # Classify each amount by column position
        withdrawal = deposit = balance = None
        for amt in amounts:
            pos = amt.start()
            val = float(amt.group(1).replace(",", ""))

            # Use midpoints between known columns
            mid_wd = (w_col + d_col) / 2
            mid_db = (d_col + b_col) / 2

            if pos >= mid_db:
                balance = val
            elif pos >= mid_wd:
                deposit = val
            else:
                withdrawal = val

        # Handle negative balance
        if neg_match:
            balance = -float(neg_match.group(1).replace(",", ""))

        if (withdrawal is not None or deposit is not None) and current_date:
            amount = deposit if deposit is not None else -withdrawal
            tx_method = _get_tx_method(full_desc)
            transactions.append(RawTransaction(
                date=current_date,
                raw_description=full_desc,
                amount=amount,
                balance=balance,
                tx_method=tx_method,
            ))
        else:
            # Only balance on this line — might be end-of-day balance update
            # Attach balance to previous transaction if same date
            if balance is not None and transactions and transactions[-1].date == current_date:
                transactions[-1].balance = balance

    return ParseResult(transactions=transactions, summary=summary, period=period)
