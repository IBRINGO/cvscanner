from domain.documents.enums import ExtractionMethod
from domain.documents.evidence import Evidence
from domain.job.entities import JobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from domain.matching.candidate_index import CandidateSkillSignal
from domain.matching.enums import MatchSignal, MatchStrength, RequirementPriority, RequirementStatus
from domain.matching.skill_matching import evaluate_skill_requirement
from domain.matching.weights import SemanticMatchingConfig
from domain.skills.taxonomy import SEED_SKILLS

ALL_SKILLS = list(SEED_SKILLS)


def _skill(name: str):
    return next(s for s in ALL_SKILLS if s.canonical_name == name)


def _requirement(
    skill_name: str | None, raw_text: str, importance=RequirementImportance.REQUIRED
) -> JobRequirement:
    return JobRequirement(
        requirement_type=RequirementType.REQUIRED_SKILL,
        importance=importance,
        raw_text=raw_text,
        skill=_skill(skill_name) if skill_name else None,
    )


def _signal(
    canonical_name: str, source_type="SKILL_SECTION", raw_text=None, source_label=None
) -> CandidateSkillSignal:
    return CandidateSkillSignal(
        canonical_name=canonical_name,
        source_type=source_type,
        evidence=Evidence(
            source_document_id="doc-1", text=raw_text or canonical_name,
            extraction_method=ExtractionMethod.RULE, confidence=0.9,
        ),
        source_label=source_label,
        raw_text=raw_text,
    )


class TestExactAndAliasMatch:
    def test_exact_canonical_match(self):
        requirement = _requirement("Django", "Django")
        index = {"Django": [_signal("Django", raw_text="Django")]}

        evaluation = evaluate_skill_requirement(requirement, index, ALL_SKILLS)

        assert evaluation.match_signal == MatchSignal.EXACT_MATCH
        assert evaluation.match_strength == MatchStrength.STRONG
        assert evaluation.status == RequirementStatus.MET
        assert evaluation.priority == RequirementPriority.MANDATORY
        assert evaluation.score == 1.0
        assert len(evaluation.evidence) == 1

    def test_candidate_alias_surface_form_is_alias_match(self):
        requirement = _requirement("PostgreSQL", "PostgreSQL")
        index = {"PostgreSQL": [_signal("PostgreSQL", raw_text="Postgres")]}

        evaluation = evaluate_skill_requirement(requirement, index, ALL_SKILLS)

        assert evaluation.match_signal == MatchSignal.ALIAS_MATCH
        assert evaluation.match_strength == MatchStrength.STRONG  # alias is not a weaker claim

    def test_requirement_alias_surface_form_is_alias_match(self):
        requirement = _requirement("JavaScript", "JS")
        index = {"JavaScript": [_signal("JavaScript", raw_text="JavaScript")]}

        evaluation = evaluate_skill_requirement(requirement, index, ALL_SKILLS)

        assert evaluation.match_signal == MatchSignal.ALIAS_MATCH


class TestOntologyMatch:
    def test_django_requirement_matched_by_related_drf(self):
        requirement = _requirement("Django", "Django")
        index = {"Django REST Framework": [_signal("Django REST Framework")]}

        evaluation = evaluate_skill_requirement(requirement, index, ALL_SKILLS)

        assert evaluation.match_signal == MatchSignal.RELATED_MATCH
        assert evaluation.match_strength == MatchStrength.PARTIAL
        assert evaluation.matched_skill == "Django REST Framework"
        assert evaluation.status == RequirementStatus.PARTIALLY_MET

    def test_kubernetes_requirement_partially_matched_by_docker(self):
        requirement = _requirement("Kubernetes", "Kubernetes")
        index = {"Docker": [_signal("Docker")]}

        evaluation = evaluate_skill_requirement(requirement, index, ALL_SKILLS)

        assert evaluation.match_signal == MatchSignal.RELATED_MATCH
        assert evaluation.match_strength == MatchStrength.PARTIAL
        # Never claim an exact match for a related-but-distinct skill.
        assert evaluation.match_signal != MatchSignal.EXACT_MATCH

    def test_related_match_never_equated_with_exact(self):
        requirement = _requirement("Python", "Python")
        # Candidate only has Django, which is related to (not equal to) Python.
        index = {"Django": [_signal("Django")]}

        evaluation = evaluate_skill_requirement(requirement, index, ALL_SKILLS)

        assert evaluation.match_signal == MatchSignal.RELATED_MATCH
        assert evaluation.matched_skill == "Django"


class TestSemanticMatch:
    def test_semantic_score_above_partial_threshold_yields_semantic_match(self):
        requirement = _requirement("Rust", "Rust")
        evaluation = evaluate_skill_requirement(
            requirement, {}, ALL_SKILLS, semantic_score=0.75, semantic_config=SemanticMatchingConfig()
        )

        assert evaluation.match_signal == MatchSignal.SEMANTIC_MATCH
        assert evaluation.match_strength == MatchStrength.PARTIAL
        assert evaluation.evidence == ()  # semantic alone carries no structural evidence

    def test_semantic_score_below_threshold_is_still_no_evidence(self):
        requirement = _requirement("Rust", "Rust")
        evaluation = evaluate_skill_requirement(requirement, {}, ALL_SKILLS, semantic_score=0.2)

        assert evaluation.match_signal == MatchSignal.NO_EVIDENCE

    def test_semantic_never_used_when_exact_match_exists(self):
        requirement = _requirement("Django", "Django")
        index = {"Django": [_signal("Django")]}
        evaluation = evaluate_skill_requirement(requirement, index, ALL_SKILLS, semantic_score=0.99)

        assert evaluation.match_signal == MatchSignal.EXACT_MATCH


class TestNoEvidence:
    def test_missing_skill_with_no_related_evidence(self):
        requirement = _requirement("Kubernetes", "Kubernetes")
        evaluation = evaluate_skill_requirement(requirement, {}, ALL_SKILLS)

        assert evaluation.match_signal == MatchSignal.NO_EVIDENCE
        assert evaluation.match_strength == MatchStrength.NONE
        assert evaluation.status == RequirementStatus.NOT_MET
        assert evaluation.score == 0.0

    def test_preferred_requirement_keeps_preferred_priority(self):
        requirement = _requirement("Kubernetes", "Kubernetes", importance=RequirementImportance.PREFERRED)
        evaluation = evaluate_skill_requirement(requirement, {}, ALL_SKILLS)

        assert evaluation.priority == RequirementPriority.PREFERRED


class TestUnresolvedRequirement:
    def test_unresolved_requirement_falls_back_to_textual_overlap(self):
        requirement = _requirement(None, "SomeInternalTool")
        index = {"SomeInternalToolkit": [_signal("SomeInternalToolkit")]}

        evaluation = evaluate_skill_requirement(requirement, index, ALL_SKILLS)

        assert evaluation.match_signal == MatchSignal.PARTIAL_MATCH

    def test_unresolved_requirement_with_no_overlap_is_no_evidence(self):
        requirement = _requirement(None, "SomeInternalTool")
        evaluation = evaluate_skill_requirement(requirement, {}, ALL_SKILLS)

        assert evaluation.match_signal == MatchSignal.NO_EVIDENCE
