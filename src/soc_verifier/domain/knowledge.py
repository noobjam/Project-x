"""Versioned guidance, separate from specification requirements and evidence."""

import hashlib
from typing import Literal, Self

from pydantic import Field, model_validator

from soc_verifier.domain.models import Contract, NonEmpty


class KnowledgeEntry(Contract):
    id: str = Field(pattern=r"^(K|C|TB|E)[0-9]{2}$")
    title: NonEmpty
    status: Literal["proposed", "approved"]
    reviewer: str = ""
    source_path: NonEmpty
    text: str = Field(min_length=1, max_length=40_000)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def reviewed(self) -> Self:
        if self.status == "approved" and not self.reviewer.strip():
            raise ValueError("Approved knowledge requires a recorded reviewer")
        return self


class KnowledgeSnapshot(Contract):
    format: Literal["knowledge-snapshot-v1"] = "knowledge-snapshot-v1"
    allow_proposed: bool = False
    entries: list[KnowledgeEntry] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def valid_entries(self) -> Self:
        if len({entry.id for entry in self.entries}) != len(self.entries):
            raise ValueError("Duplicate knowledge IDs")
        for entry in self.entries:
            if hashlib.sha256(entry.text.encode()).hexdigest() != entry.sha256:
                raise ValueError("Knowledge content hash mismatch")
            if entry.status != "approved" and not self.allow_proposed:
                raise ValueError("Proposed knowledge requires explicit trial opt-in")
        return self
