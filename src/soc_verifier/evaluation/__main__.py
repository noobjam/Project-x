"""Local-only evaluation preparation, separate from the planning CLI."""

import argparse
from pathlib import Path

from pydantic import ValidationError

from soc_verifier.evaluation.baseline import _json_bytes, freeze_baseline, verify_baseline
from soc_verifier.evaluation.packets import (
    PrivateSelection,
    PublicRecipe,
    fetch_public,
    load_packet,
    prepare_private,
    prepare_public,
    require_ignored,
)
from soc_verifier.evaluation.pilot import freeze_pilot, verify_pilot
from soc_verifier.evaluation.scoring import Annotations, score_packet, validate_annotations
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
    private = commands.add_parser("prepare-private")
    private.add_argument("--baseline", type=Path, required=True)
    private.add_argument("--selection", type=Path, required=True)
    private.add_argument("--output", type=Path, required=True)
    public = commands.add_parser("prepare-public")
    public.add_argument("--recipe", type=Path, required=True)
    public.add_argument("--source-root", type=Path, required=True)
    public.add_argument("--output", type=Path, required=True)
    fetch = commands.add_parser("fetch-public")
    fetch.add_argument("--recipe", type=Path, required=True)
    fetch.add_argument("--output", type=Path, required=True)
    packet = commands.add_parser("verify-packet")
    packet.add_argument("packet", type=Path)
    packet.add_argument("--annotations", type=Path)
    pilot = commands.add_parser("freeze-pilot")
    pilot.add_argument("root", type=Path)
    pilot.add_argument("--annotations-file", default="reference/annotations.v001.json")
    pilot_verify = commands.add_parser("verify-pilot")
    pilot_verify.add_argument("root", type=Path)
    score = commands.add_parser("score")
    for name in ("packet", "annotations", "assessment", "output"):
        score.add_argument(f"--{name}", type=Path, required=True)
    for name in ("analysis", "plan", "review"):
        score.add_argument(f"--{name}", type=Path)
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
        elif args.command == "verify":
            manifest = verify_baseline(args.bundle, check_originals=args.check_originals)
            print(f"Verified {len(manifest.files)} files; semantic acceptance remains pending.")
        elif args.command == "prepare-private":
            paths = prepare_private(
                args.baseline,
                PrivateSelection.model_validate_json(args.selection.read_bytes()),
                args.output,
            )
            print(f"Prepared {len(paths)} private source packets; context review remains pending.")
        elif args.command in {"fetch-public", "prepare-public"}:
            recipe = PublicRecipe.model_validate_json(args.recipe.read_bytes())
            if args.command == "fetch-public":
                fetch_public(recipe, args.output)
                print(f"Verified {len(recipe.files)} pinned public files; no model calls.")
            else:
                paths = prepare_public(recipe, args.source_root, args.output)
                print(
                    f"Prepared {len(paths)} public source packets; context review remains pending."
                )
        elif args.command == "verify-packet":
            packet_manifest, specification = load_packet(args.packet)
            if args.annotations:
                validate_annotations(
                    args.packet, Annotations.model_validate_json(args.annotations.read_bytes())
                )
            print(f"Verified {packet_manifest.case_id}: {len(specification.blocks)} source blocks.")
        elif args.command in {"freeze-pilot", "verify-pilot"}:
            inventory = (
                freeze_pilot(args.root, annotations_file=args.annotations_file)
                if args.command == "freeze-pilot"
                else verify_pilot(args.root)
            )
            print(f"Verified pilot inventory: {len(inventory.files)} pinned files; no model calls.")
        elif args.command == "score":
            report = score_packet(
                args.packet,
                args.annotations,
                args.assessment,
                {
                    name: path
                    for name in ("analysis", "plan", "review")
                    if (path := getattr(args, name))
                },
            )
            output = require_ignored(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as stream:
                stream.write(_json_bytes(report))
            print(
                f"Wrote packet score to {output}; "
                f"semantic acceptance: {report['semantic_acceptance']}."
            )
    except ValidationError:
        parser.exit(1, "Evaluation snapshot schema validation failed.\n")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Evaluation snapshot failed: {error}\n")


if __name__ == "__main__":
    main()
