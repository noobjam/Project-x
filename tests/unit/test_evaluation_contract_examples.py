import json
from hashlib import sha256
from pathlib import Path


def test_source_spans_preserve_unicode_newlines_and_repeated_text():
    root = Path(__file__).parents[1] / "fixtures" / "evaluation"
    examples = json.loads((root / "contract-examples.json").read_text())
    source = json.loads((root / "source.json").read_text())
    block = source["blocks"][0]
    for span in examples["spans"]:
        assert span["document_id"] == source["sha256"]
        assert span["block_id"] == block["id"]
        assert span["text_sha256"] == sha256(block["text"].encode()).hexdigest()
        assert block["text"][span["start"] : span["end"]] == span["expected_text"]
    assert len(block["text"].casefold()) != len(block["text"])
    assert len(block["text"].encode()) != len(block["text"])


def test_task_fingerprint_example_binds_exact_source_and_effective_inputs():
    root = Path(__file__).parents[1] / "fixtures" / "evaluation"
    example = json.loads((root / "contract-examples.json").read_text())["task"]
    payload = example["fingerprint_payload"]
    assert payload["inputs"][0]["sha256"] == sha256((root / "source.json").read_bytes()).hexdigest()
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    assert sha256(canonical.encode()).hexdigest() == example["input_fingerprint"]
    assert payload["assigned_ids"] == ["P00001"]
    assert "task_id" not in payload
    assert "attempt" not in payload
