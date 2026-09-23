from application.tailoring.generation import generate_section_text
from domain.tailoring.enums import TailoringMode
from domain.truth.entities import CandidateFact
from domain.truth.enums import AllowedTransformation, FactType, VerificationStatus
from infrastructure.llm.base import LLMProviderError
from infrastructure.llm.providers.fake_provider import FakeLLMProvider


def _skill_fact() -> CandidateFact:
    return CandidateFact(
        id="skill:0",
        type=FactType.SKILL,
        value="Postgres",
        normalized_value="PostgreSQL",
        confidence=0.9,
        verification_status=VerificationStatus.VERIFIED,
        allowed_transformations=(AllowedTransformation.REPHRASE,),
    )


def _experience_fact(value: str = "Built internal tooling.") -> CandidateFact:
    return CandidateFact(
        id="experience:0",
        type=FactType.EXPERIENCE,
        value=value,
        normalized_value=None,
        confidence=0.9,
        verification_status=VerificationStatus.VERIFIED,
        allowed_transformations=(AllowedTransformation.REPHRASE,),
    )


class TestSkillNormalization:
    def test_skill_rephrase_never_calls_the_llm(self):
        class _ExplodingProvider:
            name = "exploding"

            def generate(self, prompt: str) -> str:
                raise AssertionError("must not be called for a skill fact")

        result = generate_section_text(
            fact=_skill_fact(),
            mode=TailoringMode.AGGRESSIVE_SAFE,
            requirement_text="PostgreSQL",
            target_state="PostgreSQL",
            llm_provider=_ExplodingProvider(),
        )
        assert result == "PostgreSQL"

    def test_falls_back_to_normalized_value_when_no_target_state_given(self):
        result = generate_section_text(
            fact=_skill_fact(),
            mode=TailoringMode.CONSERVATIVE,
            requirement_text="PostgreSQL",
            target_state=None,
            llm_provider=None,
        )
        assert result == "PostgreSQL"


class TestConservativeMode:
    def test_experience_rephrase_is_left_unchanged_in_conservative_mode(self):
        fact = _experience_fact()
        result = generate_section_text(
            fact=fact,
            mode=TailoringMode.CONSERVATIVE,
            requirement_text="Design and maintain REST APIs",
            target_state=None,
            llm_provider=FakeLLMProvider(),
        )
        assert result == fact.value


class TestAggressiveSafeMode:
    def test_uses_the_llm_response_when_it_parses(self):
        fact = _experience_fact()
        result = generate_section_text(
            fact=fact,
            mode=TailoringMode.AGGRESSIVE_SAFE,
            requirement_text="Design and maintain REST APIs",
            target_state=None,
            llm_provider=FakeLLMProvider(),
        )
        assert result == fact.value  # the default fake echoes the original text back

    def test_falls_back_to_original_text_when_the_provider_fails(self):
        class _FailingProvider:
            name = "failing"

            def generate(self, prompt: str) -> str:
                raise LLMProviderError("boom")

        fact = _experience_fact()
        result = generate_section_text(
            fact=fact,
            mode=TailoringMode.AGGRESSIVE_SAFE,
            requirement_text="Design and maintain REST APIs",
            target_state=None,
            llm_provider=_FailingProvider(),
        )
        assert result == fact.value

    def test_falls_back_to_original_text_when_the_response_is_unparseable(self):
        fact = _experience_fact()
        result = generate_section_text(
            fact=fact,
            mode=TailoringMode.AGGRESSIVE_SAFE,
            requirement_text="Design and maintain REST APIs",
            target_state=None,
            llm_provider=FakeLLMProvider(response_fn=lambda prompt: "not json at all"),
        )
        assert result == fact.value
