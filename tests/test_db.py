"""Tests for ledgerloom.db — schema creation, seeding, and insert helpers."""

import sqlite3

import pytest
from ledgerloom.db import (
    create_db,
    get_account_id,
    insert_source,
    insert_transactions,
    source_exists,
)


# ---------------------------------------------------------------------------
# create_db
# ---------------------------------------------------------------------------

def test_create_db_creates_all_tables(db_conn):
    tables = {
        row[0]
        for row in db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    expected = {
        "accounts",
        "sources",
        "transactions",
        "splitwise_expenses",
        "splitwise_payments",
        "statement_summary",
    }
    assert expected.issubset(tables)


def test_create_db_seeds_five_accounts(db_conn):
    count = db_conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    assert count == 5


# ---------------------------------------------------------------------------
# insert_source
# ---------------------------------------------------------------------------

def test_insert_source_returns_integer_id(db_conn):
    account_id = get_account_id(db_conn, "0001")
    source_id = insert_source(db_conn, "/fake/path.pdf", "abc123hash", account_id, "2026-01-01", "2026-01-31")
    assert isinstance(source_id, int)
    assert source_id > 0


# ---------------------------------------------------------------------------
# source_exists
# ---------------------------------------------------------------------------

def test_source_exists_true_for_known_hash(db_conn):
    account_id = get_account_id(db_conn, "0001")
    insert_source(db_conn, "/fake/path.pdf", "knownhash", account_id, None, None)
    db_conn.commit()
    assert source_exists(db_conn, "knownhash") is True


def test_source_exists_false_for_unknown_hash(db_conn):
    assert source_exists(db_conn, "nonexistenthash") is False


# ---------------------------------------------------------------------------
# insert_transactions
# ---------------------------------------------------------------------------

def test_insert_transactions_inserts_correct_row_count(db_conn):
    account_id = get_account_id(db_conn, "0001")
    source_id = insert_source(db_conn, "/fake/path.pdf", "txhash1", account_id, "2026-01-01", "2026-01-31")

    rows = [
        {"date": "2026-01-05", "raw_description": "TIM HORTONS", "amount": -3.50, "merchant": "Tim Hortons", "category": "Food & Drink"},
        {"date": "2026-01-10", "raw_description": "METRO GROCERY", "amount": -67.20, "merchant": "Metro", "category": "Groceries"},
        {"date": "2026-01-15", "raw_description": "PAYROLL DEPOSIT", "amount": 2500.00, "merchant": None, "category": "Income"},
    ]
    count = insert_transactions(db_conn, source_id, account_id, rows)
    db_conn.commit()

    assert count == 3
    stored = db_conn.execute("SELECT COUNT(*) FROM transactions WHERE source_id = ?", (source_id,)).fetchone()[0]
    assert stored == 3


# ---------------------------------------------------------------------------
# get_account_id
# ---------------------------------------------------------------------------

def test_get_account_id_returns_correct_id_for_0001(db_conn):
    account_id = get_account_id(db_conn, "0001")
    row = db_conn.execute(
        "SELECT account_suffix FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()
    assert row is not None
    assert row[0] == "0001"


def test_get_account_id_raises_for_unknown_suffix(db_conn):
    with pytest.raises(ValueError, match="No account with suffix"):
        get_account_id(db_conn, "9999")


