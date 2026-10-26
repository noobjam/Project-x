import pytest

from soc_verifier.workflows.spec_to_plan.batching import (
    AnalysisBatch,
    evidence,
    merge_analyses,
    split_specification,
)


def test_chunks_are_bounded_ordered_and_complete(specification):
    blocks = [
        specification.blocks[0].model_copy(
            update={
                "id": f"P{index:05d}",
                "text": "A testable condition. " * 20,
                "section": "Reset" if index < 3 else "Boot",
            }
        )
        for index in range(7)
    ]
    spec = specification.model_copy(update={"blocks": blocks})
    chunks = split_specification(spec, 1000)
    assert len(chunks) > 1
    assert [block.id for chunk in chunks for block in chunk] == [block.id for block in blocks]
    assert all(
        sum(len(block.model_dump_json()) + 1 for block in chunk) + 2 <= 1000 for chunk in chunks
    )


def test_oversized_single_block_is_never_truncated(specification):
    spec = specification.model_copy(
        update={"blocks": [specification.blocks[0].model_copy(update={"text": "x" * 2000})]}
    )
    with pytest.raises(ValueError, match="exceeds the chunk limit"):
        split_specification(spec, 1000)


def test_merge_preserves_distinct_requirements_and_all_evidence(analysis):
    requirement = analysis.requirements[0]
    duplicate = requirement.model_copy(
        update={"id": "another-id", "source_ids": ["P00002"], "open_questions": ["Reset duration?"]}
    )
    conflict = requirement.model_copy(
        update={"id": "conflict", "statement": "Reset preserves pending interrupts."}
    )
    batches = [
        AnalysisBatch(requirements=[requirement], gaps=["gap"]),
        AnalysisBatch(requirements=[duplicate, conflict], gaps=["gap"]),
    ]
    merged = merge_analyses(batches)
    assert len(merged.requirements) == 2
    assert merged.requirements[0].source_ids == ["P00001", "P00002"]
    assert merged.requirements[0].open_questions == ["Reset duration?"]
    assert merged.gaps == ["gap"]
    assert merged.requirements[0].id == merge_analyses(batches[:1]).requirements[0].id


def test_table_header_is_supplied_from_original_evidence(specification):
    blocks = [
        specification.blocks[0].model_copy(
            update={
                "kind": "table_row",
                "id": f"T00001-R{index:04d}",
                "text": text,
            }
        )
        for index, text in enumerate(["Register | Reset", "IRQ0 | 0", "IRQ1 | 0"], start=1)
    ]
    supplied = evidence(specification.model_copy(update={"blocks": blocks}), {"T00001-R0003"})
    assert [item["id"] for item in supplied] == ["T00001-R0001", "T00001-R0003"]
