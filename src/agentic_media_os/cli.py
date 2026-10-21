"""CLI uses the same service and state store as the API."""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from agentic_media_os.config import Settings
from agentic_media_os.models import ApprovedContent, Brief, Review, WorkflowRun
from agentic_media_os.providers import LocalProvider
from agentic_media_os.store import Conflict, NotFound, SQLiteRunStore
from agentic_media_os.workflows import ContentWorkflow


def read_json(path: Path) -> str:
    with path.open(encoding="utf-8-sig") as handle:
        text = handle.read(262145)
    if len(text.encode("utf-8")) > 262144:
        raise ValueError("Input file too large")
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agentic Media OS local content workflow")
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("run", help="Generate a draft awaiting review")
    start.add_argument("brief", type=Path)
    for command in ("show", "export"):
        commands.add_parser(command).add_argument("id", type=UUID)
    review = commands.add_parser("review")
    review.add_argument("id", type=UUID)
    review.add_argument("decision", type=Path, help="Review JSON; see examples/review.json")
    args = parser.parse_args(argv)
    try:
        config = Settings()
        logging.basicConfig(level=config.log_level, format="%(levelname)s %(name)s %(message)s")
        store = SQLiteRunStore(config.database_path)
        workflow = ContentWorkflow(store, LocalProvider())
        result: WorkflowRun | ApprovedContent
        match args.command:
            case "run":
                result = workflow.start(Brief.model_validate_json(read_json(args.brief)))
            case "show":
                result = store.get(args.id)
            case "review":
                result = workflow.review(
                    args.id, Review.model_validate_json(read_json(args.decision))
                )
            case "export":
                result = workflow.export(args.id)
            case _:
                raise ValueError("Unknown command")
        print(result.model_dump_json(indent=2))
        return 1 if getattr(result, "status", None) == "failed" else 0
    except (ValidationError, ValueError, OSError, sqlite3.Error, NotFound, Conflict) as error:
        # Do not echo exception messages: they may include secrets, notes or filesystem paths.
        print(
            f"Operation failed ({type(error).__name__}); check input, state and config.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
