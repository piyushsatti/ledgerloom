"""Tests for src/ledgerloom/config.py — verifies C1 contract behaviour.

All tests use tmp_path and the public path= parameter; no real config/ reads
except test_load_categories_happy and test_load_merchants_happy (which are
read-only checks that the shipped .example files conform to the loader schema).
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from ledgerloom.config import (
    CategoryRule,
    ConfigNotFoundError,
    ConfigSchemaError,
    DataSource,
    FinancialGoal,
    FixedObligation,
    UserConfig,
    append_category_rule,
    append_merchant,
    load_categories,
    load_merchants,
    load_user_config,
    reset_config_cache,
    _read_yaml,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]

_MINIMAL_USER_CONFIG = {
    "name": "Test User",
    "currency": "CAD",
    "locale": "en-CA",
    "country": "CA",
    "tax_jurisdiction": "CA-QC",
    "fiscal_year_start_month": 1,
    "monthly_income_after_tax": 3000.0,
}


def _write_user_config(path: Path, data: dict | None = None) -> Path:
    cfg = _MINIMAL_USER_CONFIG.copy() if data is None else data
    path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset the config cache before and after every test."""
    reset_config_cache()
    yield
    reset_config_cache()


# ---------------------------------------------------------------------------
# 1. test_load_user_config_happy
# ---------------------------------------------------------------------------


def test_load_user_config_happy(tmp_path):
    cfg_file = tmp_path / "user_config.yaml"
    data = {
        **_MINIMAL_USER_CONFIG,
        "fixed_obligations": [
            {"name": "Rent", "amount": 1500.0, "cadence": "monthly"}
        ],
        "financial_goals": [
            {"name": "Emergency fund", "target_amount": 10000.0, "target_date": "2026-12-31"}
        ],
        "sources": [
            {"name": "rbc", "kind": "checking", "parser": "rbc", "path": "data/rbc/"}
        ],
    }
    _write_user_config(cfg_file, data)

    cfg = load_user_config(cfg_file)

    assert isinstance(cfg, UserConfig)
    assert cfg.name == "Test User"
    assert cfg.currency == "CAD"
    assert cfg.locale == "en-CA"
    assert cfg.country == "CA"
    assert cfg.tax_jurisdiction == "CA-QC"
    assert cfg.fiscal_year_start_month == 1
    assert cfg.monthly_income_after_tax == 3000.0
    assert len(cfg.fixed_obligations) == 1
    assert cfg.fixed_obligations[0] == FixedObligation("Rent", 1500.0, "monthly")
    assert len(cfg.financial_goals) == 1
    assert cfg.financial_goals[0] == FinancialGoal("Emergency fund", 10000.0, "2026-12-31")
    assert len(cfg.sources) == 1
    assert cfg.sources[0] == DataSource("rbc", "checking", "rbc", "data/rbc/")


# ---------------------------------------------------------------------------
# 2. test_load_user_config_missing_raises
# ---------------------------------------------------------------------------


def test_load_user_config_missing_raises(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(ConfigNotFoundError) as exc_info:
        load_user_config(missing)
    assert "/onboard" in str(exc_info.value) or str(missing) in str(exc_info.value)
    # The explicit-path form should include the path in the message
    assert str(missing) in str(exc_info.value)


# ---------------------------------------------------------------------------
# 3. test_load_user_config_schema_error
# ---------------------------------------------------------------------------


def test_load_user_config_schema_error(tmp_path):
    cfg_file = tmp_path / "user_config.yaml"
    # Missing 'name'
    data = {k: v for k, v in _MINIMAL_USER_CONFIG.items() if k != "name"}
    cfg_file.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ConfigSchemaError) as exc_info:
        load_user_config(cfg_file)
    assert "name" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 4a. test_load_categories_happy
# ---------------------------------------------------------------------------


def test_load_categories_happy():
    """Read-only: shipped .example file must satisfy the loader schema."""
    example = _REPO_ROOT / "config" / "categories.yaml.example"
    assert example.exists(), f"Example file missing: {example}"
    rules = load_categories(example)
    assert isinstance(rules, list)
    assert len(rules) > 0
    assert all(isinstance(r, CategoryRule) for r in rules)
    # Check first rule is well-formed
    first = rules[0]
    assert isinstance(first.category, str) and first.category
    assert isinstance(first.subcategory, str)
    assert isinstance(first.keywords, tuple)


# ---------------------------------------------------------------------------
# 4b. test_load_merchants_happy
# ---------------------------------------------------------------------------


def test_load_merchants_happy():
    """Read-only: shipped .example file (empty merchants: {}) must load cleanly."""
    example = _REPO_ROOT / "config" / "merchants.yaml.example"
    assert example.exists(), f"Example file missing: {example}"
    merchants = load_merchants(example)
    assert isinstance(merchants, dict)
    # .example ships empty
    assert merchants == {}


# ---------------------------------------------------------------------------
# 5. test_loader_cache
# ---------------------------------------------------------------------------


def test_loader_cache(tmp_path):
    """Second call with the same path returns cached value; _read_yaml not called again."""
    cfg_file = tmp_path / "user_config.yaml"
    _write_user_config(cfg_file)

    call_count = 0
    original_read_yaml = _read_yaml

    def counting_read_yaml(path):
        nonlocal call_count
        call_count += 1
        return original_read_yaml(path)

    with patch("ledgerloom.config._read_yaml", side_effect=counting_read_yaml):
        _ = load_user_config(cfg_file)
        _ = load_user_config(cfg_file)

    assert call_count == 1, f"Expected 1 disk read, got {call_count}"


# ---------------------------------------------------------------------------
# 6. test_reset_config_cache
# ---------------------------------------------------------------------------


def test_reset_config_cache(tmp_path):
    """reset_config_cache() forces re-read on next load call."""
    cfg_file = tmp_path / "user_config.yaml"
    _write_user_config(cfg_file)

    call_count = 0
    original_read_yaml = _read_yaml

    def counting_read_yaml(path):
        nonlocal call_count
        call_count += 1
        return original_read_yaml(path)

    with patch("ledgerloom.config._read_yaml", side_effect=counting_read_yaml):
        _ = load_user_config(cfg_file)
        reset_config_cache()
        _ = load_user_config(cfg_file)

    assert call_count == 2, f"Expected 2 disk reads after reset, got {call_count}"


# ---------------------------------------------------------------------------
# 7. test_env_var_redirects_default_path
# ---------------------------------------------------------------------------


def test_env_var_redirects_default_path(tmp_path, monkeypatch):
    """LEDGERLOOM_CONFIG_DIR redirects the default path resolution."""
    cfg_file = tmp_path / "user_config.yaml"
    _write_user_config(cfg_file)

    monkeypatch.setenv("LEDGERLOOM_CONFIG_DIR", str(tmp_path))
    reset_config_cache()

    cfg = load_user_config(path=None)
    assert cfg.name == "Test User"


# ---------------------------------------------------------------------------
# 8. test_yaml_document_order_preserved
# ---------------------------------------------------------------------------


def test_yaml_document_order_preserved(tmp_path):
    """load_categories returns rules in yaml document order (not sorted)."""
    cats_file = tmp_path / "categories.yaml"
    # Non-alphabetical order: Income, Coffee/Tea, Bills
    data = {
        "rules": [
            {"category": "Income",     "subcategory": "Salary",  "keywords": ["Payroll"]},
            {"category": "Coffee/Tea", "subcategory": "Starbucks", "keywords": ["Starbucks"]},
            {"category": "Bills",      "subcategory": "Phone",   "keywords": ["Telco"]},
        ]
    }
    cats_file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    rules = load_categories(cats_file)
    assert [r.category for r in rules] == ["Income", "Coffee/Tea", "Bills"]


# ---------------------------------------------------------------------------
# 9. test_load_categories_missing_raises_config_not_found
# ---------------------------------------------------------------------------


def test_load_categories_missing_raises_config_not_found(tmp_path):
    """Missing categories.yaml raises ConfigNotFoundError with /onboard hint or path."""
    missing = tmp_path / "categories.yaml"
    with pytest.raises(ConfigNotFoundError) as exc_info:
        load_categories(missing)
    msg = str(exc_info.value)
    assert "/onboard" in msg or str(missing) in msg


# ---------------------------------------------------------------------------
# 10. test_writer_invalidates_cache
# ---------------------------------------------------------------------------


def test_writer_invalidates_cache(tmp_path):
    """After a writer runs, the next load returns freshly-written content."""
    from ledgerloom.config import save_user_config

    # --- save_user_config ---
    cfg_file = tmp_path / "user_config.yaml"
    _write_user_config(cfg_file)
    cfg1 = load_user_config(cfg_file)
    assert cfg1.name == "Test User"

    new_cfg = UserConfig(
        name="Updated User",
        currency="USD",
        locale="en-US",
        country="US",
        tax_jurisdiction="US-CA",
        fiscal_year_start_month=4,
        monthly_income_after_tax=5000.0,
        fixed_obligations=(),
        financial_goals=(),
        sources=(),
    )
    save_user_config(new_cfg, cfg_file)
    cfg2 = load_user_config(cfg_file)
    assert cfg2.name == "Updated User"

    # --- append_merchant ---
    merch_file = tmp_path / "merchants.yaml"
    merch_file.write_text(yaml.safe_dump({"merchants": {}}), encoding="utf-8")
    m1 = load_merchants(merch_file)
    assert "TIM HORTONS" not in m1

    append_merchant("TIM HORTONS", "Tim Hortons", merch_file)
    m2 = load_merchants(merch_file)
    assert m2["TIM HORTONS"] == "Tim Hortons"

    # --- append_category_rule ---
    cats_file = tmp_path / "categories.yaml"
    cats_file.write_text(yaml.safe_dump({"rules": []}), encoding="utf-8")
    r1 = load_categories(cats_file)
    assert r1 == []

    new_rule = CategoryRule(category="Coffee/Tea", subcategory="Starbucks", keywords=("Starbucks",))
    append_category_rule(new_rule, cats_file)
    r2 = load_categories(cats_file)
    assert len(r2) == 1
    assert r2[0].category == "Coffee/Tea"
    assert r2[0].subcategory == "Starbucks"
    assert "Starbucks" in r2[0].keywords


# ---------------------------------------------------------------------------
# 11. test_error_messages_match_contract
# ---------------------------------------------------------------------------


def test_error_messages_match_contract(tmp_path):
    """ConfigSchemaError messages must contain exact substrings per C1 error table."""

    def write_cfg(data: dict) -> Path:
        p = tmp_path / f"cfg_{hash(str(data)) & 0xFFFFFF}.yaml"
        p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        return p

    # Missing required key
    no_name = {k: v for k, v in _MINIMAL_USER_CONFIG.items() if k != "name"}
    with pytest.raises(ConfigSchemaError) as exc_info:
        load_user_config(write_cfg(no_name))
    assert "missing required key" in str(exc_info.value)
    assert "name" in str(exc_info.value)

    # Wrong type
    bad_type = {**_MINIMAL_USER_CONFIG, "fiscal_year_start_month": "January"}
    with pytest.raises(ConfigSchemaError) as exc_info:
        load_user_config(write_cfg(bad_type))
    msg = str(exc_info.value)
    assert "expected" in msg and "got" in msg

    # tax_jurisdiction fails regex
    bad_tj = {**_MINIMAL_USER_CONFIG, "tax_jurisdiction": "lowercase"}
    with pytest.raises(ConfigSchemaError) as exc_info:
        load_user_config(write_cfg(bad_tj))
    assert "tax_jurisdiction" in str(exc_info.value)
    assert "does not match" in str(exc_info.value)

    # fiscal_year_start_month out of range
    bad_month = {**_MINIMAL_USER_CONFIG, "fiscal_year_start_month": 13}
    with pytest.raises(ConfigSchemaError) as exc_info:
        load_user_config(write_cfg(bad_month))
    assert "fiscal_year_start_month must be 1..12" in str(exc_info.value)

    # cadence not in allowed set
    bad_cadence = {
        **_MINIMAL_USER_CONFIG,
        "fixed_obligations": [{"name": "Rent", "amount": 500.0, "cadence": "quarterly"}],
    }
    with pytest.raises(ConfigSchemaError) as exc_info:
        load_user_config(write_cfg(bad_cadence))
    assert "cadence" in str(exc_info.value)
    assert "quarterly" in str(exc_info.value)
    assert "monthly" in str(exc_info.value)
