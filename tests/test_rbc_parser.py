"""Tests for ledgerloom.parsers.rbc: parse_rbc_statement."""

import pytest

from ledgerloom.parsers.rbc import parse_rbc_statement

# ---------------------------------------------------------------------------
# Synthetic statement text
#
# Mimics pdftotext -layout output: fixed-width columns where
#   Withdrawals ($) starts around col 55
#   Deposits ($)    starts around col 75
#   Balance ($)     starts around col 95
# ---------------------------------------------------------------------------

SYNTHETIC_RBC_TEXT = """\
RBC Royal Bank

                         From December 19, 2025 to January 21, 2026

Summary of your account

    Your opening balance                                           $2,500.00
    Total deposits                                        +        1,800.00
    Total withdrawals                                     -          950.00
    Your closing balance                                           $3,350.00

RBC Advantage Banking

    Date       Description                         Withdrawals ($)  Deposits ($)  Balance ($)

20 Dec  Contactless Interac purchase - XXXX STARBUC   45.75                     2,454.25

21 Dec  Visa Debit purchase - XXXX METRO GROCERY ST   22.49                     2,431.76

28 Dec  e-Transfer sent - Jane Smith                 110.00                     2,321.76

 3 Jan  Payroll Deposit ACME CORP LTD                          1,800.00         4,121.76

15 Jan  Online Banking transfer to Savings Account   771.76                     3,350.00

"""


class TestParseRbcStatement:

    def setup_method(self):
        self.result = parse_rbc_statement(SYNTHETIC_RBC_TEXT)

    # ------------------------------------------------------------------
    # Transaction count
    # ------------------------------------------------------------------

    def test_parses_correct_number_of_transactions(self):
        assert len(self.result.transactions) == 5

    # ------------------------------------------------------------------
    # Dates — YYYY-MM-DD format
    # ------------------------------------------------------------------

    def test_first_transaction_date(self):
        tx = self.result.transactions[0]
        assert tx.date == "2025-12-20"

    def test_second_transaction_date(self):
        tx = self.result.transactions[1]
        assert tx.date == "2025-12-21"

    def test_january_transaction_date(self):
        # "3 Jan" falls in year_end (2026) because month < 10
        tx = self.result.transactions[3]
        assert tx.date == "2026-01-03"

    def test_all_dates_are_yyyy_mm_dd(self):
        import re
        for tx in self.result.transactions:
            assert re.match(r"\d{4}-\d{2}-\d{2}", tx.date), (
                f"Date '{tx.date}' is not YYYY-MM-DD"
            )

    # ------------------------------------------------------------------
    # Amounts — negative for withdrawals, positive for deposits
    # ------------------------------------------------------------------

    def test_interac_purchase_is_negative(self):
        tx = self.result.transactions[0]
        assert tx.amount == pytest.approx(-45.75)

    def test_visa_debit_purchase_is_negative(self):
        tx = self.result.transactions[1]
        assert tx.amount == pytest.approx(-22.49)

    def test_etransfer_sent_is_negative(self):
        tx = self.result.transactions[2]
        assert tx.amount == pytest.approx(-110.00)

    def test_payroll_deposit_is_positive(self):
        tx = self.result.transactions[3]
        assert tx.amount == pytest.approx(1800.00)

    def test_online_transfer_is_negative(self):
        tx = self.result.transactions[4]
        assert tx.amount == pytest.approx(-771.76)

    # ------------------------------------------------------------------
    # Period
    # ------------------------------------------------------------------

    def test_period_start(self):
        assert self.result.period is not None
        assert self.result.period[0] == "2025-12-19"

    def test_period_end(self):
        assert self.result.period is not None
        assert self.result.period[1] == "2026-01-21"

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def test_summary_opening_balance(self):
        assert self.result.summary.get("opening") == pytest.approx(2500.00)

    def test_summary_closing_balance(self):
        assert self.result.summary.get("closing") == pytest.approx(3350.00)

    def test_summary_total_deposits(self):
        assert self.result.summary.get("deposits") == pytest.approx(1800.00)

    def test_summary_total_withdrawals(self):
        assert self.result.summary.get("withdrawals") == pytest.approx(950.00)

    # ------------------------------------------------------------------
    # tx_method classification
    # ------------------------------------------------------------------

    def test_interac_tx_method(self):
        tx = self.result.transactions[0]
        assert tx.tx_method == "interac"

    def test_visa_debit_tx_method(self):
        tx = self.result.transactions[1]
        assert tx.tx_method == "visa_debit"

    def test_etransfer_tx_method(self):
        tx = self.result.transactions[2]
        assert tx.tx_method == "etransfer"

    def test_payroll_tx_method(self):
        tx = self.result.transactions[3]
        assert tx.tx_method == "payroll"

    def test_online_transfer_tx_method(self):
        tx = self.result.transactions[4]
        assert tx.tx_method == "online"
