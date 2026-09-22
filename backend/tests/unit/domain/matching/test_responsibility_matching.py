from domain.cv.entities import Experience
from domain.documents.enums import ExtractionMethod
from domain.documents.evidence import Evidence
from domain.matching.enums import MatchSignal, RequirementStatus
from domain.matching.responsibility_matching import evaluate_responsibility, lexical_overlap


def _experience(description: str) -> Experience:
    return Experience(
        title="Engineer",
        company="Acme",
        start_date_raw=None,
        end_date_raw=None,
        description=description,
        evidence=Evidence(
            source_document_id="doc-1",
            text=description,
            extraction_method=ExtractionMethod.RULE,
            confidence=0.9,
        ),
    )


class TestLexicalOverlap:
    def test_identical_text_has_full_overlap(self):
        assert lexical_overlap("build rest apis", "build rest apis") == 1.0

    def test_unrelated_text_has_no_overlap(self):
        assert lexical_overlap("build rest apis", "paint the fence") == 0.0


class TestEvaluateResponsibility:
    def test_lexical_overlap_yields_partial_match_with_evidence(self):
        experiences = (_experience("Built REST APIs using Django and PostgreSQL"),)
        evaluation = evaluate_responsibility("Design and maintain REST APIs", experiences)

        assert evaluation.match_signal == MatchSignal.PARTIAL_MATCH
        assert evaluation.status == RequirementStatus.PARTIALLY_MET
        assert len(evaluation.evidence) == 1

    def test_semantic_only_match_carries_no_structural_evidence(self):
        experiences = (_experience("Completely unrelated wording"),)
        evaluation = evaluate_responsibility(
            "Design and maintain REST APIs",
            experiences,
            semantic_score=0.9,
            semantic_match_experience=experiences[0],
        )

        assert evaluation.match_signal == MatchSignal.SEMANTIC_MATCH
        assert evaluation.evidence == ()

    def test_no_overlap_and_no_semantic_score_is_no_evidence(self):
        experiences = (_experience("Completely unrelated wording"),)
        evaluation = evaluate_responsibility("Design and maintain REST APIs", experiences)

        assert evaluation.match_signal == MatchSignal.NO_EVIDENCE

    def test_never_produces_an_exact_match(self):
        # Responsibility alignment is supporting evidence only - it must
        # never claim the same certainty as a skill exact match.
        experiences = (_experience("Design and maintain REST APIs"),)
        evaluation = evaluate_responsibility("Design and maintain REST APIs", experiences)

        assert evaluation.match_signal != MatchSignal.EXACT_MATCH
