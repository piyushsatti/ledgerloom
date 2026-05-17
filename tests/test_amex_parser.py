"""Tests for ledgerloom.parsers.amex: parse_amex_statement."""

import pytest

from ledgerloom.parsers.amex import parse_amex_statement

# ---------------------------------------------------------------------------
# Synthetic Amex Cobalt statement text
#
# Transaction line format:
#   <txn_date>  <post_date>  <MERCHANT NAME CITY>  <AMOUNT>
# e.g. "Apr 2  Apr 3  LOBLAWS TORONTO ON  38.47"
# ---------------------------------------------------------------------------

SYNTHETIC_AMEX_TEXT = """\
American Express Cobalt Card

Opening Date  Closing Date
Mar 21, 2026  Apr 20, 2026

Account Summary

Payments                                            $0.00
Purchases                                        $182.43
Fees                                              $15.99
New Balance                                      $198.42

Transactions

Mar 22  Mar 23  LOBLAWS #1042 TORONTO ON                           38.47
Mar 25  Mar 26  STARBUCKS STORE 00123 TORONTO                       6.75
Apr 5   Apr 6   SPOTIFY CANADA TORONTO ON                          11.99
Apr 12  Apr 13  UBER CANADA/UBEREATS TORONTO                      125.22

Other Account Transactions

MEMBERSHIP FEE                                                      15.99

"""


class TestParseAmexStatement:

    def setup_method(self):
        self.result = parse_amex_statement(SYNTHETIC_AMEX_TEXT)

    # ------------------------------------------------------------------
    # Transaction count (4 purchases + 1 membership fee)
    # ------------------------------------------------------------------

    def test_parses_correct_number_of_transactions(self):
        assert len(self.result.transactions) == 5

    # ------------------------------------------------------------------
    # All amounts are negative (money out)
    # ------------------------------------------------------------------

    def test_all_amounts_are_negative(self):
        for tx in self.result.transactions:
            assert tx.amount < 0, (
                f"Expected negative amount for '{tx.raw_description}', got {tx.amount}"
            )

    def test_loblaws_amount(self):
        tx = next(t for t in self.result.transactions if "LOBLAWS" in t.raw_description)
        assert tx.amount == pytest.approx(-38.47)

    def test_spotify_amount(self):
        tx = next(t for t in self.result.transactions if "SPOTIFY" in t.raw_description)
        assert tx.amount == pytest.approx(-11.99)

    def test_uber_amount(self):
        tx = next(t for t in self.result.transactions if "UBER" in t.raw_description)
        assert tx.amount == pytest.approx(-125.22)

    # ------------------------------------------------------------------
    # Period
    # ------------------------------------------------------------------

    def test_period_start(self):
        assert self.result.period is not None
        assert self.result.period[0] == "2026-03-21"

    def test_period_end(self):
        assert self.result.period is not None
        assert self.result.period[1] == "2026-04-20"

    # ------------------------------------------------------------------
    # Membership fee is included
    # ------------------------------------------------------------------

    def test_membership_fee_present(self):
        fee_txns = [t for t in self.result.transactions if t.raw_description == "MEMBERSHIP FEE"]
        assert len(fee_txns) == 1

    def test_membership_fee_amount(self):
        fee_txn = next(t for t in self.result.transactions if t.raw_description == "MEMBERSHIP FEE")
        assert fee_txn.amount == pytest.approx(-15.99)

    def test_membership_fee_date_matches_period_end(self):
        fee_txn = next(t for t in self.result.transactions if t.raw_description == "MEMBERSHIP FEE")
        assert fee_txn.date == "2026-04-20"

    # ------------------------------------------------------------------
    # tx_method is credit_card for all transactions
    # ------------------------------------------------------------------

    def test_all_tx_method_is_credit_card(self):
        for tx in self.result.transactions:
            assert tx.tx_method == "credit_card", (
                f"Expected 'credit_card' for '{tx.raw_description}', got '{tx.tx_method}'"
            )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def test_summary_purchases(self):
        assert self.result.summary.get("purchases") == pytest.approx(182.43)

    def test_summary_fees(self):
        assert self.result.summary.get("fees") == pytest.approx(15.99)

    def test_summary_new_balance(self):
        assert self.result.summary.get("new_balance") == pytest.approx(198.42)

    # ------------------------------------------------------------------
    # Dates are in YYYY-MM-DD format using the closing year
    # ------------------------------------------------------------------

    def test_loblaws_date(self):
        tx = next(t for t in self.result.transactions if "LOBLAWS" in t.raw_description)
        assert tx.date == "2026-03-22"

    def test_april_transaction_date(self):
        tx = next(t for t in self.result.transactions if "SPOTIFY" in t.raw_description)
        assert tx.date == "2026-04-05"
