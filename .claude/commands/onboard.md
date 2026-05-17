# Financial Analysis Onboarding

You are the single entry point for new users of this finance analysis tool. Walk every step in order. Don't skip any step on a first run. Ask one question at a time using `AskUserQuestion` — never batch.

## Step 1 — Detect first-run state

Check whether `config/user_config.yaml` exists.

- **If it doesn't exist:** proceed through all 11 steps. This is a first run.
- **If it already exists:** ask `AskUserQuestion`: "You're already onboarded. What would you like to do? re-onboard (full flow, won't clobber existing config) / refresh-memory-only (re-run analysis + update memory note, skip setup) / abort"
  - `refresh-memory-only` → jump to Step 9.
  - `re-onboard` → proceed through all steps but never overwrite existing yaml keys without prompting.
  - `abort` → exit cleanly.

## Step 2 — Identity & locale

Ask `AskUserQuestion`, one at a time, collecting:

1. "What's your name? (used to identify you in Splitwise exports)"
2. "What country are you in? (2-letter code, e.g. CA, US, GB)"
3. "What's your tax jurisdiction? (e.g. CA-QC for Quebec, CA-ON for Ontario, US-CA for California)"
4. "What currency do you use? (3-letter ISO code, e.g. CAD, USD, GBP)"
5. "What locale? (BCP-47 tag, e.g. en-CA, en-US — press Enter for en-CA)"
6. "What month does your fiscal year start? (1–12, press Enter for 1 = January)"

Store all answers in memory before writing anything.

## Step 3 — Income & obligations

Ask `AskUserQuestion`, one at a time:

1. "What's your monthly net income after tax? (the amount that actually hits your bank)"

Then loop on fixed obligations until the user says done:
- "Add a fixed obligation? Format: `name | amount | cadence` (e.g. `Rent | 1500 | monthly`) — or `done` to continue"
- Valid cadences: `monthly`, `weekly`, `biweekly`, `annual`

Then loop on financial goals until done:
- "Add a financial goal? Format: `name | target_amount | target_date` (e.g. `Emergency fund | 10000 | 2026-12-31`) — or `done` to continue"

## Step 4 — Write config/user_config.yaml

Using the C1 writer API, write `config/user_config.yaml` with all gathered fields and `sources: []`:

```python
from ledgerloom.config import save_user_config, UserConfig, FixedObligation, FinancialGoal
cfg = UserConfig(
    name=name,
    currency=currency,
    locale=locale,
    country=country,
    tax_jurisdiction=tax_jurisdiction,
    fiscal_year_start_month=fiscal_year_start_month,
    monthly_income_after_tax=monthly_income_after_tax,
    fixed_obligations=tuple(obligations),
    financial_goals=tuple(goals),
    sources=(),
)
save_user_config(cfg)
```

If `config/` is empty and a `.example` file exists, copy that as the starting point before merging user answers. Report: "Config written to config/user_config.yaml."

## Step 5 — Detect data files

Scan `data/` recursively for `*.pdf` and `*.csv` files. Group by directory. Report what's there:

```
data/rbc/        — 12 PDFs
data/amex/       — 6 PDFs
data/splitwise/  — 2 CSVs
```

For each directory, check if its name matches a parser in `ingest.PARSER_REGISTRY`. Unrecognized directories are candidates for `/parser`. If everything is recognized, skip Step 6.

## Step 6 — Invoke /parser for unrecognized sources

For each directory that has files but no matching parser, ask `AskUserQuestion`:
- "I found files in `data/<dir>/` but no parser for it. Run `/parser` to add one? yes / skip"

If the user says yes, dispatch the `/parser` skill with the first sample file from that directory. Wait for it to complete before moving to the next directory. `/parser` will write back to `config/user_config.yaml` `sources:` automatically.

Process one directory at a time, sequentially.

## Step 7 — Build the database

Run: `uv run python build_db.py`

Show the output. If it exits with an error, diagnose and fix before continuing. Report the final stats: PDFs processed, transactions loaded, Splitwise entries.

## Step 8 — First-pass categorization

Invoke `/categorize` with `top_n=10`. The user gets a feel for the labeling loop without spending an hour on it. They can always run `/categorize` again later for more coverage.

## Step 9 — Baseline analysis

Run these queries against `ledgerloom.db` and present the top 3 findings inline (do not dispatch `/analyze` — leave that for the user's first real session):

```sql
-- Top spending category
SELECT category, SUM(amount) total FROM transactions
WHERE amount < 0 GROUP BY category ORDER BY total LIMIT 1;

-- Top merchant by spend
SELECT merchant, SUM(amount) total FROM transactions
WHERE amount < 0 AND merchant IS NOT NULL
GROUP BY merchant ORDER BY total LIMIT 1;

-- Biggest single outflow (potential leak)
SELECT date, raw_description, amount FROM transactions
WHERE amount < 0 ORDER BY amount LIMIT 1;
```

Present concisely: "Your top category is X ($Y/month). Your top merchant is Z ($W total). Your biggest single charge was $V on DATE."

Connect the numbers to behavior where you can — don't just print them.

## Step 10 — Seed auto-memory

Write a memory note (via the `Memory` tool or by appending to `MEMORY.md` per the harness convention) summarizing:

- Name and monthly income after tax
- Top fixed obligation and its amount
- Top financial goal and target date
- Primary data sources (names from `config.sources`)
- One sentence on what brought them here (inferred from their goals)

One paragraph max. On re-run, append a dated entry rather than clobbering the existing note.

Example: "Alex: $5,200/month net, $1,800/month rent (monthly), saving $15,000 for house down payment by 2027-06-30. Sources: chase_checking, chase_credit, paypal. Onboarded 2026-05-17."

## Step 11 — What to do next

Print this exactly:

"You're set. Run `/analyze` for the full picture, `/budget` to plan, `/habits` for behavioral patterns. Drop new statements into `data/<bank>/` and re-run `uv run python build_db.py` — only new files are processed."
