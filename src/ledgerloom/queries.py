"""Read-only analysis functions for financial data."""

import sqlite3
from datetime import date

from ledgerloom.config import load_user_config


def _default_since(conn: sqlite3.Connection) -> str:
    """Compute the default `since` date at call time.

    1. SELECT MIN(date) FROM transactions — use that if non-null.
    2. Otherwise fall back to fiscal_year_start_month from user config:
       f"{Y:04d}-{M:02d}-01" where M = fiscal_year_start_month and Y is the
       current calendar year if today.month >= M, else today.year - 1.
    """
    row = conn.execute("SELECT MIN(date) FROM transactions").fetchone()
    if row and row[0]:
        return row[0]
    cfg = load_user_config()
    today = date.today()
    year = today.year if today.month >= cfg.fiscal_year_start_month else today.year - 1
    return f"{year:04d}-{cfg.fiscal_year_start_month:02d}-01"


def monthly_budget(conn: sqlite3.Connection,
                   since: str | None = None) -> list[dict]:
    if since is None:
        since = _default_since(conn)
    rows = conn.execute("""
        SELECT strftime('%Y-%m', date) AS month,
               ROUND(SUM(CASE WHEN category = 'Income' THEN amount ELSE 0 END), 2) AS income,
               ROUND(SUM(CASE WHEN amount < 0 AND category NOT IN ('Transfer')
                         THEN ABS(amount) ELSE 0 END), 2) AS spent,
               ROUND(SUM(CASE WHEN category = 'Transfer' AND subcategory = 'Remittance'
                         THEN ABS(amount) ELSE 0 END), 2) AS remittance,
               ROUND(SUM(CASE WHEN category = 'Transfer' AND subcategory = 'e-Transfer Out'
                         THEN ABS(amount) ELSE 0 END), 2) AS etransfers_out
        FROM transactions WHERE date >= ?
        GROUP BY month ORDER BY month
    """, (since,)).fetchall()
    cols = ["month", "income", "spent", "remittance", "etransfers_out"]
    return [dict(zip(cols, r)) for r in rows]


def spending_by_category(conn: sqlite3.Connection,
                         since: str | None = None) -> list[dict]:
    if since is None:
        since = _default_since(conn)
    rows = conn.execute("""
        SELECT category, ROUND(SUM(ABS(amount)), 2) AS total,
               COUNT(*) AS txn_count
        FROM transactions
        WHERE amount < 0 AND date >= ? AND category NOT IN ('Transfer')
        GROUP BY category ORDER BY total DESC
    """, (since,)).fetchall()
    return [dict(zip(["category", "total", "txn_count"], r)) for r in rows]


def top_merchants(conn: sqlite3.Connection,
                  since: str | None = None,
                  limit: int = 20) -> list[dict]:
    if since is None:
        since = _default_since(conn)
    rows = conn.execute("""
        SELECT merchant, category, COUNT(*) AS visits,
               ROUND(SUM(ABS(amount)), 2) AS total
        FROM transactions
        WHERE amount < 0 AND date >= ? AND merchant IS NOT NULL
              AND category NOT IN ('Transfer')
        GROUP BY merchant ORDER BY total DESC LIMIT ?
    """, (since, limit)).fetchall()
    return [dict(zip(["merchant", "category", "visits", "total"], r)) for r in rows]


def find_subscriptions(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT merchant,
               COUNT(DISTINCT strftime('%Y-%m', date)) AS months_seen,
               ROUND(AVG(ABS(amount)), 2) AS avg_amount,
               ROUND(SUM(ABS(amount)), 2) AS total
        FROM transactions
        WHERE amount < 0 AND merchant IS NOT NULL
        GROUP BY merchant
        HAVING months_seen >= 2
        ORDER BY months_seen DESC, total DESC
    """).fetchall()
    return [dict(zip(["merchant", "months_seen", "avg_amount", "total"], r)) for r in rows]


def verify_against_summaries(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT a.name, s.period_start, s.period_end,
               ss.total_deposits, ss.total_withdrawals,
               ROUND(COALESCE(SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END), 0), 2) AS parsed_deps,
               ROUND(COALESCE(SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END), 0), 2) AS parsed_withs
        FROM statement_summary ss
        JOIN sources s ON ss.source_id = s.id
        JOIN accounts a ON s.account_id = a.id
        LEFT JOIN transactions t ON t.source_id = s.id
        GROUP BY ss.id
        ORDER BY a.name, s.period_start
    """).fetchall()
    results = []
    for r in rows:
        name, pstart, pend, stmt_dep, stmt_with, parsed_dep, parsed_with = r
        dep_diff = abs(parsed_dep - stmt_dep) if stmt_dep else 0
        with_diff = abs(parsed_with - stmt_with) if stmt_with else 0
        results.append({
            "account": name, "period": f"{pstart} to {pend}",
            "stmt_deposits": stmt_dep, "stmt_withdrawals": stmt_with,
            "parsed_deposits": parsed_dep, "parsed_withdrawals": parsed_with,
            "status": "OK" if dep_diff < 1 and with_diff < 1
                      else f"DIFF dep={dep_diff:.2f} with={with_diff:.2f}",
        })
    return results
