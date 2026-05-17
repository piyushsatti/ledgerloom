"""Tests for ledgerloom.parsers.splitwise: parse_splitwise_csv."""

import os
import tempfile

import pytest

from ledgerloom.parsers.splitwise import parse_splitwise_csv

pytestmark = pytest.mark.usefixtures("default_config")

# ---------------------------------------------------------------------------
# Synthetic Splitwise CSV content
#
# Format mirrors a real Splitwise export:
#   - "Note: does not include group expenses" header line
#   - blank line
#   - CSV header row
#   - real expense rows
#   - a payment row ("X paid Y")
#   - a "Settle all balances" row (must be discarded)
# ---------------------------------------------------------------------------

SYNTHETIC_CSV_CONTENT = """\
Note: does not include group expenses

Date,Description,Category,Cost,Currency,Friend A,Test User
2026-01-15,Groceries run,Food,120.00,CAD,-60.00,60.00
2026-02-01,February Rent,Housing,2400.00,CAD,-1200.00,1200.00
2026-02-10,Internet bill,Utilities,60.00,CAD,-30.00,30.00
2026-03-05,Test User paid Friend A,Payment,500.00,CAD,-500.00,500.00
2026-03-06,Settle all balances,Payment,0.00,CAD,0.00,0.00
"""


@pytest.fixture
def csv_file(tmp_path):
    """Write synthetic CSV to a named temp file that mimics a Splitwise export filename."""
    path = tmp_path / "test-user-and-friend-a_2026-01-01_2026-03-31.csv"
    path.write_text(SYNTHETIC_CSV_CONTENT, encoding="utf-8")
    return str(path)


class TestParseSplittwiseCSV:

    def test_returns_tuple_of_two_lists(self, csv_file):
        result = parse_splitwise_csv(csv_file)
        assert isinstance(result, tuple)
        assert len(result) == 2
        expenses, payments = result
        assert isinstance(expenses, list)
        assert isinstance(payments, list)

    # ------------------------------------------------------------------
    # Settlements are excluded from both lists
    # ------------------------------------------------------------------

    def test_settlements_excluded_from_expenses(self, csv_file):
        expenses, _ = parse_splitwise_csv(csv_file)
        descriptions = [e.description for e in expenses]
        assert "Settle all balances" not in descriptions

    def test_settlements_excluded_from_payments(self, csv_file):
        _, payments = parse_splitwise_csv(csv_file)
        descriptions = [p.from_person + " " + p.to_person for p in payments]
        # None of the payment descriptions should reference a settlement row
        for desc in descriptions:
            assert "Settle" not in desc

    # ------------------------------------------------------------------
    # Expense count and content
    # ------------------------------------------------------------------

    def test_correct_number_of_expenses(self, csv_file):
        expenses, _ = parse_splitwise_csv(csv_file)
        # 3 real expenses (Groceries, Rent, Internet); payment row goes to payments
        assert len(expenses) == 3

    def test_groceries_user_share(self, csv_file):
        expenses, _ = parse_splitwise_csv(csv_file)
        grocery = next(e for e in expenses if e.description == "Groceries run")
        assert grocery.user_share == pytest.approx(60.00)

    def test_rent_user_share(self, csv_file):
        expenses, _ = parse_splitwise_csv(csv_file)
        rent = next(e for e in expenses if e.description == "February Rent")
        assert rent.user_share == pytest.approx(1200.00)

    def test_internet_total_cost(self, csv_file):
        expenses, _ = parse_splitwise_csv(csv_file)
        internet = next(e for e in expenses if e.description == "Internet bill")
        assert internet.total_cost == pytest.approx(60.00)

    def test_expenses_have_correct_dates(self, csv_file):
        expenses, _ = parse_splitwise_csv(csv_file)
        dates = {e.description: e.date for e in expenses}
        assert dates["Groceries run"] == "2026-01-15"
        assert dates["February Rent"] == "2026-02-01"

    # ------------------------------------------------------------------
    # Payments
    # ------------------------------------------------------------------

    def test_correct_number_of_payments(self, csv_file):
        _, payments = parse_splitwise_csv(csv_file)
        assert len(payments) == 1

    def test_payment_from_person(self, csv_file):
        _, payments = parse_splitwise_csv(csv_file)
        assert payments[0].from_person == "Test User"

    def test_payment_to_person(self, csv_file):
        _, payments = parse_splitwise_csv(csv_file)
        assert payments[0].to_person == "Friend A"

    def test_payment_amount(self, csv_file):
        _, payments = parse_splitwise_csv(csv_file)
        assert payments[0].amount == pytest.approx(500.00)

    def test_payment_date(self, csv_file):
        _, payments = parse_splitwise_csv(csv_file)
        assert payments[0].date == "2026-03-05"

    # ------------------------------------------------------------------
    # Group name extracted from filename
    # ------------------------------------------------------------------

    def test_group_name_from_filename(self, csv_file):
        expenses, payments = parse_splitwise_csv(csv_file)
        # filename: test-user-and-friend-a_2026... → group "friend a"
        # (slug = "test-user"; long pattern "test-user-and-(.+?)_\d{4}" matches)
        for record in expenses + payments:
            assert record.group_name == "friend a"

    # ------------------------------------------------------------------
    # Source file populated
    # ------------------------------------------------------------------

    def test_source_file_is_basename(self, csv_file):
        expenses, _ = parse_splitwise_csv(csv_file)
        expected_basename = os.path.basename(csv_file)
        for expense in expenses:
            assert expense.source_file == expected_basename


class TestParseSplittwiseCSVPentagonGroup:
    """Verify filename fallback when no slug pattern matches.

    The hardcoded 'pentagon' branch was removed in P2.T1 — filenames that do
    not match the user-slug pattern fall through to the full filename as the
    group name.
    """

    def test_pentagon_group_name_falls_back_to_filename(self, tmp_path):
        path = tmp_path / "pentagon_2026-01-01_2026-03-31.csv"
        path.write_text(SYNTHETIC_CSV_CONTENT, encoding="utf-8")
        expenses, _ = parse_splitwise_csv(str(path))
        # Neither "test-user-and-..." nor "test-and-..." matches the
        # filename, so group_name falls back to the full filename.
        for expense in expenses:
            assert expense.group_name == "pentagon_2026-01-01_2026-03-31.csv"


class TestParseSplittwiseCSVNoPreamble:
    """Verify parsing works when the CSV starts with a Date header (no Note: preamble)."""

    def test_parses_without_preamble(self, tmp_path):
        csv_no_preamble = (
            "Date,Description,Category,Cost,Currency,Friend A,Test User\n"
            "2026-01-20,Coffee,Food,8.00,CAD,-4.00,4.00\n"
        )
        path = tmp_path / "test-user-and-friend-a_2026-01-01.csv"
        path.write_text(csv_no_preamble, encoding="utf-8")
        expenses, payments = parse_splitwise_csv(str(path))
        assert len(expenses) == 1
        assert expenses[0].user_share == pytest.approx(4.00)
        assert len(payments) == 0


class TestParseSplittwiseCSVNonDefaultUser:
    """Verify parsing works with a non-default user (Jane Doe)."""

    JANE_CSV_CONTENT = """\
Note: does not include group expenses

Date,Description,Category,Cost,Currency,Friend A,Jane Doe
2026-04-01,Dinner,Food,80.00,CAD,-40.00,40.00
2026-04-10,Jane Doe paid Friend A,Payment,40.00,CAD,-40.00,40.00
"""

    def test_jane_doe_expenses_and_payments(self, tmp_path, jane_doe_config):
        path = tmp_path / "jane-doe-and-friend-a_2026-04-01_2026-04-30.csv"
        path.write_text(self.JANE_CSV_CONTENT, encoding="utf-8")
        expenses, payments = parse_splitwise_csv(str(path))

        assert len(expenses) == 1
        assert expenses[0].description == "Dinner"
        assert expenses[0].user_share == pytest.approx(40.00)

        assert len(payments) == 1
        assert payments[0].from_person == "Jane Doe"
        assert payments[0].to_person == "Friend A"

    def test_jane_doe_group_name_from_filename(self, tmp_path, jane_doe_config):
        path = tmp_path / "jane-doe-and-friend-a_2026-04-01_2026-04-30.csv"
        path.write_text(self.JANE_CSV_CONTENT, encoding="utf-8")
        expenses, payments = parse_splitwise_csv(str(path))
        # slug = "jane-doe", long pattern "jane-doe-and-(.+?)_\d{4}" matches
        for record in expenses + payments:
            assert record.group_name == "friend a"
