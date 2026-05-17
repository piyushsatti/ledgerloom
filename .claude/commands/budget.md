# Budget Tier Generator

Generate three budget tiers (Strict, Semi-Strict, Lenient) based on the user's actual financial data.

## Prerequisites
- `ledgerloom.db` must exist
- User should have run `/analyze` first (or you need to gather income + fixed costs)

## Steps

### 1. Calculate committed costs
Query the database and ask the user to confirm:
- Housing (rent + utilities)
- Non-negotiable obligations (remittance, child support, etc.)
- Transit
- Phone/internet
- Bank fees
- Insurance
- Installment payments (Affirm, car, etc.)
- Subscriptions (list each one with amount)
- Fixed food plans (meal subscriptions)

Sum = total committed. Available = income - committed.

### 2. Analyze current discretionary spending
From the database, calculate average monthly spending in:
- Coffee/tea
- Fast food
- Restaurants
- Groceries
- Shopping
- Transport (beyond transit pass)
- Entertainment
- Alcohol
- Other discretionary

### 3. Generate three tiers

**STRICT (War Mode):**
- Zero purchased coffee (home-brew only)
- Minimal social spending
- Groceries from discount stores, list-only shopping
- Zero restaurants, zero shopping, zero Uber
- Goal: maximum savings for emergency fund building

**SEMI-STRICT (Disciplined):**
- One purchased coffee/day max
- Moderate social budget
- Planned weekly grocery trips
- Occasional restaurants (gap days only)
- Minimal shopping (essentials)
- Goal: sustainable default operating mode

**LENIENT (Comfortable):**
- Reasonable daily spending
- Regular social activities
- Normal grocery habits
- Occasional dining out
- Some shopping budget
- Goal: long-term sustainable after emergency fund is built

### 4. Calculate for each tier
- Total discretionary spend
- Monthly savings
- Annual savings
- Time to reach $2K / $5K / $10K emergency fund

### 5. Recommend which tier and when
- STRICT for the first 1-2 months (build emergency buffer)
- SEMI-STRICT as default
- LENIENT after emergency fund target is met

### 6. Project future scenarios
If the user shares career plans (expected raise, job hop), calculate what each tier looks like at higher income levels.

## Output Format
Present as a clean table with all three tiers side by side. Include a "when to use each" guide.
