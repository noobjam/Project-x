"""Synthetic fixtures only. No proprietary source files or live network calls."""

import socket

import pytest

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
