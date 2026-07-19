"""Tests for ledgerloom.normalize: extract_merchant and normalize_merchant."""

import pytest

from ledgerloom.normalize import extract_merchant, normalize_merchant

pytestmark = pytest.mark.usefixtures("default_config")


class TestExtractMerchant:
    def test_strips_contactless_interac_prefix(self):
        result = extract_merchant("Contactless Interac purchase - XXXX TIM HORTONS #28")
        assert result == "TIM HORTONS #28"

    def test_strips_visa_debit_prefix(self):
        result = extract_merchant("Visa Debit purchase - XXXX MCDONALD'S #137")
        assert result == "MCDONALD'S #137"

    def test_strips_misc_payment_prefix(self):
        result = extract_merchant("Misc Payment PAYPAL")
        assert result == "PAYPAL"

    def test_strips_online_banking_payment_prefix(self):
        result = extract_merchant("Online Banking payment - XXXX TELCO")
        assert result == "TELCO"

    def test_returns_raw_text_unchanged_when_no_known_prefix(self):
        result = extract_merchant("Funds transfer credit WAL-MART CANADA")
        assert result == "Funds transfer credit WAL-MART CANADA"

    def test_returns_none_for_empty_string(self):
        result = extract_merchant("")
        assert result is None

    def test_strips_scotia_pos_purchase_and_apos_stacked_prefixes(self):
        result = extract_merchant("pos purchase Apos Marche Tharsini Montr")
        assert "Marche Tharsini" in result
        assert "Apos" not in result
        assert "pos purchase" not in result.lower()

    def test_strips_scotia_withdrawal_prefix(self):
        result = extract_merchant("withdrawal Free Interac E-Transfer")
        assert result == "Free Interac E-Transfer"

    def test_strips_scotia_payroll_deposit_prefix(self):
        result = extract_merchant("payroll deposit People Center")
        assert result == "People Center"

    def test_strips_rbc_csv_visa_debit_purchase_with_numeric_id(self):
        result = extract_merchant("VISA DEBIT PURCHASE - 2831 CHRONO-RECHARGE")
        assert result == "CHRONO-RECHARGE"

    def test_strips_rbc_csv_misc_payment(self):
        result = extract_merchant("MISC PAYMENT PAYPAL")
        assert result == "PAYPAL"


class TestNormalizeMerchant:
    def test_maps_tim_hortons_with_location_number(self):
        result = normalize_merchant("TIM HORTONS #28")
        assert result == "Tim Hortons"

    def test_maps_tim_hortons_different_location(self):
        result = normalize_merchant("TIM HORTONS #30")
        assert result == "Tim Hortons"

    def test_maps_mcdonalds_with_location_number(self):
        result = normalize_merchant("MCDONALD'S #137")
        assert result == "McDonald's"

    def test_maps_walmart_store_variant(self):
        result = normalize_merchant("WALMART STORE #456")
        assert result == "Walmart"

    def test_maps_uber_canada_abbreviated(self):
        result = normalize_merchant("UBER CANADA/UBE")
        assert result == "Uber"

    def test_returns_original_string_when_no_match(self):
        result = normalize_merchant("SOME UNKNOWN STORE")
        assert result == "SOME UNKNOWN STORE"

    def test_returns_none_for_none_input(self):
        result = normalize_merchant(None)
        assert result is None


def test_empty_merchant_map_returns_stripped_input(empty_rules_config):
    assert normalize_merchant("TIM HORTONS #28") == "TIM HORTONS #28"
    assert normalize_merchant("  SOME STORE  ") == "SOME STORE"
    assert normalize_merchant(None) is None
