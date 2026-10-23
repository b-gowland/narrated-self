"""The `tns` command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .protocol import protocol_hash
from .runner import dry_run, plan_round


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tns", description="The Narrated Self")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("protocol-hash", help="Print the SHA-256 of protocol/")

    run = sub.add_parser("run", help="Send the round's prompts to every model")
    run.add_argument("--round", required=True, dest="round_id")
    run.add_argument("--models", type=Path, help="Model config (default: config/models_<round>.yaml)")
    run.add_argument("--dry-run", action="store_true", help="Print the prompt matrix and cost; no API calls")

    args = parser.parse_args(argv)
    root = Path.cwd()

    if args.command == "protocol-hash":
        print(protocol_hash(root))
        return 0

    if args.command == "run":
        plan = plan_round(root, args.round_id, args.models)
        if args.dry_run:
            dry_run(plan)
            return 0
        from .runner import run_round

        return run_round(root, plan)

    return 1


if __name__ == "__main__":
    sys.exit(main())
