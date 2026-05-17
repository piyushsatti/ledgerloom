# Habits & Behavioral Deep Dive

Analyze spending patterns to identify behavioral drivers — not just what was spent, but WHY.

## Prerequisites
- `ledgerloom.db` must exist with transaction data

## Analysis

### 1. The Autopilot Score
Count days with small discretionary purchases ($1-10 range) at coffee shops, fast food, convenience stores.
- Days with autopilot spending / total days = autopilot rate
- Target: <30% of days

### 2. Comfort Spending Detection
Find merchants visited frequently with small, varied amounts (not subscriptions):
- Same merchant, 10+ visits in 3 months, amounts under $20
- These are often stress/comfort/habit purchases, not planned ones
- Cross-reference with day-of-week (worse on Mondays? After paydays?)

### 3. Day-of-Week Pattern
```sql
SELECT day_of_week, COUNT(*), SUM(amount), AVG(amount)
FROM transactions WHERE category IN discretionary_categories
GROUP BY day_of_week
```
Identify the worst day. Ask the user: "What happens on [worst day] that drives spending?"

### 4. Payday Effect
Compare spending in the 3 days before vs 3 days after each payday.
If post-payday spending is >1.5x pre-payday: flag it.
Intervention: automatic savings transfer on payday.

### 5. Time-of-Day Patterns (if data available)
If PayPal or email receipt data has timestamps:
- Morning purchases (commute spending)
- Afternoon purchases (3-4PM stress window)
- Evening purchases (tired/comfort)
- Late night purchases (impulse/sleep-deprived)

### 6. The Caffeine Audit
Identify all coffee/tea/energy drink purchases:
- McDonald's under $3 = coffee
- Tim Hortons = coffee
- Starbucks, other cafés = coffee/tea
Calculate: total caffeine spend per month, average per day, frequency

### 7. The Gap Day Problem
If the user has a meal plan:
- How many days/month does the meal plan cover?
- What happens on gap days? (restaurant spending spikes?)
- Cost of gap days vs extending the meal plan

### 8. Keystone Habit Assessment
Ask the user:
- Do you exercise regularly? When did you last have a consistent streak?
- What changed when you were exercising vs now?
- What's the barrier to restarting?

The research (Oaten & Cheng 2006, Hillman et al. 2008) shows exercise measurably reduces impulse spending by strengthening the prefrontal cortex. This is not motivational advice — it's neuroscience.

## Output
Present patterns with specific data, then connect each pattern to a behavioral driver. End with the top 3 habit changes ranked by financial impact.

## Key Principle
> "Finances follow habits, and habits are the keystones of everything."
Don't just analyze numbers. Understand the person behind the numbers — their stress, sleep, routines, and what triggers reactive spending.
