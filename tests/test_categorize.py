"""Tests for ledgerloom.categorize: categorize."""

import pytest

from ledgerloom.categorize import categorize

pytestmark = pytest.mark.usefixtures("default_config")


class TestCategorize:
    def test_tim_hortons_is_coffee_tea(self):
        assert categorize("Tim Hortons", "anything") == ("Coffee/Tea", "Tim Hortons")

    def test_mcdonalds_is_fast_food(self):
        assert categorize("McDonald's", "anything") == ("Fast Food", "McDonald's")

    def test_walmart_is_groceries(self):
        assert categorize("Walmart", "anything") == ("Groceries", "Walmart")

    def test_winners_is_shopping(self):
        assert categorize("Winners", "anything") == ("Shopping", "Winners")

    def test_affirm_is_bills_bnpl(self):
        assert categorize("Affirm", "anything") == ("Bills", "BNPL")

    def test_falls_back_to_raw_description_for_salary(self):
        assert categorize(None, "Payroll Deposit WAL-MART CANADA") == ("Income", "Salary")

    def test_falls_back_to_raw_description_for_etransfer_out(self):
        assert categorize(None, "e-Transfer sent John Doe") == ("Transfer", "e-Transfer Out")

    def test_falls_back_to_raw_description_for_remittance(self):
        assert categorize(None, "International remittance 2WI790920437580") == ("Transfer", "Remittance")

    def test_falls_back_to_raw_description_for_bank_fee(self):
        assert categorize(None, "Monthly fee") == ("Bills", "Bank Fee")

    def test_uncategorized_when_no_match(self):
        assert categorize(None, "some random unknown thing") == ("Uncategorized", "")

    def test_local_restaurant_a_is_restaurant(self):
        assert categorize("Local Restaurant A", "anything") == ("Restaurant", "Local Restaurant A")


def test_empty_rules_returns_uncategorized(empty_rules_config):
    assert categorize("Tim Hortons", "Tim Hortons purchase") == ("Uncategorized", "")
    assert categorize(None, "Payroll Deposit") == ("Uncategorized", "")
    assert categorize(None, "some random string") == ("Uncategorized", "")
