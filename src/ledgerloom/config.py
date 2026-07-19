"""Config loader and writer for ledgerloom.

Public API (see contracts/C1-config-api.md for the full contract):

    load_user_config(path=None) -> UserConfig
    load_categories(path=None) -> list[CategoryRule]
    load_merchants(path=None) -> dict[str, str]
    reset_config_cache() -> None

    save_user_config(cfg, path=None) -> None
    append_merchant(raw_fragment, canonical_name, path=None) -> None
    append_category_rule(rule, path=None) -> None

    ConfigNotFoundError(FileNotFoundError)
    ConfigSchemaError(ValueError)

Default search path: <repo_root>/config/<filename>.yaml
  where repo_root = Path(__file__).resolve().parents[2]

If LEDGERLOOM_CONFIG_DIR env var is set and path=None, defaults resolve to
  $LEDGERLOOM_CONFIG_DIR/<file>.yaml. Explicit path= always wins.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ConfigNotFoundError(FileNotFoundError):
    """Raised when a required config file does not exist."""


class ConfigSchemaError(ValueError):
    """Raised when a config file exists but fails schema validation."""


# ---------------------------------------------------------------------------
# Dataclasses  (frozen, slots per C1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FixedObligation:
    name: str
    amount: float  # positive, in user_config.currency
    cadence: str  # one of: "monthly", "weekly", "biweekly", "annual"


@dataclass(frozen=True, slots=True)
class FinancialGoal:
    name: str
    target_amount: float  # positive
    target_date: str  # ISO-8601 "YYYY-MM-DD"


@dataclass(frozen=True, slots=True)
class DataSource:
    name: str  # short identifier, e.g. "rbc", "rbc_credit"
    kind: str  # "checking", "credit_card", "splitwise", "paypal"
    parser: str  # module name under ledgerloom.parsers
    path: str  # relative to repo root
    # Optional: account_suffix to route generic-CSV sources to an account
    # (matches accounts.account_suffix). Falls back to `name` when absent.
    # Must stay last / defaulted so existing 4-positional construction sites
    # (PDF sources) are unaffected.
    account_suffix: str | None = None


@dataclass(frozen=True, slots=True)
class UserConfig:
    name: str
    currency: str
    locale: str
    country: str
    tax_jurisdiction: str
    fiscal_year_start_month: int
    monthly_income_after_tax: float
    fixed_obligations: tuple[FixedObligation, ...]
    financial_goals: tuple[FinancialGoal, ...]
    sources: tuple[DataSource, ...]


@dataclass(frozen=True, slots=True)
class CategoryRule:
    category: str
    subcategory: str  # may be ""
    keywords: tuple[str, ...]  # case-insensitive substrings


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_CADENCES = {"monthly", "weekly", "biweekly", "annual"}
_TAX_JURISDICTION_RE = re.compile(r"^[A-Z]{2}(-[A-Z0-9]{1,3})?$")

# ---------------------------------------------------------------------------
# Module-level caches  (keyed by resolved absolute path string)
# ---------------------------------------------------------------------------

_user_config_cache: dict[str, UserConfig] = {}
_categories_cache: dict[str, list[CategoryRule]] = {}
_merchants_cache: dict[str, dict[str, str]] = {}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    """Return the repo root: parent of 'src/', two levels up from this file."""
    return Path(__file__).resolve().parents[2]


def _default_path(filename: str) -> Path:
    """Resolve the default path for a config file.

    If LEDGERLOOM_CONFIG_DIR is set, resolves to $LEDGERLOOM_CONFIG_DIR/<filename>.
    Otherwise resolves to <repo_root>/config/<filename>.
    """
    env_dir = os.environ.get("LEDGERLOOM_CONFIG_DIR")
    if env_dir:
        return Path(env_dir) / filename
    return _repo_root() / "config" / filename


def _read_yaml(path: Path) -> Any:
    """Read and parse a YAML file. Single choke-point for monkeypatching in tests."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ConfigSchemaError(f"failed to parse {path.name}: {exc}") from exc


def _require_key(data: dict, key: str, filename: str) -> Any:
    if key not in data:
        raise ConfigSchemaError(f"missing required key '{key}' in {filename}")
    return data[key]


def _require_type(value: Any, expected_type: type, key: str, filename: str) -> Any:
    if not isinstance(value, expected_type):
        raise ConfigSchemaError(
            f"key '{key}' in {filename}: expected {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )
    return value


def _resolve_path(path: Path | None, filename: str) -> Path:
    """Return the resolved absolute path for a config file.

    If path is not None, use it directly (explicit always wins).
    Otherwise, use the default path resolution logic.
    """
    if path is not None:
        return path.resolve()
    return _default_path(filename).resolve()


def _check_file_exists(resolved: Path, explicit: bool) -> None:
    """Raise ConfigNotFoundError if the file does not exist.

    Uses different message formats depending on whether the path was
    explicitly supplied or derived from defaults.
    """
    if not resolved.exists():
        if explicit:
            raise ConfigNotFoundError(str(resolved))
        raise ConfigNotFoundError(
            f"config/user_config.yaml not found. Run /onboard to create it."
        )


def _check_config_file_exists(resolved: Path, filename: str, explicit: bool) -> None:
    """Raise ConfigNotFoundError for categories/merchants missing files."""
    if not resolved.exists():
        if explicit:
            raise ConfigNotFoundError(str(resolved))
        raise ConfigNotFoundError(f"{filename} not found. Run /onboard to create it.")


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


def _validate_user_config(data: Any, filename: str) -> UserConfig:
    if not isinstance(data, dict):
        raise ConfigSchemaError(
            f"key 'root' in {filename}: expected dict, got {type(data).__name__}"
        )

    # Required scalar fields
    name = _require_type(_require_key(data, "name", filename), str, "name", filename)
    if not name:
        raise ConfigSchemaError(f"key 'name' in {filename}: expected non-empty str")

    currency = _require_type(
        _require_key(data, "currency", filename), str, "currency", filename
    )
    locale = _require_type(
        _require_key(data, "locale", filename), str, "locale", filename
    )
    country = _require_type(
        _require_key(data, "country", filename), str, "country", filename
    )
    tax_jurisdiction = _require_type(
        _require_key(data, "tax_jurisdiction", filename),
        str,
        "tax_jurisdiction",
        filename,
    )
    if not _TAX_JURISDICTION_RE.match(tax_jurisdiction):
        raise ConfigSchemaError(
            f"tax_jurisdiction '{tax_jurisdiction}' does not match "
            r"^[A-Z]{2}(-[A-Z0-9]{1,3})?$"
        )

    fys_raw = _require_key(data, "fiscal_year_start_month", filename)
    _require_type(fys_raw, int, "fiscal_year_start_month", filename)
    if not (1 <= fys_raw <= 12):
        raise ConfigSchemaError(f"fiscal_year_start_month must be 1..12, got {fys_raw}")

    income_raw = _require_key(data, "monthly_income_after_tax", filename)
    if not isinstance(income_raw, (int, float)):
        raise ConfigSchemaError(
            f"key 'monthly_income_after_tax' in {filename}: expected float, "
            f"got {type(income_raw).__name__}"
        )
    if income_raw < 0:
        raise ConfigSchemaError(
            f"key 'monthly_income_after_tax' in {filename}: must be >= 0"
        )

    # Optional list fields
    raw_obligations = data.get("fixed_obligations") or []
    _require_type(raw_obligations, list, "fixed_obligations", filename)
    obligations: list[FixedObligation] = []
    for i, item in enumerate(raw_obligations):
        _require_type(item, dict, f"fixed_obligations[{i}]", filename)
        obl_name = _require_type(
            _require_key(item, "name", filename),
            str,
            f"fixed_obligations[{i}].name",
            filename,
        )
        obl_amount_raw = _require_key(item, "amount", filename)
        if not isinstance(obl_amount_raw, (int, float)):
            raise ConfigSchemaError(
                f"key 'fixed_obligations[{i}].amount' in {filename}: expected float, "
                f"got {type(obl_amount_raw).__name__}"
            )
        obl_cadence = _require_type(
            _require_key(item, "cadence", filename),
            str,
            f"fixed_obligations[{i}].cadence",
            filename,
        )
        if obl_cadence not in _VALID_CADENCES:
            raise ConfigSchemaError(
                f"cadence '{obl_cadence}' not in {{monthly,weekly,biweekly,annual}}"
            )
        obligations.append(
            FixedObligation(obl_name, float(obl_amount_raw), obl_cadence)
        )

    raw_goals = data.get("financial_goals") or []
    _require_type(raw_goals, list, "financial_goals", filename)
    goals: list[FinancialGoal] = []
    for i, item in enumerate(raw_goals):
        _require_type(item, dict, f"financial_goals[{i}]", filename)
        g_name = _require_type(
            _require_key(item, "name", filename),
            str,
            f"financial_goals[{i}].name",
            filename,
        )
        g_amount_raw = _require_key(item, "target_amount", filename)
        if not isinstance(g_amount_raw, (int, float)):
            raise ConfigSchemaError(
                f"key 'financial_goals[{i}].target_amount' in {filename}: expected float, "
                f"got {type(g_amount_raw).__name__}"
            )
        g_date = _require_type(
            _require_key(item, "target_date", filename),
            str,
            f"financial_goals[{i}].target_date",
            filename,
        )
        goals.append(FinancialGoal(g_name, float(g_amount_raw), g_date))

    raw_sources = data.get("sources") or []
    _require_type(raw_sources, list, "sources", filename)
    sources: list[DataSource] = []
    for i, item in enumerate(raw_sources):
        _require_type(item, dict, f"sources[{i}]", filename)
        s_name = _require_type(
            _require_key(item, "name", filename), str, f"sources[{i}].name", filename
        )
        s_kind = _require_type(
            _require_key(item, "kind", filename), str, f"sources[{i}].kind", filename
        )
        s_parser = _require_type(
            _require_key(item, "parser", filename),
            str,
            f"sources[{i}].parser",
            filename,
        )
        s_path = _require_type(
            _require_key(item, "path", filename), str, f"sources[{i}].path", filename
        )
        s_account_suffix = item.get("account_suffix")
        if s_account_suffix is not None:
            _require_type(
                s_account_suffix, str, f"sources[{i}].account_suffix", filename
            )
        sources.append(DataSource(s_name, s_kind, s_parser, s_path, s_account_suffix))

    return UserConfig(
        name=name,
        currency=currency,
        locale=locale,
        country=country,
        tax_jurisdiction=tax_jurisdiction,
        fiscal_year_start_month=fys_raw,
        monthly_income_after_tax=float(income_raw),
        fixed_obligations=tuple(obligations),
        financial_goals=tuple(goals),
        sources=tuple(sources),
    )


def _validate_categories(data: Any, filename: str) -> list[CategoryRule]:
    if not isinstance(data, dict):
        raise ConfigSchemaError(
            f"key 'root' in {filename}: expected dict, got {type(data).__name__}"
        )
    raw_rules = _require_key(data, "rules", filename)
    _require_type(raw_rules, list, "rules", filename)
    rules: list[CategoryRule] = []
    for i, item in enumerate(raw_rules):
        _require_type(item, dict, f"rules[{i}]", filename)
        cat = _require_type(
            _require_key(item, "category", filename),
            str,
            f"rules[{i}].category",
            filename,
        )
        subcat = item.get("subcategory", "")
        if subcat is None:
            subcat = ""
        _require_type(subcat, str, f"rules[{i}].subcategory", filename)
        raw_kws = item.get("keywords") or []
        _require_type(raw_kws, list, f"rules[{i}].keywords", filename)
        kws = tuple(str(k) for k in raw_kws)
        rules.append(CategoryRule(category=cat, subcategory=subcat, keywords=kws))
    return rules


def _validate_merchants(data: Any, filename: str) -> dict[str, str]:
    if not isinstance(data, dict):
        raise ConfigSchemaError(
            f"key 'root' in {filename}: expected dict, got {type(data).__name__}"
        )
    raw_merchants = _require_key(data, "merchants", filename)
    if raw_merchants is None:
        raw_merchants = {}
    _require_type(raw_merchants, dict, "merchants", filename)
    return {str(k): str(v) for k, v in raw_merchants.items()}


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------


def load_user_config(path: Path | None = None) -> UserConfig:
    """Load and validate user_config.yaml. Caches by resolved absolute path."""
    explicit = path is not None
    resolved = _resolve_path(path, "user_config.yaml")
    cache_key = str(resolved)

    if cache_key in _user_config_cache:
        return _user_config_cache[cache_key]

    if not resolved.exists():
        if explicit:
            raise ConfigNotFoundError(str(resolved))
        raise ConfigNotFoundError(
            "config/user_config.yaml not found. Run /onboard to create it."
        )

    data = _read_yaml(resolved)
    cfg = _validate_user_config(data, resolved.name)
    _user_config_cache[cache_key] = cfg
    return cfg


def load_categories(path: Path | None = None) -> list[CategoryRule]:
    """Load and validate categories.yaml. Caches by resolved absolute path."""
    explicit = path is not None
    resolved = _resolve_path(path, "categories.yaml")
    cache_key = str(resolved)

    if cache_key in _categories_cache:
        return _categories_cache[cache_key]

    if not resolved.exists():
        if explicit:
            raise ConfigNotFoundError(str(resolved))
        raise ConfigNotFoundError(
            "categories.yaml not found. Run /onboard to create it."
        )

    data = _read_yaml(resolved)
    rules = _validate_categories(data, resolved.name)
    _categories_cache[cache_key] = rules
    return rules


def load_merchants(path: Path | None = None) -> dict[str, str]:
    """Load and validate merchants.yaml. Caches by resolved absolute path."""
    explicit = path is not None
    resolved = _resolve_path(path, "merchants.yaml")
    cache_key = str(resolved)

    if cache_key in _merchants_cache:
        return _merchants_cache[cache_key]

    if not resolved.exists():
        if explicit:
            raise ConfigNotFoundError(str(resolved))
        raise ConfigNotFoundError(
            "merchants.yaml not found. Run /onboard to create it."
        )

    data = _read_yaml(resolved)
    merchants = _validate_merchants(data, resolved.name)
    _merchants_cache[cache_key] = merchants
    return merchants


def reset_config_cache() -> None:
    """Clear all three caches. Call in test fixtures; not for production use."""
    _user_config_cache.clear()
    _categories_cache.clear()
    _merchants_cache.clear()


# ---------------------------------------------------------------------------
# Public writers  (T6)
# ---------------------------------------------------------------------------


def save_user_config(cfg: UserConfig, path: Path | None = None) -> None:
    """Serialize a UserConfig dataclass to user_config.yaml (full overwrite).

    Invalidates the cache entry for the target file on success.
    """
    resolved = _resolve_path(path, "user_config.yaml")

    data: dict = {
        "name": cfg.name,
        "currency": cfg.currency,
        "locale": cfg.locale,
        "country": cfg.country,
        "tax_jurisdiction": cfg.tax_jurisdiction,
        "fiscal_year_start_month": cfg.fiscal_year_start_month,
        "monthly_income_after_tax": cfg.monthly_income_after_tax,
        "fixed_obligations": [
            {"name": ob.name, "amount": ob.amount, "cadence": ob.cadence}
            for ob in cfg.fixed_obligations
        ],
        "financial_goals": [
            {
                "name": g.name,
                "target_amount": g.target_amount,
                "target_date": g.target_date,
            }
            for g in cfg.financial_goals
        ],
        "sources": [
            {"name": s.name, "kind": s.kind, "parser": s.parser, "path": s.path}
            | (
                {"account_suffix": s.account_suffix}
                if s.account_suffix is not None
                else {}
            )
            for s in cfg.sources
        ],
    }

    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)

    # Invalidate cache so the next load_user_config returns fresh content
    _user_config_cache.pop(str(resolved), None)


def append_merchant(
    raw_fragment: str,
    canonical_name: str,
    path: Path | None = None,
) -> None:
    """Add or update one entry in merchants.yaml.

    Reads existing yaml, merges the new key (overwrites if already present),
    then writes back. Invalidates cache on success.
    """
    resolved = _resolve_path(path, "merchants.yaml")

    if resolved.exists():
        existing_data = _read_yaml(resolved)
        if not isinstance(existing_data, dict):
            existing_data = {}
        merchants: dict = existing_data.get("merchants") or {}
        if not isinstance(merchants, dict):
            merchants = {}
    else:
        merchants = {}

    merchants[raw_fragment] = canonical_name

    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            {"merchants": merchants}, fh, sort_keys=False, allow_unicode=True
        )

    _merchants_cache.pop(str(resolved), None)


def append_category_rule(rule: CategoryRule, path: Path | None = None) -> None:
    """Append one CategoryRule to the rules list in categories.yaml.

    Does not deduplicate — rule ordering and deduplication are the caller's
    responsibility (first-match-wins semantics per C1 §Caching behavior).
    Invalidates cache on success.
    """
    resolved = _resolve_path(path, "categories.yaml")

    if resolved.exists():
        existing_data = _read_yaml(resolved)
        if not isinstance(existing_data, dict):
            existing_data = {}
        rules: list = existing_data.get("rules") or []
        if not isinstance(rules, list):
            rules = []
    else:
        rules = []

    rules.append(
        {
            "category": rule.category,
            "subcategory": rule.subcategory,
            "keywords": list(rule.keywords),
        }
    )

    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as fh:
        yaml.safe_dump({"rules": rules}, fh, sort_keys=False, allow_unicode=True)

    _categories_cache.pop(str(resolved), None)
