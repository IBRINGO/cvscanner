"""Executes a TailoringPlan (Phase 5 sections 19-26, 30-31, 57, 73).

PLANNING -> GENERATING -> VALIDATING -> COMPLETED/FAILED. Every proposed
section is generated (application/tailoring/generation.py) and then
independently validated by the Truth Layer
(domain/truth/claim_validation.py) regardless of which mode produced it
- a rejected proposal keeps the original text and is reported as a
rejected change, never silently dropped (section 57). The tailored
profile is then re-scored through application/matching/scoring.py's
`ProfileScorer` - the exact same code path Phase 4's RunAnalysis uses,
never a manually adjusted number (section 73).

    tailoring_repository needs: get_plan, get_analysis_document_pair, mark_status, mark_failed, save_result
    candidate_profile_repository needs: get(document_id) -> CandidateProfile | None
    job_profile_repository needs: get(document_id) -> JobProfile | None
    skill_repository needs: all() -> list[Skill]
    embedding_provider needs: embed(texts) -> list[list[float]]
    llm_provider needs: generate(prompt) -> str
"""
import dataclasses
import logging

from application.matching.scoring import ProfileScorer
from application.tailoring.generation import generate_section_text
from domain.cv.entities import CandidateProfile, Experience
from domain.matching.education_matching import candidate_highest_education
from domain.matching.enums import RequirementStatus
from domain.matching.experience_matching import compute_years_of_experience
from domain.skills.enrichment import TechnologyMentionScanner
from domain.tailoring.diff import compute_word_diff
from domain.tailoring.entities import TailoredCV, TailoringChange
from domain.tailoring.enums import TailoringStatus
from domain.truth.claim_validation import validate_generated_text
from domain.truth.entities import CandidateFact
from domain.truth.enums import FactType
from domain.truth.fact_extraction import build_candidate_facts

logger = logging.getLogger(__name__)


class RunTailoring:
    def __init__(
        self,
        tailoring_repository,
        candidate_profile_repository,
        job_profile_repository,
        skill_repository,
        embedding_provider,
        llm_provider,
    ) -> None:
        self._tailoring_repository = tailoring_repository
        self._candidate_profile_repository = candidate_profile_repository
        self._job_profile_repository = job_profile_repository
        self._skill_repository = skill_repository
        self._scorer = ProfileScorer(skill_repository, embedding_provider)
        self._llm_provider = llm_provider

    def execute(self, plan_id: str) -> None:
        logger.info("tailoring.started plan_id=%s", plan_id)
        try:
            self._tailoring_repository.mark_status(plan_id, TailoringStatus.PLANNING)
            plan = self._tailoring_repository.get_plan(plan_id)
            candidate_document_id, job_document_id = self._tailoring_repository.get_analysis_document_pair(
                plan.analysis_id
            )
            candidate = self._candidate_profile_repository.get(candidate_document_id)
            job = self._job_profile_repository.get(job_document_id)
            if candidate is None or job is None:
                self._tailoring_repository.mark_failed(
                    plan_id, "The candidate or job profile could not be found."
                )
                return

            before_result = self._scorer.score(candidate, job)
            facts = build_candidate_facts(candidate)
            facts_by_id = {fact.id: fact for fact in facts}
            all_skills = self._skill_repository.all()
            scanner = TechnologyMentionScanner(all_skills)
            known_skill_names = _known_skill_names(facts, scanner)
            highest_education_level = candidate_highest_education(candidate)[0]

            self._tailoring_repository.mark_status(plan_id, TailoringStatus.GENERATING)
            changes: list[TailoringChange] = []
            experience_overrides: dict[int, Experience] = {}
            skill_overrides: dict[int, str] = {}

            for operation in plan.operations:
                fact = facts_by_id.get(operation.fact_id)
                if fact is None:
                    continue
                proposed_text = generate_section_text(
                    fact=fact,
                    mode=plan.mode,
                    requirement_text=operation.recommendation_title,
                    target_state=operation.target_state,
                    llm_provider=self._llm_provider,
                )
                change = self._validate_and_build_change(
                    fact=fact,
                    proposed_text=proposed_text,
                    recommendation_title=operation.recommendation_title,
                    scanner=scanner,
                    known_skill_names=known_skill_names,
                    highest_education_level=highest_education_level,
                    candidate=candidate,
                )
                changes.append(change)
                if change.accepted:
                    _apply_change(fact, change.final_text, experience_overrides, skill_overrides)

            self._tailoring_repository.mark_status(plan_id, TailoringStatus.VALIDATING)
            tailored_candidate = _rebuild_profile(candidate, experience_overrides, skill_overrides)
            after_result = self._scorer.score(tailored_candidate, job)

            improved, unchanged, still_missing = _compare_requirements(
                before_result.evaluations, after_result.evaluations
            )

            result = TailoredCV(
                analysis_id=plan.analysis_id,
                plan=plan,
                status=TailoringStatus.COMPLETED,
                changes=tuple(changes),
                before_score=before_result.breakdown.overall,
                after_score=after_result.breakdown.overall,
                requirements_improved=improved,
                requirements_unchanged=unchanged,
                requirements_still_missing=still_missing,
            )
            self._tailoring_repository.save_result(plan_id, result)
            logger.info(
                "tailoring.completed plan_id=%s before=%.4f after=%.4f",
                plan_id,
                before_result.breakdown.overall,
                after_result.breakdown.overall,
            )
        except Exception:
            self._tailoring_repository.mark_failed(
                plan_id, "An unexpected error occurred while generating the tailored CV."
            )
            logger.exception("tailoring.failed plan_id=%s", plan_id)
            raise

    def _validate_and_build_change(
        self,
        *,
        fact: CandidateFact,
        proposed_text: str,
        recommendation_title: str,
        scanner: TechnologyMentionScanner,
        known_skill_names: frozenset[str],
        highest_education_level,
        candidate: CandidateProfile,
    ) -> TailoringChange:
        verified_years = None
        if fact.type == FactType.EXPERIENCE:
            index = int(fact.id.split(":")[1])
            experience = candidate.experiences[index]
            verified_years = compute_years_of_experience((experience,)).total_years

        validation = validate_generated_text(
            original_text=fact.value,
            proposed_text=proposed_text,
            scanner=scanner,
            known_skill_names=known_skill_names,
            verified_years=verified_years,
            highest_education_level=highest_education_level,
        )

        final_text = proposed_text if validation.is_valid else fact.value
        diff = compute_word_diff(fact.value, final_text)
        return TailoringChange(
            fact_id=fact.id,
            original_text=fact.value,
            final_text=final_text,
            diff=diff,
            accepted=validation.is_valid,
            recommendation_title=recommendation_title,
            rejection_reasons=tuple(v.reason for v in validation.violations),
        )


def _known_skill_names(facts: tuple[CandidateFact, ...], scanner: TechnologyMentionScanner) -> frozenset[str]:
    names: set[str] = set()
    for fact in facts:
        if fact.type == FactType.SKILL:
            names.add(fact.normalized_value or fact.value)
        names.update(skill.canonical_name for skill in scanner.scan(fact.value))
    return frozenset(names)


def _apply_change(
    fact: CandidateFact,
    final_text: str,
    experience_overrides: dict[int, str],
    skill_overrides: dict[int, str],
) -> None:
    fact_type, index_str = fact.id.split(":")
    index = int(index_str)
    if fact_type == "skill":
        skill_overrides[index] = final_text
    elif fact_type == "experience":
        experience_overrides[index] = final_text


def _rebuild_profile(
    candidate: CandidateProfile,
    experience_overrides: dict[int, str],
    skill_overrides: dict[int, str],
) -> CandidateProfile:
    """Section 73 takes the literal path (Tailored CV -> re-extraction ->
    Phase 4 engine). This reuses the already-structured CandidateProfile
    directly instead of rendering a document and re-parsing it: tailoring
    only ever changes wording/canonical naming of facts the Truth Layer
    already verified, never structure, so re-running Phase 2's extractor
    on rendered text would only reintroduce the same facts through a
    lossier path. Documented as a deliberate simplification in
    docs/architecture/phase-5-recommendations-and-tailoring.md.

    An experience's rewritten text updates `description` specifically,
    since that is what domain/matching/responsibility_matching.py reads
    for lexical/semantic overlap - the field a clarified bullet actually
    needs to change for the re-analysis to reflect the improvement.
    """
    if not skill_overrides and not experience_overrides:
        return candidate

    new_skills = list(candidate.skills)
    for index, new_text in skill_overrides.items():
        new_skills[index] = dataclasses.replace(new_skills[index], raw_text=new_text)

    new_experiences = list(candidate.experiences)
    for index, new_text in experience_overrides.items():
        new_experiences[index] = dataclasses.replace(new_experiences[index], description=new_text)

    return dataclasses.replace(candidate, skills=tuple(new_skills), experiences=tuple(new_experiences))


def _compare_requirements(before, after) -> tuple[int, int, int]:
    improved = unchanged = still_missing = 0
    for before_eval, after_eval in zip(before, after, strict=False):
        if after_eval.status == RequirementStatus.MET and before_eval.status != RequirementStatus.MET:
            improved += 1
        elif after_eval.status != RequirementStatus.MET:
            still_missing += 1
        else:
            unchanged += 1
    return improved, unchanged, still_missing
