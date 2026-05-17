"""Integration smoke tests — skipped automatically when real data files are absent."""

import pytest
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "extracted"
CONFIG_DIR = Path(__file__).parent.parent / "config"

# Skip when real data OR config files are absent
_data_present = (DATA_DIR / "rbc").exists() and any((DATA_DIR / "rbc").glob("*.pdf"))
_config_present = (CONFIG_DIR / "user_config.yaml").exists()

pytestmark = pytest.mark.skipif(
    not _data_present or not _config_present,
    reason="Real data files or config files not present"
)


def test_full_pipeline(tmp_path):
    """Run the full pipeline on real data and verify basic sanity."""
    from ledgerloom.db import create_db
    from ledgerloom.ingest import ingest_all

    db_path = tmp_path / "test_integration.db"
    conn = create_db(str(db_path))
    stats = ingest_all(conn, DATA_DIR, CACHE_DIR)

    # Should have parsed some PDFs
    assert stats["pdfs"] > 0
    assert stats["transactions"] > 100  # we know there are ~559

    # Should have splitwise data if CSVs present
    if (DATA_DIR / "splitwise").exists():
        assert stats["sw_expenses"] > 0

    # Verify savings accounts match perfectly
    from ledgerloom.queries import verify_against_summaries
    for v in verify_against_summaries(conn):
        if "Savings" in v["account"]:
            assert v["status"] == "OK", f"Savings mismatch: {v}"

    conn.close()


def test_incremental_import(tmp_path):
    """Running pipeline twice should skip already-imported files."""
    from ledgerloom.db import create_db
    from ledgerloom.ingest import ingest_all

    db_path = tmp_path / "test_incremental.db"
    conn = create_db(str(db_path))

    stats1 = ingest_all(conn, DATA_DIR, CACHE_DIR)
    stats2 = ingest_all(conn, DATA_DIR, CACHE_DIR)

    assert stats1["pdfs"] > 0
    assert stats2["pdfs"] == 0  # all skipped on second run
    assert stats2["skipped"] == stats1["pdfs"] + stats1["skipped"]

    conn.close()
