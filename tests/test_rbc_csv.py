"""Tests for ledgerloom.parsers.rbc_csv: parse_rbc_csv."""

from ledgerloom.parsers.rbc_csv import parse_rbc_csv

# Representative rows from a real RBC online-banking CSV export (with a
# leading BOM on the header, as the real file has), including a Description 2
# edge case (empty here — real exports leave it blank for most rows) and a
# deposit row asserting the positive sign convention.
_CSV_TEXT = (
    "﻿Account Type,Account Number,Transaction Date,Cheque Number,"
    "Description 1,Description 2,CAD$,USD$\n"
    "Chequing,05981-5087788,7/7/2026,,E-TRANSFER SENT NEHA 5302 2SGB96,,-19.09,\n"
    "Chequing,05981-5087788,7/7/2026,,MISC PAYMENT PAYPAL,,-9.19,\n"
    "Chequing,05981-5087788,7/10/2026,,PAYROLL DEPOSIT PEOPLE CENTER,,1000,\n"
    "Chequing,05981-5087788,7/14/2026,,VISA DEBIT PURCHASE - 2831 CHRONO-RECHARGE,,-33.25,\n"
    "Chequing,05981-5087788,7/16/2026,,VISA DEBIT PURCHASE - 4261 AFFIRM CANADA,,-48.08,\n"
    "Chequing,05981-5087788,7/17/2026,,VISA DEBIT PURCHASE - 1786 AFFIRM CANADA,,-94.92,\n"
)


def _write_csv(tmp_path):
    p = tmp_path / "download-transactions.csv"
    p.write_bytes(_CSV_TEXT.encode("utf-8"))
    return p


def test_row_count(tmp_path):
    result = parse_rbc_csv(str(_write_csv(tmp_path)))
    assert len(result.transactions) == 6


def test_dates_are_iso(tmp_path):
    result = parse_rbc_csv(str(_write_csv(tmp_path)))
    for t in result.transactions:
        assert len(t.date) == 10 and t.date[4] == "-" and t.date[7] == "-"
    assert result.transactions[0].date == "2026-07-07"
    assert result.transactions[2].date == "2026-07-10"


def test_sign_convention_used_as_is(tmp_path):
    """CAD$ is already signed — no negation should be applied."""
    result = parse_rbc_csv(str(_write_csv(tmp_path)))
    etransfer = next(
        t for t in result.transactions if "E-TRANSFER SENT" in t.raw_description
    )
    assert etransfer.amount == -19.09

    payroll = next(
        t for t in result.transactions if "PAYROLL DEPOSIT" in t.raw_description
    )
    assert payroll.amount == 1000.0


def test_bom_is_stripped_from_header(tmp_path):
    """The BOM on the first header field must not leak into fieldnames/data."""
    result = parse_rbc_csv(str(_write_csv(tmp_path)))
    assert len(result.transactions) == 6  # would be 0 if the BOM broke DictReader


def test_period_tuple(tmp_path):
    result = parse_rbc_csv(str(_write_csv(tmp_path)))
    assert result.period == ("2026-07-07", "2026-07-17")


def test_raw_description_populated(tmp_path):
    result = parse_rbc_csv(str(_write_csv(tmp_path)))
    for t in result.transactions:
        assert t.raw_description


def test_description_2_joined_when_present(tmp_path):
    csv_text = (
        "﻿Account Type,Account Number,Transaction Date,Cheque Number,"
        "Description 1,Description 2,CAD$,USD$\n"
        "Chequing,05981-5087788,7/7/2026,,MISC PAYMENT,PAYPAL EXTRA,-9.19,\n"
    )
    p = tmp_path / "with_desc2.csv"
    p.write_bytes(csv_text.encode("utf-8"))
    result = parse_rbc_csv(str(p))
    assert result.transactions[0].raw_description == "MISC PAYMENT  PAYPAL EXTRA"


def test_summary_is_empty(tmp_path):
    result = parse_rbc_csv(str(_write_csv(tmp_path)))
    assert result.summary == {}


def test_no_rows_returns_empty_result(tmp_path):
    header_only = (
        "﻿Account Type,Account Number,Transaction Date,Cheque Number,"
        "Description 1,Description 2,CAD$,USD$\n"
    )
    p = tmp_path / "empty.csv"
    p.write_bytes(header_only.encode("utf-8"))
    result = parse_rbc_csv(str(p))
    assert result.transactions == []
    assert result.period is None
