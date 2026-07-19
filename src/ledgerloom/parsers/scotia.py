"""Parser for Scotiabank CSV exports.

Header (BOM-prefixed): Filter,Date,Description,Sub-description,Type of
Transaction,Amount,Balance

Filter only carries a label ("Current statement period") on the first data
row and is blank on the rest — ignored entirely.

Dates are already ISO (YYYY-MM-DD) — used as-is.

Sign convention: Amount is already signed (negative = debit/out, positive =
credit/in) per LedgerLoom's convention — used as-is, no negation. Balance is
carried through to RawTransaction.balance.

Description is the transaction type (e.g. "pos purchase", "deposit",
"payroll deposit", "withdrawal"); Sub-description holds the merchant text
(e.g. "Apos Marche Tharsini     Montr "). raw_description combines them as
"{Description} {Sub-description}" with internal whitespace runs collapsed to
a single space — faithful-ish but readable. The "Apos " artifact and
tx-type-word prefix are stripped later, in normalize.extract_merchant, not
here.

tx_method is a best-effort mapping from Description; unrecognized types fall
back to None.
"""

import csv
import re

from ledgerloom.parsers import ParseResult, RawTransaction

_WS_RE = re.compile(r"\s+")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_TX_METHOD_MAP = {
    "pos purchase": "pos",
    "withdrawal": "withdrawal",
    "deposit": "deposit",
    "payroll deposit": "deposit",
    "bill payment": "billpay",
}


def _tx_method(description: str) -> str | None:
    desc_lower = description.strip().lower()
    if "e-transfer" in desc_lower:
        return "etransfer"
    return _TX_METHOD_MAP.get(desc_lower)


def parse_scotia(csv_path: str) -> ParseResult:
    """Parse a Scotiabank CSV export into a ParseResult.

    Skips rows with a non-ISO date, empty combined description, or
    unparseable Amount rather than raising. summary is always {} (activity
    exports carry no statement summary).
    """
    transactions: list[RawTransaction] = []

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return ParseResult()

        for row in reader:
            date = (row.get("Date") or "").strip()
            if not _DATE_RE.match(date):
                continue

            description = (row.get("Description") or "").strip()
            sub_description = (row.get("Sub-description") or "").strip()
            raw_description = _WS_RE.sub(
                " ", f"{description} {sub_description}"
            ).strip()
            if not raw_description:
                continue

            amount_str = (row.get("Amount") or "").strip()
            if not amount_str:
                continue
            try:
                amount = float(amount_str)
            except ValueError:
                continue

            balance_str = (row.get("Balance") or "").strip()
            balance = None
            if balance_str:
                try:
                    balance = float(balance_str)
                except ValueError:
                    balance = None

            transactions.append(
                RawTransaction(
                    date=date,
                    raw_description=raw_description,
                    amount=amount,
                    balance=balance,
                    tx_method=_tx_method(description),
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
