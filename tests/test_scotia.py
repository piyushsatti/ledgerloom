"""Tests for ledgerloom.parsers.scotia: parse_scotia."""

from ledgerloom.parsers.scotia import parse_scotia

# Representative rows from a real Scotiabank CSV export, including the
# Filter-only-on-first-row edge case, a deposit (positive amount), a
# withdrawal, and a payroll deposit that should map tx_method to "deposit".
_CSV_TEXT = (
    "﻿Filter,Date,Description,Sub-description,Type of Transaction,Amount,Balance\n"
    '"Current statement period","2026-07-15","pos purchase",'
    '"Apos Marche Tharsini     Montr ","Debit","-17.72","2056.84"\n'
    '"","2026-07-13","deposit","Free Interac E-Transfer ","Credit","50.00","2106.45"\n'
    '"","2026-07-10","payroll deposit","People Center ","Credit","909.81","2056.45"\n'
    '"","2026-07-07","withdrawal","Free Interac E-Transfer ","Debit","-15.80","548.67"\n'
    '"","2026-06-29","bill payment","Rogers Wireless Pre-Auth Dr ","Debit","-52.36","618.59"\n'
)


def _write_csv(tmp_path):
    p = tmp_path / "scotia.csv"
    p.write_bytes(_CSV_TEXT.encode("utf-8"))
    return p


def test_row_count(tmp_path):
    result = parse_scotia(str(_write_csv(tmp_path)))
    assert len(result.transactions) == 5


def test_dates_are_iso_already(tmp_path):
    result = parse_scotia(str(_write_csv(tmp_path)))
    assert result.transactions[0].date == "2026-07-15"
    for t in result.transactions:
        assert len(t.date) == 10 and t.date[4] == "-" and t.date[7] == "-"


def test_sign_convention_used_as_is(tmp_path):
    result = parse_scotia(str(_write_csv(tmp_path)))
    pos = next(t for t in result.transactions if "pos purchase" in t.raw_description)
    assert pos.amount == -17.72

    deposit = next(
        t for t in result.transactions if t.raw_description.startswith("deposit")
    )
    assert deposit.amount == 50.00


def test_balance_captured(tmp_path):
    result = parse_scotia(str(_write_csv(tmp_path)))
    pos = next(t for t in result.transactions if "pos purchase" in t.raw_description)
    assert pos.balance == 2056.84


def test_tx_method_mapping(tmp_path):
    result = parse_scotia(str(_write_csv(tmp_path)))

    pos = next(
        t for t in result.transactions if t.raw_description.startswith("pos purchase")
    )
    assert pos.tx_method == "pos"

    withdrawal = next(
        t for t in result.transactions if t.raw_description.startswith("withdrawal")
    )
    assert withdrawal.tx_method == "withdrawal"

    payroll = next(
        t
        for t in result.transactions
        if t.raw_description.startswith("payroll deposit")
    )
    assert payroll.tx_method == "deposit"


def test_raw_description_combines_description_and_sub_description(tmp_path):
    result = parse_scotia(str(_write_csv(tmp_path)))
    pos = next(t for t in result.transactions if "Marche Tharsini" in t.raw_description)
    # Whitespace runs collapsed to a single space; the "Apos " artifact is
    # kept faithful here — stripping happens in normalize, not the parser.
    assert pos.raw_description == "pos purchase Apos Marche Tharsini Montr"


def test_filter_only_on_first_row_is_ignored(tmp_path):
    """The Filter column is blank on every row but the first — must not break parsing."""
    result = parse_scotia(str(_write_csv(tmp_path)))
    assert len(result.transactions) == 5


def test_period_tuple(tmp_path):
    result = parse_scotia(str(_write_csv(tmp_path)))
    assert result.period == ("2026-06-29", "2026-07-15")


def test_raw_description_populated(tmp_path):
    result = parse_scotia(str(_write_csv(tmp_path)))
    for t in result.transactions:
        assert t.raw_description


def test_summary_is_empty(tmp_path):
    result = parse_scotia(str(_write_csv(tmp_path)))
    assert result.summary == {}


def test_no_rows_returns_empty_result(tmp_path):
    header_only = (
        "﻿Filter,Date,Description,Sub-description,Type of Transaction,Amount,Balance\n"
    )
    p = tmp_path / "empty.csv"
    p.write_bytes(header_only.encode("utf-8"))
    result = parse_scotia(str(p))
    assert result.transactions == []
    assert result.period is None
