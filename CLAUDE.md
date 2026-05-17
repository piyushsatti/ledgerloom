# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

Personal finance analysis tool for anyone managing their own money. Parses bank statement PDFs, Splitwise CSVs, and PayPal exports into a queryable SQLite database for spending analysis, behavioral insights, and budgeting.

**Philosophy:** Finances follow habits. Don't just analyze numbers — understand the behaviors driving them. Connect spending patterns to stress, sleep, routines, and life circumstances.

## Build & Run

```bash
uv run python build_db.py                       # Parse all data, build ledgerloom.db
uv run pytest                                   # Full test suite
uv run pytest tests/test_db.py::test_name -v    # Single test
```

System dependency: `pdftotext` via `brew install poppler`

`build_db.py` is idempotent: SHA256 of each source file is checked against the `sources` table, so already-imported files are skipped. To re-categorize without re-parsing, call `ledgerloom.categorize.recategorize_all(conn)`.

## Custom Commands

This project includes slash commands for guided financial analysis:

| Command | Purpose |
|---------|---------|
| `/onboard` | First-time setup — gather context, write config, run initial analysis |
| `/parser` | Add a new bank/card parser — inspects a sample file, generates parser code, registers it |
| `/categorize` | Label uncategorized merchants; writes to `config/merchants.yaml` and `config/categories.yaml` |
| `/analyze` | Comprehensive spending analysis — categories, merchants, patterns, leaks |
| `/budget` | Generate three budget tiers (Strict, Semi-Strict, Lenient) with savings projections |
| `/subscriptions` | Audit all recurring charges across bank, PayPal, and email |
| `/habits` | Behavioral deep dive — autopilot spending, comfort eating, caffeine audit, keystone habits |
| `/perspectives` | Launch 6 parallel Opus subagents for multi-angle life analysis |
| `/salary-calc` | Net pay calculator (jurisdiction-aware) + affordability assessment |

**Recommended flow for new users:** `/onboard` → `/parser` (per data source) → `/categorize` → `/analyze` → `/habits` → `/budget`

## How to Guide Users

When someone opens this project for financial analysis:

1. **Start with curiosity, not spreadsheets.** Ask about their life — work hours, stress, sleep, routines. The numbers make more sense with context.
2. **One question at a time.** Use AskUserQuestion. Don't overwhelm with multiple questions.
3. **Connect spending to behavior.** "$X/month on convenience-store snacks" is data. "Those purchases cluster on stressful weekdays after long work hours" is insight.
4. **Be honest, not gentle.** Users want to know where they stand. Don't sugarcoat overdraft patterns or unsustainable spending.
5. **Research-backed recommendations.** Cite studies when recommending behavioral changes. Oaten & Cheng (2006) on exercise and spending. Kuchler & Pagel (2018) on tracking effects. Wansink (2006) on environmental friction.

## Project Structure

```text
config/                       # Personal config (gitignored; .example files committed)
  user_config.yaml.example    # Copy to user_config.yaml and fill in
  categories.yaml.example     # Category rules — edited by /categorize
  merchants.yaml.example      # Merchant canonical names — edited by /categorize
data/<source>/                # Bank PDFs / CSVs per source, paths from config/user_config.yaml — gitignored
cache/extracted/              # Cached pdftotext output — gitignored, regenerated
src/ledgerloom/                  # Python package
  config.py                   # Single source of truth for all config I/O (see Configuration)
  extract.py                  # PDF → text with SHA256 caching
  parsers/                    # Statement parsers (rbc.py, rbc_credit.py, amex.py, splitwise.py, ...)
  normalize.py                # Merchant name extraction + canonical mapping
  categorize.py               # Category rules engine
  db.py                       # SQLite schema + insert helpers
  ingest.py                   # Pipeline orchestrator + PARSER_REGISTRY
  queries.py                  # Read-only analysis functions
specs/                        # Four-layer spec framework (see Specs)
docs/                         # Analysis outputs and examples
build_db.py                   # CLI entry point
ledgerloom.db                    # Generated SQLite database — gitignored
```

## Specs

`specs/` is the source of truth for design decisions. Code comments often reference these by ID (e.g. `# C1`, `# C3 §"First-run gate"`). When unsure why something is designed a certain way, read the spec, not the code.

- `specs/intent/I.x` — why this project exists (stakeholder outcomes).
- `specs/capabilities/C.x` — externally observable behaviors per slash command.
- `specs/contracts/K.x` — internal typed commitments (producer/consumer/invariants). Edit these *before* changing the corresponding module.
- `specs/realizations/R.Kx` — file/module/test references that implement each contract.

Contracts and realizations are paired: `K.2-write-user-config.md` ↔ `R.K2-config-writer.md` ↔ `src/ledgerloom/config.py`.

## Configuration

Three YAML files live under `config/`. All config I/O goes through `src/ledgerloom/config.py` — never read or write YAML directly from any other module.

**Loader functions** (module `ledgerloom.config`):

- `load_user_config(path=None) -> UserConfig` — reads `config/user_config.yaml`
- `load_categories(path=None) -> list[CategoryRule]` — reads `config/categories.yaml`
- `load_merchants(path=None) -> dict[str, str]` — reads `config/merchants.yaml`

**Writer functions**:

- `save_user_config(cfg, path=None)` — full rewrite of `user_config.yaml`
- `append_merchant(raw_fragment, canonical_name, path=None)` — appends one entry to `merchants.yaml`
- `append_category_rule(rule, path=None)` — appends one rule to `categories.yaml`

All loaders cache by resolved path. Each writer invalidates its cache entry on success, so a `load_*()` call immediately after a writer always returns fresh content. Use `reset_config_cache()` in tests. Callers must never call `yaml.safe_dump` directly — all yaml emission lives in `ledgerloom.config`.

Key fields in `UserConfig`: `name`, `currency` (ISO-4217), `locale` (BCP-47), `country` (ISO-3166-1), `tax_jurisdiction` (e.g. `CA-QC`, `US-CA`, `IN-MH`), `fiscal_year_start_month`, `monthly_income_after_tax`, `fixed_obligations`, `financial_goals`, `sources`.

## Pipeline

```text
PDF/CSV → [Extract] → [Parse] → [Normalize] → [Categorize] → ledgerloom.db
```

Each stage is independent. Re-run categorization without re-parsing via `recategorize_all()` in `categorize.py`.

`ingest.py` dispatches via `PARSER_REGISTRY: dict[str, tuple[kind, callable]]` where `kind ∈ {"pdf", "csv"}`. Each `DataSource` in `user_config.yaml` carries a `parser:` field that must match a registry key — `build_db.py` validates this at startup before touching the DB and exits with code 2 on unknown parser names.

**Adding a parser**: prefer `/parser` (it generates the module, registers it, and appends the source block). Manual path: implement `parse_*(text|path) -> ParseResult` in `src/ledgerloom/parsers/<name>.py`, then add `"<name>": ("pdf"|"csv", parse_fn)` to `PARSER_REGISTRY`. `RawTransaction` / `ParseResult` types live in `src/ledgerloom/parsers/__init__.py`.

**Caveat**: `_detect_account()` in `ingest.py` maps PDF filenames to account suffixes via hardcoded keywords (`"checking"`, `"savings"`, `"credit"`, `amex/` parent dir). New banks added via `/parser` should extend this function — currently the only place statement-file → account routing lives outside `PARSER_REGISTRY`.

## Database Schema

Key tables: `accounts`, `sources` (file tracking/dedup), `transactions` (with raw_description, merchant, amount, category, subcategory, tx_method, is_recurring, metadata JSON), `splitwise_expenses`, `splitwise_payments`, `statement_summary`.

Key views: `v_monthly_spending`, `v_daily_totals`, `v_merchant_spending`.

The `splitwise_expenses` table uses `user_share` for the current user's portion of each shared expense.

## Example parsers shipped

Reference implementations bundled with the repo. Your bank will likely need `/parser` to generate its own:

- RBC (Canadian retail bank — checking, savings, credit card)
- American Express Cobalt (example)
- Splitwise CSV
- PayPal CSV

Add new banks via `/parser`.

## Analysis Queries

Prefer the helpers in `src/ledgerloom/queries.py` (`monthly_budget`, `spending_by_category`, `top_merchants`, `find_subscriptions`, `verify_against_summaries`) over ad-hoc SQL — they share a `_default_since()` policy (MIN(date) from transactions, else fiscal-year start from `user_config`) and consistently exclude `Transfer` from spend totals.

Pre-built views in the schema: `v_monthly_spending`, `v_daily_totals`, `v_merchant_spending`.

## Testing

- Fixtures live in `tests/conftest.py`: `db_conn` (in-memory DB with accounts seeded), `default_config` / `empty_rules_config` / `jane_doe_config` (write yaml into `tmp_path/config/`, set `LEDGERLOOM_CONFIG_DIR` env var, call `reset_config_cache()` on setup *and* teardown).
- Tests must never read `config/*.yaml` from the real repo. Use one of the config fixtures or set `LEDGERLOOM_CONFIG_DIR` yourself.
- `ledgerloom.config` caches by resolved absolute path; if a test mutates yaml on disk, call `reset_config_cache()` to force a reload.

## Adding New Data

Drop new statement files into the directory for your source (per the `sources:` block in `config/user_config.yaml`). Run `build_db.py` — only new/changed files are processed (SHA256 dedup).

## Security

Data files contain real financial information. The `data/` and `cache/` directories and `ledgerloom.db` are all gitignored. Never commit financial data. `config/*.yaml` (non-`.example`) files are also gitignored — they contain income and obligation figures.

## Key Research References

These studies inform the behavioral analysis features:
- **Oaten & Cheng (2006):** Exercise programs measurably reduce impulse spending
- **Hillman et al. (2008):** Exercise strengthens prefrontal cortex (impulse control)
- **Kuchler & Pagel (2018):** Tracking spending reduces it by 15-16%
- **Wansink (2006):** Small friction (6 feet) reduces consumption 50%
- **Thaler & Sunstein (2008):** Defaults and environmental design beat willpower
- **Drake et al.:** Caffeine 6hrs before bed reduces sleep by 1+ hour
