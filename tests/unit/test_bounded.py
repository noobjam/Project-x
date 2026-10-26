import pytest

from soc_verifier.agents.base import ModelResponseError, OutputLimitError
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.batching import AnalysisBatch
from soc_verifier.workflows.spec_to_plan.bounded import bounded_call


def combine(left, right):
    return AnalysisBatch(
        requirements=[*left.requirements, *right.requirements], gaps=[*left.gaps, *right.gaps]
    )


def test_output_overflow_is_split_without_losing_items(tmp_path):
    calls = []

    def generate(items):
        calls.append(items)
        if len(items) > 1:
            raise OutputLimitError("limit")
        return AnalysisBatch(requirements=[], gaps=items)

    artifacts = ArtifactStore(tmp_path)
    result = bounded_call(artifacts, "batch", ["one", "two"], AnalysisBatch, generate, combine)
    assert result.gaps == ["one", "two"]
    assert calls == [["one", "two"], ["one"], ["two"]]
    assert artifacts.exists("batch.split.json")


def test_split_and_completed_children_survive_restart(tmp_path):
    artifacts = ArtifactStore(tmp_path)

    def first(items):
        if len(items) > 1:
            raise OutputLimitError("limit")
        if items == ["two"]:
            raise RuntimeError("network interrupted")
        return AnalysisBatch(requirements=[], gaps=items)

    with pytest.raises(RuntimeError, match="network interrupted"):
        bounded_call(artifacts, "batch", ["one", "two"], AnalysisBatch, first, combine)
    calls = []

    def resumed(items):
        calls.append(items)
        return AnalysisBatch(requirements=[], gaps=items)

    result = bounded_call(artifacts, "batch", ["one", "two"], AnalysisBatch, resumed, combine)
    assert calls == [["two"]]
    assert result.gaps == ["one", "two"]


def test_non_overflow_errors_are_not_retried(tmp_path):
    artifacts = ArtifactStore(tmp_path)

    def refused(items):
        raise ModelResponseError("refused")

    with pytest.raises(ModelResponseError, match="refused"):
        bounded_call(artifacts, "batch", [1, 2], AnalysisBatch, refused, combine)
    assert not artifacts.exists("batch.split.json")


def test_single_item_overflow_stops_instead_of_looping(tmp_path):
    artifacts = ArtifactStore(tmp_path)

    def overflow(items):
        raise OutputLimitError("limit")

    with pytest.raises(OutputLimitError):
        bounded_call(artifacts, "batch", [1], AnalysisBatch, overflow, combine)
    assert not artifacts.exists("batch.split.json")
