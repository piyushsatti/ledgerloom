"""Tests for ledgerloom.parsers.amex_csv: parse_amex_csv."""

from ledgerloom.parsers.amex_csv import parse_amex_csv

_HEADER = (
    "Date,Date Processed,Description,Amount,Foreign Spend Amount,Commission,"
    "Exchange Rate,Additional Information,Merchant,Address,City / Province,"
    "Postal Code,Country,Reference\n"
)

# Representative rows from a real AMEX activity.csv export, including the
# embedded-newline City / Province edge case and a negative-amount (credit /
# payment) row that must be negated to a positive amount.
_ROWS = (
    "18 Jul 2026,18 Jul 2026,UBER TRIP               TORONTO,21.93,,,,,"
    "UBER TRIP               TORONTO,121 Bloor Street East 16th floor,"
    "\"TORONTO\nON\",M4W 1A9,CANADA,'AT261990006000010444354'\n"
    "16 Jul 2026,17 Jul 2026,OMNIVORE ST-LAURENT 001 MONTREAL,26.00,,,,,"
    "OMNIVORE ST-LAURENT 001 MONTREAL,4306 BLVD SAINT-LAURENT BLVD,"
    "\"MONTREAL\nQC\",H2W 1Z8,CANADA,'AT261980005000010347575'\n"
    "15 Jul 2026,15 Jul 2026,APPLE.COM/BILL          TORONTO,14.70,,,,,"
    "APPLE.COM/BILL          TORONTO,120 BREMNER BLVD,"
    "\"TORONTO\nON\",M5J 0A8,CANADA,'AT261960006000010384660'\n"
    "13 Jul 2026,13 Jul 2026,ABC*4261-ANYTIME FITNES MONTREAL,34.44,,,,,"
    'ABC*4261-ANYTIME FITNES MONTREAL,"FIRST CANADIAN PL\n'
    '100 KING ST W B-2 LEVEL","TORONTO\nON",M5X 1A3,CANADA,\'AT261940006000010349408\'\n'
    "27 Jun 2026,27 Jun 2026,PAYMENT RECEIVED - THANK YOU,-1342.42,,,,,"
    "PAYMENT RECEIVED - THANK YOU,,,,,'AT261780003000010001052'\n"
)


def _write_csv(tmp_path):
    p = tmp_path / "activity.csv"
    p.write_text(_HEADER + _ROWS, encoding="utf-8")
    return p


def test_row_count(tmp_path):
    result = parse_amex_csv(str(_write_csv(tmp_path)))
    assert len(result.transactions) == 5


def test_dates_are_iso(tmp_path):
    result = parse_amex_csv(str(_write_csv(tmp_path)))
    for t in result.transactions:
        assert len(t.date) == 10 and t.date[4] == "-" and t.date[7] == "-"
    assert result.transactions[0].date == "2026-07-18"
    assert result.transactions[-1].date == "2026-06-27"


def test_sign_convention(tmp_path):
    result = parse_amex_csv(str(_write_csv(tmp_path)))
    uber = next(t for t in result.transactions if "UBER TRIP" in t.raw_description)
    assert uber.amount == -21.93

    payment = next(
        t for t in result.transactions if "PAYMENT RECEIVED" in t.raw_description
    )
    assert payment.amount == 1342.42


def test_embedded_newline_field_does_not_break_parsing(tmp_path):
    """Multiline quoted City / Province must not split a row in two."""
    result = parse_amex_csv(str(_write_csv(tmp_path)))
    assert len(result.transactions) == 5
    fitness = next(
        t for t in result.transactions if "ANYTIME FITNES" in t.raw_description
    )
    assert fitness.amount == -34.44


def test_period_tuple(tmp_path):
    result = parse_amex_csv(str(_write_csv(tmp_path)))
    assert result.period == ("2026-06-27", "2026-07-18")


def test_raw_description_populated(tmp_path):
    result = parse_amex_csv(str(_write_csv(tmp_path)))
    for t in result.transactions:
        assert t.raw_description


def test_summary_is_empty(tmp_path):
    result = parse_amex_csv(str(_write_csv(tmp_path)))
    assert result.summary == {}


def test_no_rows_returns_empty_result(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text(_HEADER, encoding="utf-8")
    result = parse_amex_csv(str(p))
    assert result.transactions == []
    assert result.period is None
