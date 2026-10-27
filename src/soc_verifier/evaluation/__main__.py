"""Local-only evaluation preparation, separate from the planning CLI."""

import argparse
from pathlib import Path

from pydantic import ValidationError

from soc_verifier.evaluation.baseline import freeze_baseline, verify_baseline
from soc_verifier.settings import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze")
    freeze.add_argument("--source", type=Path, required=True)
    freeze.add_argument("--reference", type=Path, required=True)
    freeze.add_argument("--historical-run", type=Path)
    freeze.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("bundle", type=Path)
    verify.add_argument("--check-originals", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "freeze":
            manifest = freeze_baseline(
                repository=Path.cwd(),
                source=args.source,
                reference=args.reference,
                historical_run=args.historical_run,
                output=args.output,
                settings=Settings(),
            )
            print(f"Frozen {len(manifest.files)} files in {args.output}; no model calls.")
        else:
            manifest = verify_baseline(args.bundle, check_originals=args.check_originals)
            print(f"Verified {len(manifest.files)} files; semantic acceptance remains pending.")
    except ValidationError:
        parser.exit(1, "Evaluation snapshot schema validation failed.\n")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Evaluation snapshot failed: {error}\n")


if __name__ == "__main__":
    main()
