"""Pipeline orchestrator: extract → parse → normalize → categorize → insert."""

from pathlib import Path
from typing import Callable

from ledgerloom import db
from ledgerloom.config import DataSource
from ledgerloom.extract import extract_pdf
from ledgerloom.normalize import extract_merchant, normalize_merchant
from ledgerloom.categorize import categorize
from ledgerloom.parsers import RawTransaction
from ledgerloom.parsers.rbc import parse_rbc_statement
from ledgerloom.parsers.rbc_credit import parse_rbc_credit
from ledgerloom.parsers.amex import parse_amex_statement
from ledgerloom.parsers.splitwise import parse_splitwise_csv
from ledgerloom.parsers.rbc_csv import parse_rbc_csv
from ledgerloom.parsers.amex_csv import parse_amex_csv
from ledgerloom.parsers.scotia import parse_scotia


# ---------------------------------------------------------------------------
# Parser registry
# ---------------------------------------------------------------------------

# Keys: parser name (matches DataSource.parser / user_config.sources[*].parser).
# Values: (kind, callable) where kind ∈ {"pdf", "csv"}.
#   - pdf callables: (text: str) -> ParseResult
#   - csv callables: (path: str) -> tuple[list[SplitExpense], list[SplitPayment]]
#     (splitwise) or (path: str) -> ParseResult (generic csv parsers)
PARSER_REGISTRY: dict[str, tuple[str, Callable]] = {
    "rbc": ("pdf", parse_rbc_statement),
    "rbc_credit": ("pdf", parse_rbc_credit),
    "amex": ("pdf", parse_amex_statement),
    "splitwise": ("csv", parse_splitwise_csv),
    "rbc_csv": ("csv", parse_rbc_csv),
    "amex_csv": ("csv", parse_amex_csv),
    "scotia": ("csv", parse_scotia),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _detect_account(pdf_path: Path) -> tuple[str, str]:
    """Determine account suffix and parser type from filename/path.

    Maps filename keywords to (suffix, parser_name) pairs using generic
    statement-type keywords rather than personal account suffixes.
    Account suffix values come from the DEFAULT_ACCOUNTS seeded in db.py;
    configure your own in user_config.yaml (sources section) for production use.
    """
    name = pdf_path.name.lower()
    if "checking" in name:
        return "0001", "rbc"
    if "savings" in name and "0003" in name:
        return "0003", "rbc"
    if "savings" in name:
        return "0002", "rbc"
    if "credit card" in name or "credit" in name:
        return "0004", "rbc_credit"
    if pdf_path.parent.name == "amex":
        return "0005", "amex"
    raise ValueError(f"Cannot detect account for: {pdf_path}")


def _transform(txns: list[RawTransaction]) -> list[dict]:
    """Apply normalization + categorization to parsed transactions."""
    results = []
    for t in txns:
        merchant_raw = extract_merchant(t.raw_description)
        merchant = normalize_merchant(merchant_raw)
        cat, subcat = categorize(merchant, t.raw_description)
        results.append(
            {
                "date": t.date,
                "raw_description": t.raw_description,
                "merchant": merchant,
                "amount": t.amount,
                "balance": t.balance,
                "tx_method": t.tx_method,
                "category": cat,
                "subcategory": subcat,
            }
        )
    return results


# ---------------------------------------------------------------------------
# Per-file ingest helpers (unchanged public API)
# ---------------------------------------------------------------------------


def ingest_pdf(conn, pdf_path: Path, cache_dir: Path) -> int:
    """Full pipeline for one PDF. Returns transaction count, or 0 if already imported."""
    fhash = db.file_hash(str(pdf_path))
    if db.source_exists(conn, fhash):
        return 0

    suffix, parser_name = _detect_account(pdf_path)
    account_id = db.get_account_id(conn, suffix)

    text = extract_pdf(pdf_path, cache_dir)

    kind, fn = PARSER_REGISTRY[parser_name]
    result = fn(text)

    period_start = result.period[0] if result.period else None
    period_end = result.period[1] if result.period else None

    source_id = db.insert_source(
        conn, str(pdf_path), fhash, account_id, period_start, period_end
    )

    transformed = _transform(result.transactions)
    count = db.insert_transactions(conn, source_id, account_id, transformed)

    if result.summary:
        db.insert_summary(conn, source_id, result.summary)

    conn.commit()
    return count


def ingest_splitwise_csv(conn, csv_path: Path) -> tuple[int, int]:
    """Ingest a Splitwise CSV. Returns (expense_count, payment_count)."""
    expenses, payments = parse_splitwise_csv(str(csv_path))

    for exp in expenses:
        db.insert_splitwise_expense(conn, exp)
    for pmt in payments:
        db.insert_splitwise_payment(conn, pmt)

    conn.commit()
    return len(expenses), len(payments)


# ---------------------------------------------------------------------------
# Per-source ingest helper (new in P2.T8)
# ---------------------------------------------------------------------------


def ingest_source(conn, source: DataSource, cache_dir: Path) -> dict:
    """Ingest all files for one DataSource entry.

    Looks up (kind, fn) in PARSER_REGISTRY[source.parser].  Scans source.path
    for *.pdf or *.csv files depending on kind, and dispatches each file.

    Returns a stats-dict with keys: pdfs, transactions, sw_expenses,
    sw_payments, skipped.  Mirrors the shape returned by ingest_all.
    """
    stats: dict = {
        "pdfs": 0,
        "transactions": 0,
        "sw_expenses": 0,
        "sw_payments": 0,
        "skipped": 0,
    }

    if source.parser not in PARSER_REGISTRY:
        raise ValueError(
            f"unknown parser '{source.parser}' — register in PARSER_REGISTRY"
        )

    kind, _fn = PARSER_REGISTRY[source.parser]
    source_path = Path(source.path)

    if kind == "pdf":
        for pdf in sorted(source_path.rglob("*.pdf")):
            count = ingest_pdf(conn, pdf, cache_dir)
            if count > 0:
                print(f"  {pdf.name}: {count} transactions")
                stats["pdfs"] += 1
                stats["transactions"] += count
            else:
                stats["skipped"] += 1

    elif kind == "csv":
        for csv_file in sorted(source_path.rglob("*.csv")):
            if source.parser == "splitwise":
                exp_count, pmt_count = ingest_splitwise_csv(conn, csv_file)
                print(f"  {csv_file.name}: {exp_count} expenses, {pmt_count} payments")
                stats["sw_expenses"] += exp_count
                stats["sw_payments"] += pmt_count
            else:
                # Generic CSV path for future parsers
                _kind2, fn2 = PARSER_REGISTRY[source.parser]
                result = fn2(str(csv_file))
                fhash = db.file_hash(str(csv_file))
                if db.source_exists(conn, fhash):
                    stats["skipped"] += 1
                    continue
                suffix = source.account_suffix or source.name
                account_id = db.get_account_id(conn, suffix)
                period_start = result.period[0] if result.period else None
                period_end = result.period[1] if result.period else None
                source_id = db.insert_source(
                    conn, str(csv_file), fhash, account_id, period_start, period_end
                )
                transformed = _transform(result.transactions)
                count = db.insert_transactions(conn, source_id, account_id, transformed)
                conn.commit()
                print(f"  {csv_file.name}: {count} transactions")
                stats["pdfs"] += 1
                stats["transactions"] += count

    return stats


# ---------------------------------------------------------------------------
# Backward-compat shim (P3.T4 will replace this)
# ---------------------------------------------------------------------------


def ingest_all(conn, data_dir: Path, cache_dir: Path) -> dict:
    """Scan data/ and ingest everything new. Returns summary stats.

    This shim is superseded by P3.T4 which iterates config.sources via
    PARSER_REGISTRY instead of scanning hardcoded directories.
    """
    stats = {
        "pdfs": 0,
        "transactions": 0,
        "sw_expenses": 0,
        "sw_payments": 0,
        "skipped": 0,
    }

    for pdf in sorted(data_dir.rglob("*.pdf")):
        count = ingest_pdf(conn, pdf, cache_dir)
        if count > 0:
            print(f"  {pdf.name}: {count} transactions")
            stats["pdfs"] += 1
            stats["transactions"] += count
        else:
            stats["skipped"] += 1

    sw_dir = data_dir / "splitwise"
    if sw_dir.exists():
        for csv_file in sorted(sw_dir.glob("*_export.csv")):
            exp_count, pmt_count = ingest_splitwise_csv(conn, csv_file)
            print(f"  {csv_file.name}: {exp_count} expenses, {pmt_count} payments")
            stats["sw_expenses"] += exp_count
            stats["sw_payments"] += pmt_count

    return stats
