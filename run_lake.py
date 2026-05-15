#!/usr/bin/env python
"""Thin CLI for the rf_lake data lake."""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  python run_lake.py migrate\n"
            "  python run_lake.py daily [YYYY-MM-DD]\n"
            "  python run_lake.py backfill START END [PIPELINE]\n"
            "  python run_lake.py one PIPELINE DATE"
        )
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "migrate":
        from rf_lake.bootstrap import bootstrap

        bootstrap()
        print("Migrations applied.")
        return

    if cmd == "daily":
        from rf_lake.jobs import run_daily

        target = sys.argv[2] if len(sys.argv) > 2 else None
        print(run_daily(target))
        return

    if cmd == "backfill":
        if len(sys.argv) < 4:
            print("Usage: python run_lake.py backfill START_DATE END_DATE [PIPELINE]")
            sys.exit(1)
        from rf_lake.jobs import backfill

        pipeline = sys.argv[4] if len(sys.argv) > 4 else None
        print(backfill(sys.argv[2], sys.argv[3], pipeline))
        return

    if cmd == "one":
        if len(sys.argv) < 4:
            print("Usage: python run_lake.py one PIPELINE DATE")
            sys.exit(1)
        from rf_lake.jobs import run_one

        print(run_one(sys.argv[2], sys.argv[3]))
        return

    print(f"Unknown command: {cmd}")
    sys.exit(1)


if __name__ == "__main__":
    main()
