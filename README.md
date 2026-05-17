# LedgerLoom

A fork-and-personalize personal-finance tool. Drop in your bank statements (PDF) and
Splitwise/PayPal CSVs; Claude parses, categorizes, and analyzes — connecting spending
to behavior, not just numbers.

Fork this repo, run `/onboard` once, and the tool adapts to your banks, country,
currency, and tax jurisdiction.

## What you get

- A local SQLite database of every transaction across all your accounts. No cloud, no
  third-party sync.
- Nine slash commands: setup (`/onboard`, `/parser`, `/categorize`) and analysis
  (`/analyze`, `/budget`, `/habits`, `/subscriptions`, `/perspectives`, `/salary-calc`).
- Behavioral framing — recommendations cite Oaten & Cheng (2006), Kuchler & Pagel
  (2018), and Wansink (2006) rather than generic "spend less" advice.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- `pdftotext` — `brew install poppler` (macOS) / `apt install poppler-utils` (Linux)
- Claude Code CLI installed and authenticated

## Quick start

1. `git clone <your-fork-url> && cd ledgerloom`
2. Open the repo in Claude Code (`claude`), then run `/onboard`. It will ask for your
   name, income, currency, tax jurisdiction, and fixed obligations — one question at a
   time — and write `config/user_config.yaml`.
3. Drop your statement files into the directories the onboarder told you (per the
   `sources:` block in your config).
4. `uv run python build_db.py` — then run `/analyze`.

## Adding a new bank

- Save a sample statement (PDF or CSV) in `data/<bank>/`.
- Run `/parser` — it inspects the format, generates `src/ledgerloom/parsers/<bank>.py`,
  and registers it in `ingest.py`.
- The skill also appends the source block to `config/user_config.yaml` for you.

## What ships out of the box

| Item                      | Notes                                                                                                                                                        |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Example parsers           | RBC checking/savings, RBC Mastercard, Amex Cobalt, Splitwise CSV, PayPal CSV. Reference implementations — your bank likely needs `/parser`.                  |
| Example category taxonomy | `config/categories.yaml.example` — ~10 universal categories (Groceries, Restaurant, Coffee/Tea, Transport, Subscription, Shopping, Bills, Income, Transfer). |
| Empty merchants map       | `config/merchants.yaml.example` — populated by `/categorize` as you label merchants.                                                                         |

## Privacy

- `data/`, `cache/`, `ledgerloom.db`, and `config/*.yaml` (non-`.example` files) are
  gitignored.
- Auto-memory lives in `~/.claude/projects/<repo-path>/memory/` — per-machine,
  per-user, never committed.
- Do not commit financial data. If you accidentally do, see CLAUDE.md for cleanup notes.

## Project layout

```text
config/                       # Your personal config (gitignored; .example files committed)
  user_config.yaml.example    # Copy to user_config.yaml and fill in
  categories.yaml.example     # Category rules — edited by /categorize
  merchants.yaml.example      # Merchant canonical names — edited by /categorize
data/<source>/                # Bank PDFs / CSVs per source, paths from config/user_config.yaml — gitignored
cache/extracted/              # Cached pdftotext output — gitignored, regenerated
src/ledgerloom/                  # Python package
  config.py                   # Single source of truth for all config I/O
  extract.py                  # PDF → text with SHA256 caching
  parsers/                    # Statement parsers (rbc.py, rbc_credit.py, amex.py, splitwise.py, ...)
  normalize.py                # Merchant name extraction + canonical mapping
  categorize.py               # Category rules engine
  db.py                       # SQLite schema + insert helpers
  ingest.py                   # Pipeline orchestrator: extract → parse → normalize → categorize → insert
  queries.py                  # Read-only analysis functions
docs/                         # Analysis outputs and examples
build_db.py                   # CLI entry point
ledgerloom.db                    # Generated SQLite database — gitignored
```

## See also

- `CLAUDE.md` — philosophy, research references, contributor notes.
- `docs/examples/anonymous-analysis.md` — what a `/analyze` output looks like.
