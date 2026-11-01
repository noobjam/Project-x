import json
from hashlib import sha256

import httpx
import pytest
from pydantic import SecretStr
from tests.conftest import inventory_response
from tests.integration.test_agent_runtime import API, completion, knowledge_lookup

from soc_verifier.agents.runtime import AgentRuntime
from soc_verifier.domain.source_inventory import SourceInventory
from soc_verifier.evaluation.__main__ import main
from soc_verifier.evaluation.source_audit import (
    INPUT_FILES,
    load_audit_evaluation,
    prepare_audits,
    run_audits,
)
from soc_verifier.providers.budget import read_spending
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.accounting import project_accounting


@pytest.fixture
def control_pack(evaluation_repo, specification, passage_accounting_draft, knowledge_snapshot):
    root = evaluation_repo / "artifacts" / "controls"
    cases = []
    for identifier in ["C01", "C02", "C03"]:
        store = ArtifactStore(root / "inputs" / identifier)
        store.write("specification.json", specification)
        store.write("obligations.r000.json", passage_accounting_draft)
        analysis, accounting = project_accounting(store, "obligations.r000.json", "analysis.json")
        store.write("analysis.json", analysis)
        store.write("source-accounting.r000.json", accounting)
        cases.append(
            {
                "id": identifier,
                "input_directory": f"inputs/{identifier}",
                "files": {
                    name: sha256(store.path(name).read_bytes()).hexdigest()
                    for name in INPUT_FILES.values()
                },
            }
        )
    manifest = {
        "format": "source-audit-control-pack-v1",
        "controls": cases,
        "reference": {"path": "reference/answers.json"},
    }
    ArtifactStore(root).write("manifest.json", manifest)
    ArtifactStore(root / "reference").write("answers.json", {"answer": "SECRET_CONTROL_ANSWER"})
    knowledge = ArtifactStore(evaluation_repo / "artifacts").write("kb.json", knowledge_snapshot)
    digest = sha256((root / "manifest.json").read_bytes()).hexdigest()
    return root, digest, knowledge


def prepared(control_pack, evaluation_repo, **overrides):
    output = evaluation_repo / "artifacts" / "audits"
    settings = Settings(
        _env_file=None,
        model="test/model",
        provider="test-endpoint",
        max_output_tokens=256,
        max_revisions=0,
        source_accounting=True,
        **overrides,
    )
    evaluation = prepare_audits(*control_pack, output, settings)
    return ArtifactStore(output), evaluation


class Agents:
    def __init__(self, evaluation, responses):
        self.configuration = evaluation.configuration
        self.responses = iter(responses)
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        assert "SECRET_CONTROL_ANSWER" not in kwargs["context"]
        assert "reference/" not in kwargs["context"]
        if issubclass(kwargs["schema"], SourceInventory):
            return inventory_response(kwargs["context"])
        response = next(self.responses)
        if isinstance(response, BaseException):
            raise response
        return response


def test_prepare_excludes_answers_and_execution_reuses_every_completed_task(
    evaluation_repo, control_pack, clean_audit
):
    store, evaluation = prepared(control_pack, evaluation_repo)
    for path in store.root.iterdir():
        assert "SECRET_CONTROL_ANSWER" not in path.read_text()
        assert "answers.json" not in path.read_text()
    agents = Agents(evaluation, [clean_audit] * 3)
    result = run_audits(agents, store)
    assert result["status"] == "completed"
    assert result["semantic_acceptance"] == "unreviewed"
    assert [c["task"].inputs.stage for c in agents.calls] == [
        "audit-control.C01.inventory",
        "audit-control.C01.comparison",
        "audit-control.C02.inventory",
        "audit-control.C02.comparison",
        "audit-control.C03.inventory",
        "audit-control.C03.comparison",
    ]
    assert run_audits(Agents(evaluation, []), store) == result


@pytest.mark.parametrize("failure", [RuntimeError("provider failure"), KeyboardInterrupt()])
def test_failure_retains_all_cases_and_cannot_retry_implicitly(
    evaluation_repo, control_pack, clean_audit, failure
):
    store, evaluation = prepared(control_pack, evaluation_repo)
    agents = Agents(evaluation, [clean_audit, failure])
    result = run_audits(agents, store)
    assert result["status"] == "incomplete"
    assert [c["status"] for c in result["cases"]] == [
        "completed",
        "interrupted" if isinstance(failure, KeyboardInterrupt) else "failed",
        "not_run",
    ]
    assert len(agents.calls) == 4
    assert run_audits(Agents(evaluation, []), store) == result


def test_killed_process_is_interrupted_without_repeating_inference(evaluation_repo, control_pack):
    store, evaluation = prepared(control_pack, evaluation_repo)
    with pytest.raises(SystemExit):
        run_audits(Agents(evaluation, [SystemExit(1)]), store)
    result = run_audits(Agents(evaluation, []), store)
    assert [c["status"] for c in result["cases"]] == ["interrupted", "not_run", "not_run"]


@pytest.mark.parametrize("target", ["C01.result.json", "evaluation.result.json"])
def test_case_results_cannot_claim_false_completion(evaluation_repo, control_pack, target):
    store, evaluation = prepared(control_pack, evaluation_repo)
    run_audits(Agents(evaluation, [RuntimeError("failed")]), store)
    record = store.read(target)
    if target == "C01.result.json":
        record["status"] = "completed"
    else:
        record["cases"] = []
    store.path(target).write_text(json.dumps(record))
    with pytest.raises(ValueError):
        run_audits(Agents(evaluation, []), store)


@pytest.mark.parametrize("target", ["C03.analysis.json", "knowledge.json", "evaluation.json"])
def test_all_snapshots_are_checked_before_any_inference(evaluation_repo, control_pack, target):
    store, evaluation = prepared(control_pack, evaluation_repo)
    store.path(target).write_text("{}")
    agents = Agents(evaluation, [])
    with pytest.raises(ValueError, match="changed"):
        run_audits(agents, store)
    assert not agents.calls


@pytest.mark.parametrize("defect", ["manifest", "source", "directory", "file", "duplicate"])
def test_bad_pack_fails_before_creating_executable_output(evaluation_repo, control_pack, defect):
    root, digest, knowledge = control_pack
    manifest = json.loads((root / "manifest.json").read_bytes())
    if defect == "manifest":
        digest = "0" * 64
    elif defect == "source":
        (root / "inputs/C03/analysis.json").write_text("{}")
    else:
        if defect == "directory":
            manifest["controls"][0]["input_directory"] = "reference"
        elif defect == "file":
            manifest["controls"][0]["files"]["../reference/answers.json"] = "0" * 64
        else:
            manifest["controls"].append(manifest["controls"][0])
        (root / "manifest.json").write_text(json.dumps(manifest))
        digest = sha256((root / "manifest.json").read_bytes()).hexdigest()
    output = evaluation_repo / "artifacts/audits"
    with pytest.raises(ValueError):
        prepare_audits(root, digest, knowledge, output, Settings(_env_file=None))
    assert not output.exists()


def test_real_sdk_cases_share_one_budget_and_keep_unknown_charges(
    evaluation_repo, control_pack, clean_audit, source_inventory
):
    store, evaluation = prepared(control_pack, evaluation_repo, max_model_calls=7)

    def respond(payload):
        messages = [m for m in payload["messages"] if m["role"] == "tool"]
        if not messages:
            return knowledge_lookup("search_knowledge", {"query": "reset"})
        if len(messages) == 1:
            return knowledge_lookup("get_knowledge_entries", {"ids": ["K01"]})
        name = payload["response_format"]["json_schema"]["schema"]["title"]
        output = source_inventory if name == "SourceInventory" else clean_audit
        return completion({"content": output.model_dump_json()})

    api = API(respond)
    settings = Settings(
        _env_file=None, openrouter_api_key=SecretStr("test-only"), **evaluation.configuration
    )
    with httpx.Client(transport=httpx.MockTransport(api)) as client:
        runtime = AgentRuntime(settings, client, artifacts=store)
        result = run_audits(runtime, store)
    assert [c["status"] for c in result["cases"]] == ["completed", "budget_exhausted", "not_run"]
    assert len(api.requests) == 7 and read_spending(store).attempts == 7
    with httpx.Client(transport=httpx.MockTransport(api)) as client:
        assert run_audits(AgentRuntime(settings, client, artifacts=store), store) == result
    assert len(api.requests) == 7
    assert result["spending_at_completion"]["reported_usd"] == "0.0007"


def test_sdk_network_failure_keeps_reservation_and_remaining_denominator(
    evaluation_repo, control_pack
):
    store, evaluation = prepared(control_pack, evaluation_repo)

    def respond(_):
        raise httpx.ReadTimeout("Synthetic uncertain charge")

    api = API(respond)
    settings = Settings(
        _env_file=None, openrouter_api_key=SecretStr("test-only"), **evaluation.configuration
    )
    with httpx.Client(transport=httpx.MockTransport(api)) as client:
        result = run_audits(AgentRuntime(settings, client, artifacts=store), store)
    assert result["spending_at_completion"]["unsettled_calls"] == 1
    assert float(result["spending_at_completion"]["reserved_usd"]) > 0
    assert result["spending_at_completion"]["reported_usd"] == "0"
    assert [c["status"] for c in result["cases"]] == ["failed", "not_run", "not_run"]


def test_cli_preparation_and_status_are_offline(evaluation_repo, control_pack, monkeypatch, capsys):
    root, digest, knowledge = control_pack
    output = evaluation_repo / "artifacts/audits"
    monkeypatch.setattr(
        "sys.argv",
        [
            "evaluation",
            "prepare-audits",
            "--bundle",
            str(root),
            "--manifest-sha256",
            digest,
            "--knowledge-snapshot",
            str(knowledge),
            "--output",
            str(output),
            "--model",
            "test/model",
            "--provider",
            "test-endpoint",
            "--max-cost-usd",
            "0.20",
            "--max-model-calls",
            "48",
        ],
    )
    main()
    assert "no model calls" in capsys.readouterr().out
    assert load_audit_evaluation(ArtifactStore(output)).configuration["max_model_calls"] == 48
    monkeypatch.setattr("sys.argv", ["evaluation", "audit-status", str(output)])
    main()
    assert json.loads(capsys.readouterr().out)["reported_usd"] == "0"
