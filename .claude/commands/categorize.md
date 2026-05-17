# Categorize uncategorized merchants

## When to use

Run `/categorize` after your first `build_db.py` run, or any time the count of `Uncategorized` transactions is non-trivial (more than 5% of all transactions). This skill labels merchants one at a time, writes canonical names to `config/merchants.yaml` and keyword rules to `config/categories.yaml`, then re-runs the categorizer to flush the DB. It never edits Python files — that's `/parser`'s job.

## Prerequisites

- `ledgerloom.db` must exist. If not, run `uv run python build_db.py` first.
- `config/categories.yaml` and `config/merchants.yaml` must exist. Create them from `.example` siblings if missing.

## Steps

### Step 1 — Query uncategorized merchants

Run this query against `ledgerloom.db`:

```sql
SELECT raw_description, merchant, COUNT(*) cnt, SUM(amount) total
FROM transactions
WHERE category = 'Uncategorized' OR category IS NULL
GROUP BY merchant
ORDER BY ABS(SUM(amount)) DESC
LIMIT 50
```

Work top-down by **absolute spend**, not by frequency. A $400 charge that appears once matters more than a $3 coffee you categorize ten times.

### Step 2 — Show a preview

Before starting the loop, display the top 3 uncategorized merchants as a table:

| Merchant | Visits | Total Spend |
|----------|--------|-------------|
| ...      | ...    | ...         |

Then ask: "Ready to label these? I'll go one at a time — answer `done` at any point to stop."

### Step 3 — Label loop (max N=10 per run, default)

For each merchant in the top-N list:

1. Print the merchant name, raw description, visit count, total spend, and 2 sample raw descriptions.

2. Use `AskUserQuestion` to ask (one question at a time — this is non-negotiable per CLAUDE.md):
   > "What is `<merchant>`? Options: `<sorted category list from load_categories()>` | `skip` | `done`"
   
   The category list comes from `{r.category for r in load_categories()}` in first-occurrence order — never hard-coded.

3. If the user picks a category, ask a follow-up `AskUserQuestion`:
   > "Subcategory? Options: `<distinct subcategories in this category>` | `none` | `+ new`"

4. If the user picks `+ new`, ask one more `AskUserQuestion`:
   > "Type the new subcategory name:"

5. Ask one final `AskUserQuestion`:
   > "Canonical display name? (press Enter to keep `<merchant>`)"

6. Write the results via the C1 writer API — **do not call `yaml.safe_dump` directly**:
   ```python
   from ledgerloom.config import append_merchant, append_category_rule, CategoryRule
   
   # Always write the merchant mapping
   append_merchant(raw_fragment=merchant.upper(), canonical_name=canonical_answer)
   
   # Write a keyword rule only if the merchant looks like a generic fragment
   # (NOT a personal name — skip if the string looks like "First Last")
   is_personal_name = len(merchant.split()) == 2 and merchant.split()[0][0].isupper() and merchant.split()[1][0].isupper()
   if not is_personal_name:
       append_category_rule(CategoryRule(
           category=chosen_category,
           subcategory=chosen_subcategory,
           keywords=(merchant,),
       ))
   ```

7. After every 3 confirmed entries, flush by calling:
   ```python
   from ledgerloom.categorize import recategorize_all
   recategorize_all(conn)
   ```
   The writers already invalidated the cache — `recategorize_all` sees the fresh rules without a manual `reset_config_cache()` call. Report: "X merchants remain uncategorized."

### Step 4 — Termination

The loop exits when **any one** of these is true:
1. User answers `done` to the merchant prompt.
2. The top-N list is exhausted.
3. Uncategorized transactions drop below 5% of total transactions.
4. N=10 iterations have completed.

On exit, report:
- How many merchants were categorized this session.
- How many uncategorized transactions remain and what percentage of the total they represent.
- If the remaining count is non-trivial: "Run `/categorize` again to continue labeling."

## Termination contract

This skill is explicitly bounded. It will not run longer than N iterations in a single invocation. If you have hundreds of uncategorized merchants, run `/categorize` several times across different sessions — each run chips away at the top spenders first.

## Examples

**Walkthrough — categorizing 3 merchants**

Starting state: 34 uncategorized transactions (12% of 283 total).

Preview table shows top 3: `HARDWARE STORE` ($312, 2 visits), `PHARMACY` ($89, 4 visits), `LIQUOR STORE` ($74, 3 visits).

**Iteration 1 — HARDWARE STORE**

```
Merchant: HARDWARE STORE
Raw description: "Visa Debit purchase - HARDWARE STORE #123"
Visits: 2 | Total: -$312.00
Samples: "Visa Debit purchase - HARDWARE STORE #123" / "Visa Debit purchase - HARDWARE STORE #456"
```

`AskUserQuestion`: "What is HARDWARE STORE? Shopping / Home & Garden / Transfer / Income / skip / done"
→ User: "Shopping"

`AskUserQuestion`: "Subcategory? Home & Garden / none / + new"
→ User: "+ new"

`AskUserQuestion`: "Type the new subcategory name:"
→ User: "Hardware"

`AskUserQuestion`: "Canonical display name? (Enter to keep HARDWARE STORE)"
→ User: (Enter)

Writes:
```yaml
# merchants.yaml gets:
HARDWARE STORE: HARDWARE STORE

# categories.yaml gets a new rule:
- { category: "Shopping", subcategory: "Hardware", keywords: ["HARDWARE STORE"] }
```

After 3 entries: `recategorize_all` runs → "28 merchants remain uncategorized."

## Key principles

- One question at a time. Always. (This is the CLAUDE.md "one-question-at-a-time" discipline — never batch multiple questions into a single prompt.)
- Top-spend first, not top-frequency. A $400 charge that appeared once matters more than a $3 coffee that appeared 15 times.
- Append-only writes: never rewrite existing yaml entries unless the user explicitly asks to re-label.
- If a merchant has zero spend (transfer, deposit), default-suggest `Transfer` or `Income` as the first option.
- Skip the keyword-rule append for personal names (e.g. e-Transfer recipients). Only `append_merchant` runs in that case.
