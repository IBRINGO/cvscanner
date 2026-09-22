"""Semantic representation abstraction (Phase 3 sections 23-24).

A `SemanticRepresentation` records that some text belonging to a
CandidateProfile/JobProfile/Experience/JobRequirement/Skill was embedded
by a specific model/version - it is the unit that
infrastructure/embeddings/ and a future semantic search layer operate on.
It never asserts a match to anything; it is a foundation, not a matching
engine (section 28).
"""
from dataclasses import dataclass, field

from domain.semantics.enums import SemanticEntityType


@dataclass(frozen=True)
class SemanticRepresentation:
    entity_type: SemanticEntityType
    entity_id: str
    text: str
    embedding: tuple[float, ...]
    model: str
    dimensions: int
    version: str
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.embedding) != self.dimensions:
            raise ValueError(
                f"embedding has {len(self.embedding)} components, expected {self.dimensions}"
            )
