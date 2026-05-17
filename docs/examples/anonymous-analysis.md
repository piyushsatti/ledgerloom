# Example /analyze Output — March 2026

Alex Rivera, 28, software engineer, lives in Austin TX, single, no dependents.
This is what `/analyze` produced after three months of data (January–March 2026).

## Snapshot

```text
Net monthly income (configured)   $5,400
Cash on hand (checking + savings)  $3,100
Emergency fund target              $8,000  (currently $1,200 — 15% funded)
Overdrafts last 3 months           1
Savings trajectory                 Slightly positive (+$180/mo avg)
```

## Category breakdown (last 3 months)

| Category     | Jan      | Feb      | Mar      | 3-mo avg |
| ------------ | -------- | -------- | -------- | -------- |
| Groceries    | $310     | $295     | $340     | $315     |
| Restaurant   | $280     | $390     | $330     | $333     |
| Coffee/Tea   | $88      | $74      | $91      | $84      |
| Transport    | $145     | $120     | $160     | $142     |
| Subscription | $97      | $97      | $112     | $102     |
| Shopping     | $210     | $65      | $185     | $153     |
| Bills        | $1,220   | $1,220   | $1,220   | $1,220   |
| **Total out**| **$2,350**| **$2,261**| **$2,438**| **$2,349**|

Bills = rent $950 + phone $65 + internet $55 + gym $30 + renter's insurance $120.

## Top merchants

| Merchant          | Category    | Visits | 3-mo total |
| ----------------- | ----------- | ------ | ---------- |
| Generic Grocery Co. | Groceries | 14     | $945       |
| Corner Coffee     | Coffee/Tea  | 18     | $251       |
| BurgerJoint       | Fast Food   | 9      | $137       |
| Streaming+        | Subscription| 3      | $54        |
| RideShare         | Transport   | 11     | $198       |
| Online Bookstore  | Shopping    | 4      | $122       |
| Local Bakery      | Coffee/Tea  | 6      | $74        |
| City Transit      | Transport   | 22     | $88        |

## Behavioral patterns

**Friday lunch clustering.** Friday lunch spend is 2.3x Monday lunch spend. BurgerJoint and
RideShare both spike on Fridays — end-of-week social routine with colleagues, not hunger.

**Payday effect.** 47% of restaurant spend lands in the 3 days after the 15th. Paycheck
arrives → discretionary guard drops → dining out increases. The pattern resets by day 18.

**Autopilot.** Corner Coffee visits: 18 in March, total $74 — consistent 7am pattern on
workdays. This is not a decision; it is a routine. At $251/quarter, worth a deliberate choice
about whether to keep it.

## Top 3 spending leaks

1. **Subscription overlap.** Streaming+ ($18/mo) and a second streaming service ($15/mo) cover
   largely the same content library. One cancellation saves $180/year.
2. **Late-night delivery.** Four delivery-app orders between 10pm and midnight in March, avg
   $28 each. These correlate with low-balance days — stress eating, not appetite. Total: $112
   in March alone.
3. **Impulse shopping.** January and March both show $180–$210 in Shopping; February (a
   stressful work month) is $65. Inverse correlation with work stress suggests shopping as a
   pressure release rather than need-driven purchasing.

## Suggested next steps

- Run `/subscriptions` to see the full recurring-charge list and flag overlaps.
- Run `/habits` for a deeper behavioral audit (autopilot spend, caffeine timing, payday effect).
- Run `/budget` to generate Strict / Semi-Strict / Lenient tiers based on this three-month baseline.

---

*Fabricated example. Numbers, names, and patterns are illustrative — your `/analyze` output will be shaped by your data and config.*
