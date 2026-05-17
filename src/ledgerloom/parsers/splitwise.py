"""Parser for Splitwise CSV exports.

Separates real shared expenses (SplitExpense) from person-to-person payments
(SplitPayment) and silently discards "Settle all balances" accounting artifacts.
"""

import csv
import json
import os
import re

from ledgerloom.config import load_user_config
from ledgerloom.parsers import SplitExpense, SplitPayment


def parse_splitwise_csv(csv_path: str) -> tuple[list[SplitExpense], list[SplitPayment]]:
    """Parse a Splitwise CSV export.

    Returns a (expenses, payments) tuple:
    - expenses: real shared expenses with user_share and counterparties
    - payments: person-to-person payment records (e.g. "X paid Y")

    "Settle all balances" rows are discarded entirely — they are internal
    Splitwise accounting artifacts, not real financial events.

    The user's name is read from load_user_config().name (e.g. "Jane Doe").
    Column detection uses full-name substring first, then first-token substring.
    Group name is extracted from the filename via a slug-based pattern; falls
    back to the full filename when no pattern matches.
    """
    cfg = load_user_config()
    user_name = cfg.name
    first_token = user_name.lower().split()[0]
    slug = re.sub(r"[^a-z0-9]+", "-", user_name.lower()).strip("-")

    expenses: list[SplitExpense] = []
    payments: list[SplitPayment] = []

    filename = os.path.basename(csv_path)
    source_file = filename

    # Determine group name from filename using slug-derived patterns.
    # Try patterns in order of specificity:
    #   1. Full slug: e.g. "jane-doe-and-..."
    #   2. First-token with optional suffix: e.g. "jane-d-and-..." (initial form)
    #   3. First-token with no suffix: e.g. "jane-and-..."
    # Fall through to the full filename when none match.
    group_name: str = filename
    for pattern in (
        rf"{re.escape(slug)}-and-(.+?)_\d{{4}}",
        rf"{re.escape(first_token)}-[^-]+-and-(.+?)_\d{{4}}",
        rf"{re.escape(first_token)}-and-(.+?)_\d{{4}}",
    ):
        m = re.match(pattern, filename)
        if m:
            group_name = m.group(1).replace("-", " ")
            break

    with open(csv_path, "r") as f:
        first_line = f.readline()
        if first_line.startswith("Note:"):
            # Skip blank lines after the Note header until we reach the CSV header
            while True:
                pos = f.tell()
                line = f.readline()
                if not line:
                    break
                if line.strip():
                    f.seek(pos)
                    break
        elif first_line.startswith("Date,"):
            f.seek(0)
        # else: unrecognised preamble — attempt to parse from current position

        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return expenses, payments

        # Find the user column (case-insensitive).
        # Two-stage: full-name substring first, then first-token substring.
        user_col: str | None = None
        user_name_lower = user_name.lower()
        for col in reader.fieldnames:
            col_lower = col.lower()
            if user_name_lower in col_lower:
                user_col = col
                break
        if user_col is None:
            for col in reader.fieldnames:
                col_lower = col.lower()
                if first_token in col_lower:
                    user_col = col
                    break

        if not user_col:
            return expenses, payments

        # Collect all person columns (non-metadata columns)
        metadata_cols = {"Date", "Description", "Category", "Cost", "Currency"}
        person_cols = [c for c in reader.fieldnames if c not in metadata_cols]

        for row in reader:
            date = row.get("Date", "").strip()

            # Skip rows without a valid YYYY-MM-DD date (totals, blanks, etc.)
            if not re.match(r"\d{4}-\d{2}-\d{2}", date):
                continue

            desc = row.get("Description", "").strip()
            category = row.get("Category", "").strip()
            cost_str = row.get("Cost", "0").strip()
            user_share_str = row.get(user_col, "0").strip()

            try:
                total_cost = float(cost_str) if cost_str else 0.0
                user_share_amount = float(user_share_str) if user_share_str else 0.0
            except ValueError:
                continue

            desc_lower = desc.lower()

            # 1. Discard settlement artifacts entirely
            if "settle all balances" in desc_lower:
                continue

            # 2. Payment rows: "X paid Y" descriptions
            if "paid" in desc_lower:
                # Parse "Firstname L. paid Firstname L." pattern
                pay_match = re.match(
                    r"(.+?)\s+paid\s+(.+)",
                    desc,
                    re.IGNORECASE,
                )
                if pay_match:
                    from_person = pay_match.group(1).strip()
                    to_person = pay_match.group(2).strip()
                else:
                    # Fallback: can't parse names cleanly
                    from_person = desc
                    to_person = ""

                payments.append(SplitPayment(
                    date=date,
                    from_person=from_person,
                    to_person=to_person,
                    amount=total_cost,
                    group_name=group_name,
                    source_file=source_file,
                ))
                continue

            # 3. Everything else is a real shared expense
            # Build counterparties: other person columns with a non-zero amount
            counterparties = []
            for col in person_cols:
                if col == user_col:
                    continue
                val_str = row.get(col, "0").strip()
                try:
                    val = float(val_str) if val_str else 0.0
                except ValueError:
                    val = 0.0
                if val != 0.0:
                    counterparties.append(col)

            expenses.append(SplitExpense(
                date=date,
                description=desc,
                sw_category=category,
                total_cost=total_cost,
                user_share=user_share_amount,
                group_name=group_name,
                source_file=source_file,
                counterparties=json.dumps(counterparties),
            ))

    return expenses, payments
