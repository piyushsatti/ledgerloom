#!/usr/bin/env python3
"""Build the ledgerloom database from sources listed in config/user_config.yaml.

First-run gate: if config/user_config.yaml does not exist, print a message
pointing at /onboard and exit with code 2.
"""

import sys
from pathlib import Path

from ledgerloom.config import ConfigNotFoundError, load_user_config
from ledgerloom.db import create_db
from ledgerloom.ingest import PARSER_REGISTRY, ingest_source
from ledgerloom.queries import verify_against_summaries

ROOT = Path(__file__).parent
CACHE_DIR = ROOT / "cache" / "extracted"
DB_PATH = ROOT / "ledgerloom.db"


def main():
    # ------------------------------------------------------------------
    # First-run gate (C3 §"First-run gate")
    # ------------------------------------------------------------------
    try:
        config = load_user_config()
    except ConfigNotFoundError:
        print(
            "config/user_config.yaml not found — run /onboard to create it."
        )
        sys.exit(2)

    # ------------------------------------------------------------------
    # Validate parser names against PARSER_REGISTRY before touching the DB
    # (C3 §"build_db.py sources schema": validation lives here, not in config)
    # ------------------------------------------------------------------
    unknown = [s.parser for s in config.sources if s.parser not in PARSER_REGISTRY]
    if unknown:
        print(
            f"Unknown parser(s) in config/user_config.yaml: {', '.join(unknown)}\n"
            f"Registered parsers: {', '.join(sorted(PARSER_REGISTRY))}\n"
            f"Run /parser to add a new parser, or fix the 'parser:' field in your config."
        )
        sys.exit(2)

    # ------------------------------------------------------------------
    # Build / open the database
    # ------------------------------------------------------------------
    print(f"Building database: {DB_PATH}")
    conn = create_db(str(DB_PATH))

    # ------------------------------------------------------------------
    # Ingest each source from config
    # ------------------------------------------------------------------
    total: dict = {"pdfs": 0, "transactions": 0, "sw_expenses": 0, "sw_payments": 0, "skipped": 0}

    if not config.sources:
        print("\nNo sources configured. Run /onboard or /parser to add data sources.")
    else:
        print("\nIngesting data...")
        for source in config.sources:
            source_path = ROOT / source.path
            if not source_path.exists():
                print(f"  [{source.name}] directory not found: {source_path} — skipping")
                continue
            print(f"  [{source.name}] scanning {source_path} ...")
            stats = ingest_source(conn, source, CACHE_DIR)
            for key in total:
                total[key] += stats.get(key, 0)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n=== STATS ===")
    print(f"  PDFs processed:     {total['pdfs']}")
    print(f"  Transactions:       {total['transactions']}")
    print(f"  Splitwise expenses: {total['sw_expenses']}")
    print(f"  Splitwise payments: {total['sw_payments']}")
    print(f"  Skipped (already):  {total['skipped']}")

    print(f"\n=== VERIFICATION ===")
    for v in verify_against_summaries(conn):
        print(f"  {v['account']} ({v['period']})")
        print(f"    Statement:  deposits={v['stmt_deposits']}, withdrawals={v['stmt_withdrawals']}")
        print(f"    Parsed:     deposits={v['parsed_deposits']}, withdrawals={v['parsed_withdrawals']}")
        print(f"    Status:     {v['status']}")

    conn.close()
    print(f"\nDone. Database at: {DB_PATH}")


if __name__ == "__main__":
    main()
