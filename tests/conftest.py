"""Synthetic fixtures only. No proprietary source files or live network calls."""

import hashlib
import json
import socket

import pytest

from soc_verifier.domain.accounting import AccountingDraft, DraftObligation, SourceQuote
from soc_verifier.domain.knowledge import KnowledgeEntry, KnowledgeSnapshot
from soc_verifier.domain.models import (
    PlanReview,
    Requirement,
    SourceBlock,
    SpecAnalysis,
    Specification,
    VerificationItem,
    VerificationPlan,
)


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Tests must not access the network")

    monkeypatch.setattr(socket.socket, "connect", denied)


@pytest.fixture
def specification():
    return Specification(
        document_name="synthetic.docx",
        sha256="a" * 64,
        blocks=[
            SourceBlock(
                id="P00001",
                kind="paragraph",
                section="Reset",
                locator="word/document.xml/body/*[1]",
                text="System reset clears pending interrupts in the interrupt controller.",
            )
        ],
        extraction_warnings=[],
    )


@pytest.fixture
def analysis():
    return SpecAnalysis(
        requirements=[
            Requirement(
                id="REQ-RST-001",
                statement="System reset clears pending interrupts.",
                feature="Reset",
                basis="explicit",
                source_ids=["P00001"],
                rationale="Directly stated",
                open_questions=[],
            )
        ],
        gaps=[],
    )


@pytest.fixture
def accounting_draft(specification, analysis):
    requirement = analysis.requirements[0]
    return AccountingDraft(
        obligations=[
            DraftObligation(
                **requirement.model_dump(exclude={"source_ids"}),
                conditions=["System reset is asserted"],
                constraints=[],
                exceptions=[],
                evidence=[
                    SourceQuote(block_id="P00001", quote=specification.blocks[0].text, occurrence=0)
                ],
            )
        ],
        dispositions=[],
        gaps=[],
    )


@pytest.fixture
def verification_plan():
    return VerificationPlan(
        items=[
            VerificationItem(
                id="VPLAN-RST-001",
                requirement_ids=["REQ-RST-001"],
                feature="Reset",
                objective="Check pending interrupts are cleared by system reset.",
                method="simulation",
                preconditions=["At least one interrupt is pending"],
                stimulus=["Apply system reset"],
                expected_results=["All pending bits read zero after reset"],
                coverage_intent=["Reset with pending interrupts"],
                environment_needs=["Reset driver", "Register access"],
                priority="high",
                open_questions=[],
            )
        ]
    )


@pytest.fixture
def clean_review():
    return PlanReview(findings=[])


@pytest.fixture
def knowledge_snapshot():
    text = (
        "## K01 — Reset methodology\nCheck reset exclusions; derive timing from the specification."
    )
    return KnowledgeSnapshot(
        allow_proposed=True,
        entries=[
            KnowledgeEntry(
                id="K01",
                title="Reset methodology",
                status="proposed",
                source_path="patterns.md",
                text=text,
                sha256=hashlib.sha256(text.encode()).hexdigest(),
            )
        ],
    )


@pytest.fixture
def knowledge_catalog(tmp_path, knowledge_snapshot):
    root = tmp_path / "knowledge"
    root.mkdir()
    entry = knowledge_snapshot.entries[0]
    (root / entry.source_path).write_text(entry.text + "\n", encoding="utf-8")
    catalog = root / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "format": "knowledge-catalog-v1",
                "entries": [
                    {
                        "id": entry.id,
                        "file": entry.source_path,
                        "status": entry.status,
                        "reviewer": "",
                        "sha256": entry.sha256,
                    }
                ],
            }
        )
    )
    return catalog
