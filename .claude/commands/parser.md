# Add a new statement parser

## When to use

Run `/parser` any time you have a bank, credit card, or wallet whose statement format isn't yet supported. This skill inspects a sample file, generates a parser at `src/ledgerloom/parsers/<bank>.py`, registers it in the pipeline, and wires a `sources:` entry into `config/user_config.yaml`. It's the only skill that writes Python — `/categorize` only edits yaml.

## Prerequisites

- `config/user_config.yaml` must exist. If it doesn't, run `/onboard` first.
- For PDF statements: `pdftotext` must be available (`brew install poppler` on macOS).

## Inputs

The user provides:
- **sample_path** — path to one sample statement (PDF or CSV), absolute or repo-relative.
- **bank_name** (optional, snake_case) — e.g. `td_visa`, `wise`. If omitted, infer from filename or document header and ask the user to confirm.
- **parser_kind** (optional) — one of `bank`, `credit`, `csv`. If omitted, infer: PDF + "Withdrawals"/"Deposits" columns → `bank`; PDF + "STATEMENT FROM" + dual-date lines → `credit`; CSV file → `csv`.

## Steps

### Step 1 — Read the sample

For PDF files: call `extract_pdf(Path(sample_path), Path("cache/extracted"))` from `src/ledgerloom/extract.py` so caching is consistent with the real pipeline. Show the user the **first 60 lines** of the extracted text so both of you see what the parser must handle.

For CSV files: read the first 20 rows and display them.

If pdftotext returns fewer than 5 non-blank lines, **abort**. Show the user all extracted text and say: "Extraction produced too little text — check that pdftotext is installed and the PDF is not image-only."

### Step 2 — Study the exemplars

Read all existing parsers in `src/ledgerloom/parsers/`: `rbc.py`, `rbc_credit.py`, `amex.py`, and the splitwise parser. Match the closest pattern by `parser_kind`:
- `bank` → model on `rbc.py` (column-position parsing, multi-line accumulation)
- `credit` → model on `rbc_credit.py` (two-date regex per line, amount with sign)
- `csv` → model on `splitwise.py` (csv.DictReader, path arg)

### Step 3 — Confirm the key facts (one question at a time)

Ask the user three questions via `AskUserQuestion`, strictly one at a time:

1. "What short name should I use for this bank? (snake_case, e.g. `td_visa`)"
2. "Is this a bank/chequing account, a credit card, or a CSV export? Answer: bank / credit / csv"
3. "What account suffix(es) appear in the filename or header? (e.g. `1234`, `5678`, or `none` if unknown)"

Never batch these into one question. Wait for each answer before asking the next.

### Step 4 — Generate the parser file

Write `src/ledgerloom/parsers/<bank_name>.py`. The file must:

- Import `ParseResult`, `RawTransaction` from `ledgerloom.parsers` at the top.
- Expose exactly one public entry point:
  - PDF: `def parse_<bank_name>_statement(text: str) -> ParseResult`
  - CSV: `def parse_<bank_name>_csv(path: str) -> ParseResult`
- Follow the sign convention from `rbc_credit.py`: **purchases/outflows are negative, refunds/credits are positive**.
- Parse the statement period when present and set `result.period = (start_iso, end_iso)`.
- Set `tx_method` where derivable from the description prefix; leave `None` otherwise.
- Match the structure of the closest exemplar — constants at the top, helpers in the middle, one parser function at the bottom.

### Step 5 — Register in ingest.py

Edit `src/ledgerloom/ingest.py`:

1. Add an import at the top of the existing imports block:
   ```python
   from ledgerloom.parsers.<bank_name> import parse_<bank_name>_statement  # or _csv
   ```
2. Add a registry entry to the existing `PARSER_REGISTRY` dict:
   ```python
   PARSER_REGISTRY["<bank_name>"] = ("pdf", parse_<bank_name>_statement)
   # or ("csv", parse_<bank_name>_csv) for CSV parsers
   ```

Do NOT refactor the registry or touch any other part of `ingest.py`. If `PARSER_REGISTRY` is missing from `ingest.py`, stop and report: "PARSER_REGISTRY not found in ingest.py — P2.T8 may not have shipped. Escalate before continuing."

### Step 6 — Append the sources entry to config

Load `config/user_config.yaml`, add the new source, and write it back via the C1 API — never write yaml directly from this skill:

```python
from ledgerloom.config import load_user_config, save_user_config, DataSource
cfg = load_user_config()
new_source = DataSource(
    name="<bank_name>",
    kind="<checking | credit_card | splitwise | paypal>",
    parser="<bank_name>",
    path="data/<bank_name>",
)
new_sources = tuple(list(cfg.sources) + [new_source])
save_user_config(cfg.__class__(**{**vars(cfg), "sources": new_sources}))
```

Create the directory `data/<bank_name>/` if it doesn't exist.

### Step 7 — Smoke-run

Run the new parser against the sample and report the transaction count:

```bash
uv run python -c "
from ledgerloom.parsers.<bank_name> import parse_<bank_name>_statement
from ledgerloom.extract import extract_pdf
from pathlib import Path
result = parse_<bank_name>_statement(extract_pdf(Path('<sample_path>'), Path('cache/extracted')))
print(len(result.transactions), 'transactions')
"
```

If the count is **0**, do NOT register the parser. Show the user the first 30 lines of extracted text and ask: "The parser found 0 transactions. Is this file in the expected format?" Wait for the user's answer before proceeding.

### Step 8 — Tell the user what's next

Print: "Drop more `<bank_name>` statements into `data/<bank_name>/` and run `uv run python build_db.py` — only new files will be processed."

## Examples

**Example A — TD Visa credit card PDF**

User runs: `/parser sample_path=data/td_visa/td_statement_2026_03.pdf`

- Step 1 extracts text; first line contains "STATEMENT FROM FEB 01, 2026 TO MAR 01, 2026".
- Step 2 picks `rbc_credit.py` as the closest exemplar (two-date + amount-per-line pattern).
- Step 3 asks: bank name → `td_visa`; kind → `credit`; suffix → `none`.
- Step 4 generates `src/ledgerloom/parsers/td_visa.py` modeled on `rbc_credit.py`, adjusting the regex for TD's header wording.
- Step 5 adds `PARSER_REGISTRY["td_visa"] = ("pdf", parse_td_visa_statement)`.
- Step 6 writes `sources: [{name: td_visa, kind: credit_card, parser: td_visa, path: data/td_visa}]`.
- Step 7 smoke-run reports "47 transactions".

**Example B — Wise CSV export**

User runs: `/parser sample_path=data/wise/transfers_2026.csv`

- Step 1 shows the first 20 CSV rows; columns include `Date`, `Amount`, `Description`.
- Step 2 picks the splitwise CSV style as the closest exemplar.
- Step 3 asks: bank name → `wise`; kind → `csv`; suffix → `none`.
- Step 4 generates `src/ledgerloom/parsers/wise.py` with `parse_wise_csv(path: str) -> ParseResult`.
- Step 5 adds `PARSER_REGISTRY["wise"] = ("csv", parse_wise_csv)`.
- Step 6 writes `sources: [{name: wise, kind: checking, parser: wise, path: data/wise}]`.
- Step 7 smoke-run reports "23 transactions".

## Key principles

- Match the closest exemplar; do not invent novel structure.
- Sign convention is non-negotiable: outflows negative, inflows positive.
- Never edit `normalize.py` or `categorize.py` from this skill — those are `/categorize`'s job.
- If the sample is ambiguous, ASK; never guess silently.

## Failure modes

| Situation | Action |
|---|---|
| pdftotext returns < 5 non-blank lines | Abort. Show all extracted text. Tell user to verify pdftotext is installed and PDF is not image-only. |
| Parser regex matches 0 lines / 0 transactions | Do NOT register. Show first 30 lines of extracted text. Ask: "Is this file in the expected format?" |
| Generated parser raises an exception during smoke-run | Show the full traceback. Do not commit the parser file. Fix the regex before proceeding. |
| User answers `abort` at any `AskUserQuestion` | Exit cleanly. Do not write partial files. |
