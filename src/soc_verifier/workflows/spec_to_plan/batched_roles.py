"""Resumable bounded calls within the analyst, planner, and reviewer roles."""

import json
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from soc_verifier.domain.models import (
    PlanReview,
    Requirement,
    SourceBlock,
    SpecAnalysis,
    Specification,
    VerificationPlan,
    validate_sources,
    validate_traceability,
)
from soc_verifier.llm.base import StructuredLLM
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan import prompts
from soc_verifier.workflows.spec_to_plan.batching import (
    AnalysisBatch,
    evidence,
    merge_analyses,
    requirement_index,
    split_specification,
)
from soc_verifier.workflows.spec_to_plan.bounded import bounded_call
from soc_verifier.workflows.spec_to_plan.reviewing import generate_review, validate_review

logger = logging.getLogger(__name__)


def _map[T](function: Callable[[int], T], count: int, workers: int) -> list[T]:
    if workers == 1:
        return [function(index) for index in range(count)]
    executor = ThreadPoolExecutor(max_workers=workers)
    try:
        futures = {executor.submit(function, index): index for index in range(count)}
        results = {futures[future]: future.result() for future in as_completed(futures)}
        return [results[index] for index in range(count)]
    finally:
        # On failure keep completed artifacts; cancel queued calls, not in-flight requests.
        executor.shutdown(wait=True, cancel_futures=True)


def analyze_batches(
    llm: StructuredLLM,
    artifacts: ArtifactStore,
    spec: Specification,
    *,
    revision: int,
    chunk_characters: int,
    workers: int,
    review: dict[str, object] | None,
) -> SpecAnalysis:
    chunks = split_specification(spec, chunk_characters)
    artifacts.write(
        f"chunks.r{revision:03d}.json",
        {
            "chunks": [
                {"id": index, "source_ids": [block.id for block in chunk]}
                for index, chunk in enumerate(chunks)
            ],
        },
    )

    def analyze(index: int) -> AnalysisBatch:
        name = f"analysis.r{revision:03d}.chunk{index:04d}.json"
        logger.info("stage=analysis revision=%s batch=%s/%s", revision, index + 1, len(chunks))

        def generate(blocks: list[SourceBlock]) -> AnalysisBatch:
            supplied = evidence(spec, {block.id for block in blocks})
            previous = f"analysis.r{revision - 1:03d}.chunk{index:04d}.json"
            context: dict[str, object] = {
                "evidence": supplied,
                "extraction_warnings": spec.extraction_warnings,
                "previous_analysis": artifacts.read(previous)
                if revision and artifacts.exists(previous)
                else None,
                "review": review,
            }
            known = {item["id"] for item in supplied}
            # One explicit correction for fabricated citations; never silently map
            # an invalid ID or accept an unsupported claim. Both calls are budgeted.
            for correction in range(2):
                result = llm.generate(
                    instruction=prompts.ANALYZE_CHUNK,
                    context=json.dumps(context),
                    schema=AnalysisBatch,
                )
                unknown = {
                    source for item in result.requirements for source in item.source_ids
                } - known
                if not unknown:
                    return result
                if correction == 0:
                    logger.warning(
                        "stage=analysis citation_correction=1 chunk=%s unknown=%s",
                        index,
                        sorted(unknown),
                    )
                    context["previous_analysis"] = result.model_dump(mode="json")
                    context["validation_feedback"] = {
                        "unknown_source_ids": sorted(unknown),
                        "instruction": (
                            "Correct citations using only the supplied evidence. Remove claims "
                            "whose support is absent; record uncertainty as a gap instead. "
                            "Do not guess IDs or infer missing rows from neighboring registers. "
                            "Return the complete corrected analysis for this chunk."
                        ),
                    }
            raise ValueError(
                f"Chunk {index} analysis cites evidence not supplied to that chunk after "
                f"one correction: {sorted(unknown)}"
            )

        result = bounded_call(
            artifacts,
            name.removesuffix(".json"),
            chunks[index],
            AnalysisBatch,
            generate,
            lambda left, right: AnalysisBatch(
                requirements=[*left.requirements, *right.requirements],
                gaps=list(dict.fromkeys([*left.gaps, *right.gaps])),
            ),
        )
        supplied = evidence(spec, {block.id for block in chunks[index]})
        known = {item["id"] for item in supplied}
        if any(set(item.source_ids) - known for item in result.requirements):
            raise ValueError("Chunk analysis cites evidence not supplied to that chunk")
        artifacts.write(name, result)
        return result

    batches = _map(analyze, len(chunks), workers)
    merged = merge_analyses(batches)
    # This pass adds interactions; it cannot delete or summarize away local requirements.
    name = f"analysis.r{revision:03d}.system.json"
    logger.info(
        "stage=system_analysis revision=%s requirements=%s", revision, len(merged.requirements)
    )
    if artifacts.exists(name):
        system = AnalysisBatch.model_validate(artifacts.read(name))
    else:
        system = llm.generate(
            instruction=prompts.ANALYZE_SYSTEM,
            context=json.dumps(
                {
                    "specification": spec.model_dump(mode="json"),
                    "requirement_index": requirement_index(merged),
                    "review": review,
                }
            ),
            schema=AnalysisBatch,
        )
    for requirement in system.requirements:
        validate_sources(SpecAnalysis(requirements=[requirement], gaps=[]), spec)
    artifacts.write(name, system)
    return merge_analyses([*batches, system])


def plan_batches(
    llm: StructuredLLM,
    artifacts: ArtifactStore,
    spec: Specification,
    analysis: SpecAnalysis,
    *,
    revision: int,
    batch_size: int,
    workers: int,
    review: dict[str, object] | None,
) -> VerificationPlan:
    groups = [
        analysis.requirements[start : start + batch_size]
        for start in range(0, len(analysis.requirements), batch_size)
    ]
    index = requirement_index(analysis)

    def plan(number: int) -> VerificationPlan:
        name = f"plan.r{revision:03d}.batch{number:04d}.json"
        logger.info("stage=planning revision=%s batch=%s/%s", revision, number + 1, len(groups))

        def generate(requirements: list[Requirement]) -> VerificationPlan:
            local = SpecAnalysis(requirements=requirements, gaps=analysis.gaps)
            previous = f"plan.r{revision - 1:03d}.batch{number:04d}.json"
            context: dict[str, object] = {
                "assigned_requirements": local.model_dump(mode="json"),
                "system_requirement_index": index,
                "evidence": evidence(
                    spec, {source for item in local.requirements for source in item.source_ids}
                ),
                "previous_plan": artifacts.read(previous)
                if revision and artifacts.exists(previous)
                else None,
                "review": review,
            }
            known = {item.id for item in requirements}
            for correction in range(2):
                result = llm.generate(
                    instruction=prompts.PLAN_BATCH,
                    context=json.dumps(context),
                    schema=VerificationPlan,
                )
                try:
                    validate_traceability(result, local)
                except ValueError:
                    if correction:
                        raise ValueError(
                            "Plan batch has invalid requirement coverage after one correction"
                        ) from None
                    covered = {
                        identifier for item in result.items for identifier in item.requirement_ids
                    }
                    logger.warning("stage=planning traceability_correction=1 batch=%s", number)
                    context["previous_plan"] = result.model_dump(mode="json")
                    context["validation_feedback"] = {
                        "missing_requirement_ids": sorted(known - covered),
                        "unknown_requirement_ids": sorted(covered - known),
                        "instruction": (
                            "Return the complete corrected plan for every assigned requirement. "
                            "Reference only assigned requirement IDs. Preserve grounded checks; "
                            "if a requirement is ambiguous or unsupported, expose that in open "
                            "questions and an inspection item instead of silently omitting it "
                            "or inventing behavior."
                        ),
                    }
                else:
                    return result
            raise AssertionError("Unreachable plan correction state")

        result = bounded_call(
            artifacts,
            name.removesuffix(".json"),
            groups[number],
            VerificationPlan,
            generate,
            lambda left, right: VerificationPlan(
                items=[
                    item.model_copy(update={"id": f"{side}:{item.id}"})
                    for side, part in [("a", left), ("b", right)]
                    for item in part.items
                ],
            ),
        )
        validate_traceability(result, SpecAnalysis(requirements=groups[number], gaps=analysis.gaps))
        artifacts.write(name, result)
        return result

    plans = _map(plan, len(groups), workers)
    # Batch-local IDs can collide. Namespace them deterministically before review/export.
    return VerificationPlan(
        items=[
            item.model_copy(update={"id": f"B{number:04d}:{item.id}"})
            for number, result in enumerate(plans)
            for item in result.items
        ]
    )


def review_batches(
    llm: StructuredLLM,
    artifacts: ArtifactStore,
    spec: Specification,
    analysis: SpecAnalysis,
    plan: VerificationPlan,
    *,
    revision: int,
    chunk_characters: int,
    workers: int,
) -> PlanReview:
    chunks = split_specification(spec, chunk_characters)
    index = requirement_index(analysis)
    known_items = {item.id for item in plan.items}

    def review(number: int) -> PlanReview:
        name = f"review.r{revision:03d}.chunk{number:04d}.json"
        logger.info("stage=review revision=%s batch=%s/%s", revision, number + 1, len(chunks))

        def generate(blocks: list[SourceBlock]) -> PlanReview:
            source_ids = {block.id for block in blocks}
            local = [item for item in analysis.requirements if set(item.source_ids) & source_ids]
            local_ids = {item.id for item in local}
            local_plan = [item for item in plan.items if set(item.requirement_ids) & local_ids]
            result = generate_review(
                llm,
                instruction=prompts.REVIEW_CHUNK,
                context={
                    "evidence": evidence(spec, source_ids),
                    "system_requirement_index": index,
                    "requirements": [item.model_dump(mode="json") for item in local],
                    "plan": [item.model_dump(mode="json") for item in local_plan],
                },
                known_items={item.id for item in local_plan},
            )
            validate_review(result, known_items)
            return result

        result = bounded_call(
            artifacts,
            name.removesuffix(".json"),
            chunks[number],
            PlanReview,
            generate,
            lambda left, right: PlanReview(
                findings=[*left.findings, *right.findings],
            ),
        )
        validate_review(result, known_items)
        artifacts.write(name, result)
        return result

    reviews = _map(review, len(chunks), workers)
    name = f"review.r{revision:03d}.system.json"
    logger.info("stage=system_review revision=%s", revision)
    if artifacts.exists(name):
        system = PlanReview.model_validate(artifacts.read(name))
    else:
        system = generate_review(
            llm,
            instruction=prompts.REVIEW_SYSTEM,
            context={
                "specification": spec.model_dump(mode="json"),
                "requirement_index": index,
                "plan_index": [
                    {
                        "id": item.id,
                        "requirement_ids": item.requirement_ids,
                        "objective": item.objective,
                        "expected_results": item.expected_results,
                    }
                    for item in plan.items
                ],
            },
            known_items=known_items,
        )
    validate_review(system, known_items)
    artifacts.write(name, system)
    unique = {
        finding.model_dump_json(): finding
        for result in [*reviews, system]
        for finding in result.findings
    }
    return PlanReview(findings=list(unique.values()))
