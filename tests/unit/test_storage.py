import pytest

from soc_verifier.storage.artifacts import ArtifactStore


def test_immutable_idempotent_artifacts(tmp_path):
    store = ArtifactStore(tmp_path)
    store.write("plan.json", {"version": 1})
    store.write("plan.json", {"version": 1})
    with pytest.raises(FileExistsError, match="Refusing"):
        store.write("plan.json", {"version": 2})
    assert store.read("plan.json") == {"version": 1}
    assert [path.name for path in tmp_path.iterdir()] == ["plan.json"]


@pytest.mark.parametrize("name", ["../plan.json", "/tmp/plan.json", "", ".", ".."])
def test_artifact_names_cannot_escape_store(tmp_path, name):
    with pytest.raises(ValueError):
        ArtifactStore(tmp_path).write(name, {})
