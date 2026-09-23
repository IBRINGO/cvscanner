from domain.cv.entities import CandidateProfile, CandidateSkillMention, Contact, Experience
from domain.documents.enums import ExtractionMethod, SectionType
from domain.documents.evidence import Evidence
from domain.truth.enums import AllowedTransformation, FactType, VerificationStatus
from domain.truth.fact_extraction import build_candidate_facts


def _evidence(text: str) -> Evidence:
    return Evidence(
        source_document_id="doc-1",
        text=text,
        extraction_method=ExtractionMethod.RULE,
        confidence=0.9,
        section=SectionType.SKILLS,
    )


def _profile(**overrides) -> CandidateProfile:
    defaults = dict(full_name="Jordan Rivera", contact=Contact(), summary=None)
    defaults.update(overrides)
    return CandidateProfile(**defaults)


class TestSkillFacts:
    def test_a_skill_with_evidence_is_verified(self):
        profile = _profile(
            skills=(CandidateSkillMention(raw_text="Django", skill=None, evidence=_evidence("Django")),)
        )
        facts = build_candidate_facts(profile)
        assert len(facts) == 1
        assert facts[0].type == FactType.SKILL
        assert facts[0].verification_status == VerificationStatus.VERIFIED
        assert facts[0].permits(AllowedTransformation.REPHRASE)

    def test_a_skill_with_no_evidence_is_supported_not_verified(self):
        profile = _profile(skills=(CandidateSkillMention(raw_text="Django", skill=None, evidence=None),))
        facts = build_candidate_facts(profile)
        assert facts[0].verification_status == VerificationStatus.SUPPORTED


class TestExperienceFacts:
    def test_experience_allows_expansion_with_existing_evidence(self):
        profile = _profile(
            experiences=(
                Experience(
                    title="Backend Engineer",
                    company="Acme",
                    start_date_raw="2020",
                    end_date_raw="2023",
                    description="Built APIs.",
                    evidence=_evidence("Backend Engineer at Acme"),
                ),
            )
        )
        facts = build_candidate_facts(profile)
        assert facts[0].type == FactType.EXPERIENCE
        assert facts[0].permits(AllowedTransformation.EXPAND_WITH_EXISTING_EVIDENCE)


class TestNoFactIsInvented:
    def test_an_empty_profile_produces_no_facts(self):
        assert build_candidate_facts(_profile()) == ()
