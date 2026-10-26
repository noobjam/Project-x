"""Deterministic evidence partitioning and lossless requirement assembly."""

import json
from hashlib import sha256

from soc_verifier.domain.models import (
    Contract,
    Requirement,
    SourceBlock,
    SpecAnalysis,
    Specification,
)


class AnalysisBatch(Contract):
    """A source chunk may contain no normative requirements (for example a TOC)."""

    requirements: list[Requirement]
    gaps: list[str]


def split_specification(spec: Specification, max_characters: int) -> list[list[SourceBlock]]:
    if max_characters < 1000:
        raise ValueError("Chunk character limit must be at least 1000")
    chunks: list[list[SourceBlock]] = []
    current: list[SourceBlock] = []
    size = 2
    for block in spec.blocks:
        length = len(block.model_dump_json()) + 1
        if length + 2 > max_characters:
            raise ValueError(
                f"Source block {block.id} exceeds the chunk limit; split it explicitly"
            )
        section_boundary = current and current[-1].section != block.section
        if current and (
            size + length > max_characters or (section_boundary and size >= max_characters // 2)
        ):
            chunks.append(current)
            current, size = [], 2
        current.append(block)
        size += length
    if current:
        chunks.append(current)
    return chunks


def merge_analyses(batches: list[AnalysisBatch]) -> SpecAnalysis:
    """Deduplicate exact statements only; never ask an LLM to compress away requirements."""
    requirements: dict[str, Requirement] = {}
    for batch in batches:
        for requirement in batch.requirements:
            key = json.dumps(
                [requirement.basis, requirement.feature, " ".join(requirement.statement.split())]
            )
            identifier = f"REQ-{sha256(key.encode()).hexdigest()[:16]}"
            existing = requirements.get(identifier)
            if existing is None:
                requirements[identifier] = requirement.model_copy(update={"id": identifier})
            else:
                requirements[identifier] = existing.model_copy(
                    update={
                        "source_ids": list(
                            dict.fromkeys([*existing.source_ids, *requirement.source_ids])
                        ),
                        "open_questions": list(
                            dict.fromkeys([*existing.open_questions, *requirement.open_questions])
                        ),
                        "rationale": "\n".join(
                            dict.fromkeys([existing.rationale, requirement.rationale])
                        ),
                    }
                )
    return SpecAnalysis(
        requirements=list(requirements.values()),
        gaps=list(dict.fromkeys(gap for batch in batches for gap in batch.gaps)),
    )


def requirement_index(analysis: SpecAnalysis) -> list[dict[str, object]]:
    return [
        {
            "id": item.id,
            "feature": item.feature,
            "statement": item.statement,
            "source_ids": item.source_ids,
        }
        for item in analysis.requirements
    ]


def evidence(spec: Specification, source_ids: set[str]) -> list[dict[str, str]]:
    """Include referenced blocks and real table headers, never invented context."""
    table_ids = {identifier.rsplit("-R", 1)[0] for identifier in source_ids if "-R" in identifier}
    headers: dict[str, str] = {}
    for block in spec.blocks:
        if block.kind == "table_row":
            headers.setdefault(block.id.rsplit("-R", 1)[0], block.id)
    selected = source_ids | {headers[table] for table in table_ids if table in headers}
    return [
        {"id": block.id, "section": block.section, "text": block.text}
        for block in spec.blocks
        if block.id in selected
    ]
