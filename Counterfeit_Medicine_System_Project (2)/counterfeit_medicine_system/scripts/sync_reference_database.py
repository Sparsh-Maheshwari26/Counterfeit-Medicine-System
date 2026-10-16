from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_store import get_counts, init_db, save_openfda_records  # noqa: E402
from src.reference_sync import fetch_openfda_records  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync product-reference records from the openFDA NDC Directory.")
    parser.add_argument("--target", type=int, default=500, help="Number of unique product records to fetch, default: 500")
    args = parser.parse_args()
    if args.target < 1:
        parser.error("--target must be at least 1")

    init_db()
    print(f"Fetching {args.target} product reference records from openFDA...")
    try:
        records = fetch_openfda_records(target=args.target)
        saved = save_openfda_records(records)
    except Exception as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        print("Existing local database was not partially updated.", file=sys.stderr)
        return 1

    counts = get_counts()
    print(f"Saved {saved} official product-reference records.")
    print(f"Local database: {counts['official']} official listings, {counts['demo']} demo-only rows.")
    print("Reminder: openFDA NDC listings do not authenticate a physical package or batch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
