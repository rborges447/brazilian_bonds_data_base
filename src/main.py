"""Entry point: rf-analytics CLI dispatcher."""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: rf-analytics <command> [args...]\n"
            "Commands:\n"
            "  bronze   — same as run_bronze.py (init, daily, one, backfill)\n"
            "  silver   — same as run_silver.py\n"
            "  gold     — same as run_gold.py\n"
            "  sync     — same as run_sync.py (daily, status)\n"
            "  migrate  — apply SQLite migrations\n"
        )
        sys.exit(1)

    cmd = sys.argv[1].lower()
    argv = [sys.argv[0], *sys.argv[2:]]
    sys.argv = argv

    if cmd == "bronze":
        from app.cli.bronze import main as bronze_main

        bronze_main()
        return
    if cmd == "silver":
        from app.cli.silver import main as silver_main

        silver_main()
        return
    if cmd == "gold":
        from app.cli.gold import main as gold_main

        gold_main()
        return
    if cmd == "sync":
        from app.cli.sync import main as sync_main

        sync_main()
        return
    if cmd == "migrate":
        from app.database import apply_migrations

        apply_migrations()
        return

    print(f"Unknown command: {cmd}")
    sys.exit(1)


if __name__ == "__main__":
    main()
