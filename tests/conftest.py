"""Shared test fixtures for the finance analysis test suite."""

import sqlite3
import textwrap

import pytest

import ledgerloom.config as _config_module
from ledgerloom.config import reset_config_cache
from ledgerloom.db import create_db


# ---------------------------------------------------------------------------
# Database fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def db_conn(tmp_path):
    """In-memory database with schema and accounts seeded."""
    conn = create_db(str(tmp_path / "test.db"))
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Config fixtures (P2.T6)
#
# Each fixture:
#   1. Writes yaml files into tmp_path/config/
#   2. Sets LEDGERLOOM_CONFIG_DIR so loaders resolve there
#   3. Calls reset_config_cache() on setup and teardown
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# default_config — mirrors today's full CATEGORY_RULES + MERCHANT_MAP
# ---------------------------------------------------------------------------

_DEFAULT_CATEGORIES_YAML = textwrap.dedent("""\
rules:
  - {category: "Income",       subcategory: "Salary",         keywords: ["Payroll Deposit"]}
  - {category: "Income",       subcategory: "Tax Refund",     keywords: ["Tax Refund", "GST CANADA"]}
  - {category: "Income",       subcategory: "Wire",           keywords: ["Funds transfer credit"]}
  - {category: "Income",       subcategory: "Interest",       keywords: ["Deposit interest", "Bonus deposit interest"]}
  - {category: "Transfer",     subcategory: "e-Transfer In",  keywords: ["e-Transfer received", "e-Transfer - Autodeposit"]}
  - {category: "Transfer",     subcategory: "e-Transfer Out", keywords: ["e-Transfer sent"]}
  - {category: "Transfer",     subcategory: "Internal",       keywords: ["Online Banking transfer", "Online Transfer to Deposit", "BR TO BR", "to Find & Save", "Auto transfer", "Find & Save from", "WWW transfer"]}
  - {category: "Transfer",     subcategory: "Remittance",     keywords: ["International remittance"]}
  - {category: "Bills",        subcategory: "Phone",          keywords: ["Telco"]}
  - {category: "Bills",        subcategory: "Transit Pass",   keywords: ["Transit Authority"]}
  - {category: "Bills",        subcategory: "Gym",            keywords: ["Local Gym", "Fitness Center"]}
  - {category: "Bills",        subcategory: "Bank Fee",       keywords: ["Monthly fee"]}
  - {category: "Bills",        subcategory: "Overdraft",      keywords: ["Overdraft interest"]}
  - {category: "Bills",        subcategory: "NSF Fee",        keywords: ["NSF item fee", "Annual NSF"]}
  - {category: "Bills",        subcategory: "NSF Return",     keywords: ["Item returned NSF"]}
  - {category: "Bills",        subcategory: "BNPL",           keywords: ["Affirm"]}
  - {category: "Subscription", subcategory: "Claude AI",      keywords: ["Claude AI", "Anthropic"]}
  - {category: "Subscription", subcategory: "OpenAI",         keywords: ["OpenAI"]}
  - {category: "Subscription", subcategory: "Apple",          keywords: ["Apple (subscription)"]}
  - {category: "Subscription", subcategory: "PayPal",         keywords: ["PayPal"]}
  - {category: "Coffee/Tea",   subcategory: "Tim Hortons",    keywords: ["Tim Hortons"]}
  - {category: "Coffee/Tea",   subcategory: "Starbucks",      keywords: ["Starbucks"]}
  - {category: "Coffee/Tea",   subcategory: "Second Cup",     keywords: ["Second Cup"]}
  - {category: "Coffee/Tea",   subcategory: "Coffee Shop A",  keywords: ["Coffee Shop A"]}
  - {category: "Coffee/Tea",   subcategory: "Coffee Shop B",  keywords: ["Coffee Shop B"]}
  - {category: "Fast Food",    subcategory: "McDonald's",     keywords: ["McDonald's"]}
  - {category: "Fast Food",    subcategory: "Subway",         keywords: ["Subway"]}
  - {category: "Fast Food",    subcategory: "Pizza Hut",      keywords: ["Pizza Hut"]}
  - {category: "Fast Food",    subcategory: "Pizza Pizza",    keywords: ["Pizza Pizza"]}
  - {category: "Fast Food",    subcategory: "Dairy Queen",    keywords: ["Dairy Queen"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant A", keywords: ["Local Restaurant A"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant B", keywords: ["Local Restaurant B"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant C", keywords: ["Local Restaurant C"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant D", keywords: ["Local Restaurant D"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant E", keywords: ["Local Restaurant E"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant F", keywords: ["Local Restaurant F"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant G", keywords: ["Local Restaurant G"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant H", keywords: ["Local Restaurant H"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant I", keywords: ["Local Restaurant I"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant J", keywords: ["Local Restaurant J"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant K", keywords: ["Local Restaurant K"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant L", keywords: ["Local Restaurant L"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant M", keywords: ["Local Restaurant M"]}
  - {category: "Restaurant",   subcategory: "Local Restaurant N", keywords: ["Local Restaurant N"]}
  - {category: "Groceries",    subcategory: "Local Market",   keywords: ["Local Market"]}
  - {category: "Groceries",    subcategory: "Walmart",        keywords: ["Walmart"]}
  - {category: "Groceries",    subcategory: "Supermarket A",  keywords: ["Supermarket A"]}
  - {category: "Groceries",    subcategory: "Supermarket B",  keywords: ["Supermarket B"]}
  - {category: "Groceries",    subcategory: "Supermarket C",  keywords: ["Supermarket C"]}
  - {category: "Groceries",    subcategory: "Pharmacy",       keywords: ["Pharmacy"]}
  - {category: "Groceries",    subcategory: "Grocery Store",  keywords: ["Grocery Store"]}
  - {category: "Shopping",     subcategory: "Winners",        keywords: ["Winners"]}
  - {category: "Shopping",     subcategory: "Old Navy",       keywords: ["Old Navy"]}
  - {category: "Shopping",     subcategory: "Dollarama",      keywords: ["Dollarama"]}
  - {category: "Shopping",     subcategory: "Canadian Tire",  keywords: ["Canadian Tire"]}
  - {category: "Shopping",     subcategory: "IKEA",           keywords: ["IKEA"]}
  - {category: "Shopping",     subcategory: "Apple Store",    keywords: ["Apple Store"]}
  - {category: "Shopping",     subcategory: "Call It Spring", keywords: ["Call It Spring"]}
  - {category: "Shopping",     subcategory: "Nick the Tailor", keywords: ["Nick the Tailor"]}
  - {category: "Shopping",     subcategory: "Liquidation",    keywords: ["Liquidation"]}
  - {category: "Transport",    subcategory: "Uber",           keywords: ["Uber"]}
  - {category: "Transport",    subcategory: "ATM",            keywords: ["ATM withdrawal", "ATM deposit"]}
  - {category: "Alcohol",      subcategory: "Liquor Store",   keywords: ["Liquor Store"]}
  - {category: "Entertainment", subcategory: "Entertainment Venue", keywords: ["Entertainment Venue"]}
  - {category: "Amex",         subcategory: "Membership Fee", keywords: ["MEMBERSHIP FEE"]}
  - {category: "Amex",         subcategory: "Cash Back",      keywords: ["CASH BACK REWARD", "CREDIT BALANCE REFUND"]}
""")

_DEFAULT_MERCHANTS_YAML = textwrap.dedent("""\
merchants:
  TIM HORTONS: Tim Hortons
  MCDONALD: McDonald's
  STARBUCKS: Starbucks
  SECOND CUP: Second Cup
  COFFEE SHOP A: Coffee Shop A
  COFFEE SHOP B: Coffee Shop B
  LOCAL MARKET: Local Market
  WALMART STORE: Walmart
  WALMART.CA: Walmart
  SUPERMARKET A: Supermarket A
  SUPERMARKET B: Supermarket B
  SUPERMARKET C: Supermarket C
  PHARMACY: Pharmacy
  GROCERY STORE: Grocery Store
  LOCAL RESTAURANT A: Local Restaurant A
  LOCAL RESTAURANT B: Local Restaurant B
  LOCAL RESTAURANT C: Local Restaurant C
  LOCAL RESTAURANT D: Local Restaurant D
  LOCAL RESTAURANT E: Local Restaurant E
  LOCAL RESTAURANT F: Local Restaurant F
  LOCAL RESTAURANT G: Local Restaurant G
  LOCAL RESTAURANT H: Local Restaurant H
  LOCAL RESTAURANT I: Local Restaurant I
  LOCAL RESTAURANT J: Local Restaurant J
  LOCAL RESTAURANT K: Local Restaurant K
  LOCAL RESTAURANT L: Local Restaurant L
  LOCAL RESTAURANT M: Local Restaurant M
  LOCAL RESTAURANT N: Local Restaurant N
  PIZZA HUT: Pizza Hut
  PIZZA PIZZA: Pizza Pizza
  DAIRY QUEEN: Dairy Queen
  SUBWAY: Subway
  WINNERS: Winners
  OLD NAVY: Old Navy
  DOLLARAMA: Dollarama
  CANADIAN TIRE: Canadian Tire
  IKEA: IKEA
  APPLE STORE: Apple Store
  APPLE.COM/BILL: Apple (subscription)
  CALL IT SPRING: Call It Spring
  NICK THE TAILOR: Nick the Tailor
  LIQUIDATION: Liquidation
  UBER CANADA: Uber
  UBER TRIP: Uber
  TELCO: Telco
  LOCAL GYM: Local Gym
  FITNESS CENTER: Fitness Center
  AFFIRM: Affirm
  CLAUDE.AI: Claude AI
  ANTHROPIC: Anthropic
  OPENAI: OpenAI
  PAYPAL: PayPal
  LINKEDI: LinkedIn
  LIQUOR STORE: Liquor Store
  ENTERTAINMENT VENUE: Entertainment Venue
  TRANSIT AUTHORITY: Transit Authority
""")

_DEFAULT_USER_CONFIG_YAML = textwrap.dedent("""\
name: "Test User"
currency: "CAD"
locale: "en-CA"
country: "CA"
tax_jurisdiction: "CA-QC"
fiscal_year_start_month: 1
monthly_income_after_tax: 5000.00
fixed_obligations: []
financial_goals: []
sources: []
""")

_EMPTY_RULES_USER_CONFIG_YAML = textwrap.dedent("""\
name: "Test User"
currency: "CAD"
locale: "en-CA"
country: "CA"
tax_jurisdiction: "CA-QC"
fiscal_year_start_month: 1
monthly_income_after_tax: 5000.00
fixed_obligations: []
financial_goals: []
sources: []
""")

_JANE_DOE_USER_CONFIG_YAML = textwrap.dedent("""\
name: "Jane Doe"
currency: "CAD"
locale: "en-CA"
country: "CA"
tax_jurisdiction: "CA-QC"
fiscal_year_start_month: 1
monthly_income_after_tax: 4000.00
fixed_obligations: []
financial_goals: []
sources: []
""")


def _write_config(config_dir, user_yaml, categories_yaml, merchants_yaml):
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "user_config.yaml").write_text(user_yaml, encoding="utf-8")
    (config_dir / "categories.yaml").write_text(categories_yaml, encoding="utf-8")
    (config_dir / "merchants.yaml").write_text(merchants_yaml, encoding="utf-8")


@pytest.fixture
def default_config(tmp_path, monkeypatch):
    """Config fixture with full CATEGORY_RULES and MERCHANT_MAP (Test User)."""
    config_dir = tmp_path / "config"
    _write_config(config_dir, _DEFAULT_USER_CONFIG_YAML, _DEFAULT_CATEGORIES_YAML, _DEFAULT_MERCHANTS_YAML)
    monkeypatch.setenv("LEDGERLOOM_CONFIG_DIR", str(config_dir))
    reset_config_cache()
    yield config_dir
    reset_config_cache()


@pytest.fixture
def empty_rules_config(tmp_path, monkeypatch):
    """Config fixture with empty rules and merchants (new-fork state)."""
    config_dir = tmp_path / "config"
    empty_cats = "rules: []\n"
    empty_merchants = "merchants: {}\n"
    _write_config(config_dir, _EMPTY_RULES_USER_CONFIG_YAML, empty_cats, empty_merchants)
    monkeypatch.setenv("LEDGERLOOM_CONFIG_DIR", str(config_dir))
    reset_config_cache()
    yield config_dir
    reset_config_cache()


@pytest.fixture
def jane_doe_config(tmp_path, monkeypatch):
    """Config fixture for a non-default user (Jane Doe)."""
    config_dir = tmp_path / "config"
    empty_cats = "rules: []\n"
    empty_merchants = "merchants: {}\n"
    _write_config(config_dir, _JANE_DOE_USER_CONFIG_YAML, empty_cats, empty_merchants)
    monkeypatch.setenv("LEDGERLOOM_CONFIG_DIR", str(config_dir))
    reset_config_cache()
    yield config_dir
    reset_config_cache()
