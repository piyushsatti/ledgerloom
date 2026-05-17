"""Tests for ledgerloom.queries — analysis functions against a seeded database."""

import pytest
from ledgerloom.db import get_account_id, insert_source, insert_transactions
from ledgerloom.queries import (
    find_subscriptions,
    monthly_budget,
    spending_by_category,
    top_merchants,
)

pytestmark = pytest.mark.usefixtures("default_config")


# ---------------------------------------------------------------------------
# Fixture: seeded database with 10 known transactions across 2 months
# ---------------------------------------------------------------------------

@pytest.fixture
def seeded_conn(db_conn):
    """
    db_conn with a predictable set of transactions:

    2026-02-01  Payroll Deposit     +3000.00  Income
    2026-02-05  Tim Hortons          -4.50    Food & Drink   (coffee)
    2026-02-10  Tim Hortons          -4.75    Food & Drink   (coffee)
    2026-02-12  Metro                -82.30   Groceries
    2026-02-15  Netflix              -17.99   Subscriptions
    2026-02-20  e-Transfer Out      -200.00   Transfer       subcategory=e-Transfer Out
    2026-03-01  Salary               +3000.00 Income
    2026-03-06  Starbucks            -6.10    Food & Drink   (coffee/tea)
    2026-03-14  Superstore           -95.40   Groceries
    2026-03-18  Netflix              -17.99   Subscriptions
    """
    account_id = get_account_id(db_conn, "0001")
    source_id = insert_source(
        db_conn, "/fake/seeded.pdf", "seededhash001", account_id,
        "2026-02-01", "2026-03-31"
    )

    rows = [
        # --- February ---
        {
            "date": "2026-02-01",
            "raw_description": "PAYROLL DEPOSIT",
            "amount": 3000.00,
            "merchant": None,
            "category": "Income",
            "subcategory": None,
        },
        {
            "date": "2026-02-05",
            "raw_description": "TIM HORTONS #123",
            "amount": -4.50,
            "merchant": "Tim Hortons",
            "category": "Food & Drink",
            "subcategory": "Coffee & Tea",
        },
        {
            "date": "2026-02-10",
            "raw_description": "TIM HORTONS #456",
            "amount": -4.75,
            "merchant": "Tim Hortons",
            "category": "Food & Drink",
            "subcategory": "Coffee & Tea",
        },
        {
            "date": "2026-02-12",
            "raw_description": "METRO GROCERY",
            "amount": -82.30,
            "merchant": "Metro",
            "category": "Groceries",
            "subcategory": None,
        },
        {
            "date": "2026-02-15",
            "raw_description": "NETFLIX.COM",
            "amount": -17.99,
            "merchant": "Netflix",
            "category": "Subscriptions",
            "subcategory": None,
        },
        {
            "date": "2026-02-20",
            "raw_description": "E-TRANSFER OUT",
            "amount": -200.00,
            "merchant": None,
            "category": "Transfer",
            "subcategory": "e-Transfer Out",
        },
        # --- March ---
        {
            "date": "2026-03-01",
            "raw_description": "SALARY DEPOSIT",
            "amount": 3000.00,
            "merchant": None,
            "category": "Income",
            "subcategory": None,
        },
        {
            "date": "2026-03-06",
            "raw_description": "STARBUCKS #789",
            "amount": -6.10,
            "merchant": "Starbucks",
            "category": "Food & Drink",
            "subcategory": "Coffee & Tea",
        },
        {
            "date": "2026-03-14",
            "raw_description": "SUPERSTORE",
            "amount": -95.40,
            "merchant": "Superstore",
            "category": "Groceries",
            "subcategory": None,
        },
        {
            "date": "2026-03-18",
            "raw_description": "NETFLIX.COM",
            "amount": -17.99,
            "merchant": "Netflix",
            "category": "Subscriptions",
            "subcategory": None,
        },
    ]

    insert_transactions(db_conn, source_id, account_id, rows)
    db_conn.commit()
    return db_conn


# ---------------------------------------------------------------------------
# monthly_budget
# ---------------------------------------------------------------------------

def test_monthly_budget_returns_correct_income_and_spent(seeded_conn):
    results = monthly_budget(seeded_conn, since="2026-02-01")
    assert len(results) == 2

    feb = next(r for r in results if r["month"] == "2026-02")
    mar = next(r for r in results if r["month"] == "2026-03")

    # Income
    assert feb["income"] == 3000.00
    assert mar["income"] == 3000.00

    # Spent excludes Transfer category
    # Feb: 4.50 + 4.75 + 82.30 + 17.99 = 109.54
    assert feb["spent"] == pytest.approx(109.54, abs=0.01)
    # Mar: 6.10 + 95.40 + 17.99 = 119.49
    assert mar["spent"] == pytest.approx(119.49, abs=0.01)

    # e-Transfer Out tracked separately
    assert feb["etransfers_out"] == pytest.approx(200.00, abs=0.01)
    assert mar["etransfers_out"] == pytest.approx(0.00, abs=0.01)


# ---------------------------------------------------------------------------
# spending_by_category
# ---------------------------------------------------------------------------

def test_spending_by_category_returns_correct_totals(seeded_conn):
    results = spending_by_category(seeded_conn, since="2026-02-01")

    # Transfer excluded; Income excluded (positive amounts filtered by amount < 0)
    category_totals = {r["category"]: r["total"] for r in results}

    # Food & Drink: 4.50 + 4.75 + 6.10 = 15.35
    assert "Food & Drink" in category_totals
    assert category_totals["Food & Drink"] == pytest.approx(15.35, abs=0.01)

    # Groceries: 82.30 + 95.40 = 177.70
    assert "Groceries" in category_totals
    assert category_totals["Groceries"] == pytest.approx(177.70, abs=0.01)

    # Subscriptions: 17.99 + 17.99 = 35.98
    assert "Subscriptions" in category_totals
    assert category_totals["Subscriptions"] == pytest.approx(35.98, abs=0.01)

    # Transfer must NOT appear
    assert "Transfer" not in category_totals


# ---------------------------------------------------------------------------
# top_merchants
# ---------------------------------------------------------------------------

def test_top_merchants_sorted_by_total_spend(seeded_conn):
    results = top_merchants(seeded_conn, since="2026-02-01", limit=10)

    # Only spending transactions with a merchant and category != Transfer
    merchant_names = [r["merchant"] for r in results]
    assert "Superstore" in merchant_names
    assert "Metro" in merchant_names
    assert "Tim Hortons" in merchant_names
    assert "Netflix" in merchant_names
    assert "Starbucks" in merchant_names

    # Superstore (95.40) > Metro (82.30) > Netflix (35.98) > Tim Hortons (9.25) > Starbucks (6.10)
    totals = [r["total"] for r in results]
    assert totals == sorted(totals, reverse=True)

    # Merchants with no merchant field (Income / Transfer) must not appear
    assert None not in merchant_names


def test_top_merchants_visit_counts(seeded_conn):
    results = top_merchants(seeded_conn, since="2026-02-01", limit=10)
    by_merchant = {r["merchant"]: r for r in results}

    assert by_merchant["Tim Hortons"]["visits"] == 2
    assert by_merchant["Netflix"]["visits"] == 2
    assert by_merchant["Metro"]["visits"] == 1


# ---------------------------------------------------------------------------
# find_subscriptions
# ---------------------------------------------------------------------------

def test_find_subscriptions_finds_multi_month_merchants(seeded_conn):
    results = find_subscriptions(seeded_conn)
    merchants = {r["merchant"] for r in results}

    # Netflix appears in both February and March
    assert "Netflix" in merchants

    # Verify months_seen >= 2 invariant
    for r in results:
        assert r["months_seen"] >= 2


def test_find_subscriptions_excludes_single_month_merchants(seeded_conn):
    results = find_subscriptions(seeded_conn)
    merchants = {r["merchant"] for r in results}

    # These appear in only one month
    assert "Metro" not in merchants
    assert "Superstore" not in merchants
    assert "Starbucks" not in merchants


def test_find_subscriptions_avg_and_total_for_netflix(seeded_conn):
    results = find_subscriptions(seeded_conn)
    netflix = next((r for r in results if r["merchant"] == "Netflix"), None)
    assert netflix is not None
    assert netflix["months_seen"] == 2
    assert netflix["avg_amount"] == pytest.approx(17.99, abs=0.01)
    assert netflix["total"] == pytest.approx(35.98, abs=0.01)


# ---------------------------------------------------------------------------
# _default_since (P2.T5)
# ---------------------------------------------------------------------------

def test_monthly_budget_defaults_since_to_earliest_tx_date(seeded_conn):
    """When since=None, monthly_budget uses MIN(date) from transactions."""
    # seeded_conn has transactions starting at 2026-02-01
    results_explicit = monthly_budget(seeded_conn, since="2026-02-01")
    results_default = monthly_budget(seeded_conn)
    assert results_explicit == results_default
    assert len(results_default) == 2
