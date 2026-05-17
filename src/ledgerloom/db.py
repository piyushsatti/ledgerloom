"""Database schema, connection helpers, and insert functions."""

import hashlib
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    institution TEXT NOT NULL,
    account_suffix TEXT
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    account_id INTEGER,
    period_start TEXT,
    period_end TEXT,
    imported_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    raw_description TEXT NOT NULL,
    merchant TEXT,
    amount REAL NOT NULL,
    balance REAL,
    tx_method TEXT,
    category TEXT,
    subcategory TEXT,
    is_recurring INTEGER DEFAULT 0,
    metadata TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS splitwise_expenses (
    id INTEGER PRIMARY KEY,
    source_file TEXT,
    group_name TEXT,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    sw_category TEXT,
    total_cost REAL,
    user_share REAL,
    counterparties TEXT
);

CREATE TABLE IF NOT EXISTS splitwise_payments (
    id INTEGER PRIMARY KEY,
    source_file TEXT,
    group_name TEXT,
    date TEXT NOT NULL,
    from_person TEXT NOT NULL,
    to_person TEXT NOT NULL,
    amount REAL NOT NULL,
    linked_txn_id INTEGER,
    FOREIGN KEY (linked_txn_id) REFERENCES transactions(id)
);

CREATE TABLE IF NOT EXISTS statement_summary (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL,
    opening_balance REAL,
    total_deposits REAL,
    total_withdrawals REAL,
    closing_balance REAL,
    FOREIGN KEY (source_id) REFERENCES sources(id)
);

CREATE VIEW IF NOT EXISTS v_monthly_spending AS
SELECT
    strftime('%Y-%m', date) AS month,
    category,
    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS spent,
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS received,
    COUNT(*) AS txn_count
FROM transactions
GROUP BY month, category
ORDER BY month, spent DESC;

CREATE VIEW IF NOT EXISTS v_daily_totals AS
SELECT
    date,
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS money_in,
    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS money_out,
    SUM(amount) AS net
FROM transactions
GROUP BY date
ORDER BY date;

CREATE VIEW IF NOT EXISTS v_merchant_spending AS
SELECT
    category,
    subcategory,
    merchant,
    COUNT(*) AS times,
    ROUND(SUM(ABS(amount)), 2) AS total,
    ROUND(SUM(ABS(amount)) / COUNT(*), 2) AS avg_per_visit
FROM transactions
WHERE amount < 0 AND merchant IS NOT NULL
GROUP BY merchant
ORDER BY total DESC;
"""

# Generic placeholder accounts — replace with your own account names and suffixes
# by editing config/user_config.yaml (sources section) before running build_db.py.
DEFAULT_ACCOUNTS = [
    ("Checking 0001", "checking", "Bank", "0001"),
    ("Savings 0002", "savings", "Bank", "0002"),
    ("Savings 0003", "savings", "Bank", "0003"),
    ("Credit Card 0004", "credit_card", "Bank", "0004"),
    ("Credit Card 0005", "credit_card", "Bank", "0005"),
]


def create_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    for name, atype, inst, suffix in DEFAULT_ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts (name, type, institution, account_suffix) "
            "VALUES (?, ?, ?, ?)",
            (name, atype, inst, suffix),
        )
    conn.commit()
    return conn


def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def source_exists(conn: sqlite3.Connection, fhash: str) -> bool:
    row = conn.execute("SELECT 1 FROM sources WHERE file_hash = ?", (fhash,)).fetchone()
    return row is not None


def get_account_id(conn: sqlite3.Connection, suffix: str) -> int:
    row = conn.execute(
        "SELECT id FROM accounts WHERE account_suffix = ?", (suffix,)
    ).fetchone()
    if not row:
        raise ValueError(f"No account with suffix {suffix}")
    return row[0]


def insert_source(conn: sqlite3.Connection, file_path: str, fhash: str,
                   account_id: int, period_start: str | None,
                   period_end: str | None) -> int:
    cur = conn.execute(
        "INSERT INTO sources (file_path, file_hash, account_id, period_start, period_end) "
        "VALUES (?, ?, ?, ?, ?)",
        (file_path, fhash, account_id, period_start, period_end),
    )
    return cur.lastrowid


def insert_transactions(conn: sqlite3.Connection, source_id: int,
                         account_id: int, rows: list[dict]) -> int:
    for r in rows:
        conn.execute(
            "INSERT INTO transactions "
            "(source_id, account_id, date, raw_description, merchant, amount, "
            "balance, tx_method, category, subcategory, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (source_id, account_id, r["date"], r["raw_description"],
             r.get("merchant"), r["amount"], r.get("balance"),
             r.get("tx_method"), r.get("category"), r.get("subcategory"),
             r.get("metadata")),
        )
    return len(rows)


def insert_summary(conn: sqlite3.Connection, source_id: int, summary: dict):
    conn.execute(
        "INSERT INTO statement_summary "
        "(source_id, opening_balance, total_deposits, total_withdrawals, closing_balance) "
        "VALUES (?, ?, ?, ?, ?)",
        (source_id, summary.get("opening"), summary.get("deposits"),
         summary.get("withdrawals"), summary.get("closing")),
    )


def insert_splitwise_expense(conn: sqlite3.Connection, exp) -> int:
    cur = conn.execute(
        "INSERT INTO splitwise_expenses "
        "(source_file, group_name, date, description, sw_category, total_cost, "
        "user_share, counterparties) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (exp.source_file, exp.group_name, exp.date, exp.description,
         exp.sw_category, exp.total_cost, exp.user_share, exp.counterparties),
    )
    return cur.lastrowid


def insert_splitwise_payment(conn: sqlite3.Connection, pmt) -> int:
    cur = conn.execute(
        "INSERT INTO splitwise_payments "
        "(source_file, group_name, date, from_person, to_person, amount) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (pmt.source_file, pmt.group_name, pmt.date,
         pmt.from_person, pmt.to_person, pmt.amount),
    )
    return cur.lastrowid
