# Subscription Audit

Find and classify all recurring charges across bank statements, PayPal, and email.

## Steps

### 1. Database scan
Query for merchants with the same amount appearing 2+ months:
```sql
SELECT merchant, amount, COUNT(*) as times, MIN(date) as first, MAX(date) as last
FROM transactions WHERE amount < 0 AND merchant IS NOT NULL
GROUP BY merchant, amount HAVING COUNT(*) >= 2
ORDER BY amount ASC
```

### 2. PayPal scan
If `data/PyapalDownload.CSV` or any PayPal CSV exists, parse it and extract all recurring payments (filter for Completed, negative amounts, named merchants).

### 3. Gmail scan (if available)
Search Gmail for subscription-related emails:
- `subject:subscription OR subject:renewal OR subject:billing`
- `from:paypal subject:receipt`
- `from:apple.com subscription`
- `from:affirm`

### 4. Classify each subscription

| Status | Meaning |
|--------|---------|
| ACTIVE — KEEP | Currently using, worth the cost |
| ACTIVE — REVIEW | Using but expensive, might downgrade |
| ACTIVE — UNKNOWN | Don't know what this is |
| ACTIVE — CANCEL | Not using or not worth it |
| CANCELLED | Previously active, now stopped |

### 5. Present findings
Show a table with: service name, monthly amount, last charge date, status, recommended action.

Calculate total monthly subscription cost (excluding installments) and total including installments.

### 6. Optimization suggestions
- Any subscriptions available cheaper through direct billing vs App Store?
- Any duplicate services (e.g., two cloud storage, two streaming)?
- Any that can be downgraded to free tier?
- Annual vs monthly pricing comparison where applicable

## Key Principle
Small subscriptions are diagnostic. $2.59/month doesn't matter financially. But forgetting it exists reveals a pattern of unmonitored recurring charges.
