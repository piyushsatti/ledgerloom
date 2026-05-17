# Salary & Affordability Calculator

Calculate net take-home pay at different salary tiers and assess affordability of major expenses.

## Usage

Read the user's `tax_jurisdiction` and `monthly_income_after_tax` from `config/user_config.yaml`
via `load_user_config()` (C1). If `tax_jurisdiction` is unset or the calculator doesn't have a
model for it, ask the user one question to confirm jurisdiction, then proceed with general
bracketed-tax reasoning rather than failing. The calculator runs on **gross salary tiers the user
provides** (or a range), not on the configured income — `monthly_income_after_tax` is used only
as a sanity check ("your configured net is $X — does our calc match?").

## What to Calculate

### 1. Net pay breakdown

For each salary tier, calculate net pay according to `tax_jurisdiction` (C1 field; format
`<COUNTRY_ISO2>-<SUBDIVISION>`, e.g. `CA-QC`, `US-CA`, `IN-MH`, or just `CA`). The tool ships
precomputed bracket logic for **`CA-QC`** and **`CA-ON`** as reference implementations. For other
jurisdictions, the assistant must:

- Ask the user for top-line marginal-rate info, OR
- Use a transparent "ballpark" model (e.g. effective rate from current brackets the assistant
  looks up in conversation), explicitly labeled as an estimate, AND
- Suggest the user add their jurisdiction to a future built-in by opening an issue.

### 2. Effective income

Pull non-negotiables from `user_config.fixed_obligations` (C1 field — list of
`{name, amount, cadence}`). Sum the monthly equivalents. Effective monthly = net − obligations.
Do not hardcode obligation categories like "remittance" or "child support"; the config defines them.

### 3. Housing affordability

- At each salary tier: what percentage is their housing cost of effective income?
- Rule of thumb: housing should be <30% of effective income
- Flag as OK / TIGHT / STRETCHED

### 4. Savings potential

Using their current committed costs:

- Available for discretionary at each salary tier
- Projected monthly savings at each budget tier (strict/semi/lenient)

### 5. Career milestone framing

- "The jump from $X to $Y adds $Z/month net"
- "At $Y, you save more on LENIENT than you currently save on STRICT"

Use placeholder tiers derived from the user's actual income range; do not hardcode specific
salary figures. The user's current net is implicit from `monthly_income_after_tax`.

## Jurisdiction notes

### CA-QC (Quebec)

Quebec has the highest marginal rates in Canada (~37% effective at mid income, ~45% at higher
brackets, ~50% at top brackets). Canada-specific savings vehicles:

- RRSP contributions more valuable at higher brackets — advise deferring RRSP until income is
  meaningfully above current level
- TFSA first for emergency savings (tax-free growth)
- FHSA if eligible ($8K/year, significant tax saving at higher brackets)

### CA-ON (Ontario)

Ontario marginal rates are ~5–8 percentage points lower than Quebec at equivalent income.
Same federal structure (CPP, EI, RRSP/TFSA/FHSA) applies.

### Other jurisdictions

If `tax_jurisdiction` is anything other than `CA-QC` or `CA-ON`, the calculator will use a
transparent estimate based on information gathered in conversation. Country-specific advice
(401k, ISA, NPS, superannuation, etc.) is out of scope unless you have configured it or
provided the relevant bracket info.

## Output

Clean table showing all salary tiers side by side. Include the "inflection point" where budget
stress disappears. Label any jurisdiction outside the two shipped implementations as an estimate.
