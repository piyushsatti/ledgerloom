# Full Spending Analysis

Run a comprehensive spending analysis on the user's financial data.

## Prerequisites
- `ledgerloom.db` must exist (run `uv run python build_db.py` first)

## Analysis Steps

### 1. Overview
Query the database for:
- Date range of transactions
- Total transactions per account
- Monthly net flows (income vs outflows)

### 2. Category Breakdown
- Spending by category (monthly and total)
- Month-over-month changes (flag categories that grew >20%)

### 3. Top Merchants
- Top 20 merchants by total spend
- Frequency of visits (high-frequency small purchases = autopilot spending)

### 4. Recurring Charges
- Same merchant + same amount appearing 2+ months = subscription
- Flag any that seem unused or duplicate

### 5. Behavioral Patterns
- Day-of-week spending distribution (which day costs the most?)
- Payday effect (do they spend more in the 3 days after payday?)
- Spending streaks (how many days per month have discretionary spending?)
- Low-balance/overdraft events

### 6. Splitwise Analysis (if data exists)
- Net Splitwise balance by person
- Separate settlements from real expenses
- Identify what portion of bank e-transfers are Splitwise settlements vs real payments

### 7. Food Spending Deep Dive
- Separate: groceries vs restaurants vs fast food vs coffee vs convenience store snacks
- Identify the daily "autopilot" spending pattern
- Calculate: total food spend including meal plans, dining, coffee, snacks

## Output
Present findings clearly with tables. Identify the top 3 spending leaks. Ask the user which areas they want to dig into.

## Key Principle
Don't just show numbers — connect spending patterns to behaviors. "$X/month on convenience-store snacks" is data. "Those purchases cluster on stressful weekdays after long work hours" is insight. Always pair the dollar figure with the behavioral pattern that produced it (time of day, day of week, mood proxies, payday proximity).
