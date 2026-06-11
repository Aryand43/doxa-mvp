"""
Developer CLI for the IRIS vector POC.

Verify connectivity before doing anything expensive:
    poetry run python -m backend.scripts.index_mock_data check

Index the mock invoices dataset into IRIS:
    poetry run python -m backend.scripts.index_mock_data index --reset
    poetry run python -m backend.scripts.index_mock_data index --limit 200

Run a sample similarity query from the command line:
    poetry run python -m backend.scripts.index_mock_data query "high risk invoices pending approval"
    poetry run python -m backend.scripts.index_mock_data query "overdue payments to GreenBuild" --top-k 3
"""

from __future__ import annotations

import argparse
import logging
import sys

from backend.vector.ingest import ingest
from backend.vector.preflight import run_preflight
from backend.vector.search import search_procurement_context


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _cmd_check(args: argparse.Namespace) -> int:
    result = run_preflight(create_table=not args.no_create)

    print("\nIRIS preflight check")
    print("--------------------")
    print(f"  config valid       : {'yes' if result.config_ok else 'NO'}")
    print(f"  OPENAI_API_KEY set : {'yes' if result.openai_key_present else 'NO'}")
    print(f"  connection ok      : {'yes' if result.connection_ok else 'NO'}")
    print(f"  table ok           : {'yes' if result.table_ok else 'NO'}")
    if result.table_status is not None:
        print(f"  table status       : {result.table_status}")
    if result.document_count is not None:
        print(f"  rows in table      : {result.document_count}")
    if result.errors:
        print("  notes:")
        for err in result.errors:
            print(f"    - {err}")
    print(f"\nResult: {'READY' if result.ok else 'NOT READY'}\n")

    return 0 if result.ok else 1


def _cmd_index(args: argparse.Namespace) -> int:
    count = ingest(limit=args.limit, reset=args.reset, batch_size=args.batch_size)
    scope = f"{args.limit} rows" if args.limit else "all rows"
    print(f"Indexed {count} invoice documents ({scope}) into IRIS.")
    return 0


def _cmd_query(args: argparse.Namespace) -> int:
    matches = search_procurement_context(args.text, top_k=args.top_k)
    if not matches:
        print("No matches found. Did you run the `index` command first?")
        return 0

    print(f'Top {len(matches)} matches for: "{args.text}"\n')
    for rank, match in enumerate(matches, start=1):
        print(f"[{rank}] score={match.score:.4f}  doc_id={match.doc_id}")
        print(f"    {match.content}")
        print(f"    metadata: {match.metadata}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="index_mock_data",
        description="Index mock procurement data into IRIS and query it.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser(
        "check",
        help="Verify env vars, IRIS connectivity, and the target table.",
    )
    p_check.add_argument(
        "--no-create",
        action="store_true",
        help="Only report whether the table exists; do not create it.",
    )
    p_check.set_defaults(func=_cmd_check)

    p_index = sub.add_parser("index", help="Embed and load the invoices dataset.")
    p_index.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the vector table before loading.",
    )
    p_index.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only index the first N rows (useful to bound embedding cost).",
    )
    p_index.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Rows per embed + upsert batch (default: 100).",
    )
    p_index.set_defaults(func=_cmd_index)

    p_query = sub.add_parser("query", help="Run a top-k similarity search.")
    p_query.add_argument("text", help="Natural-language query string.")
    p_query.add_argument("--top-k", type=int, default=5, help="Number of results.")
    p_query.set_defaults(func=_cmd_query)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _configure_logging(getattr(args, "verbose", False))
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
