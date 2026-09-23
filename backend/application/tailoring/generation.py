"""Generates proposed text for one `SectionOperation` (Phase 5 sections
19-26). This is where a `TailoringMode` actually changes behavior:

CONSERVATIVE never calls the LLM. A SKILL fact's REPHRASE operation is a
deterministic keyword-normalization (section 22 - "Postgres" ->
"PostgreSQL", using the canonical name Phase 2/3's taxonomy already
established); an EXPERIENCE fact's REPHRASE operation in CONSERVATIVE
mode is left unchanged (returns the original text) - CONSERVATIVE mode
only ever touches what is already fully deterministic.

AGGRESSIVE_SAFE calls the LLM for an EXPERIENCE fact's REPHRASE
operation - the one case that genuinely benefits from rewriting rather
than a template. The prompt (section 26) explicitly forbids inventing
facts and asks for a single-field JSON response
(`{"proposed_text": "..."}` - section 25's structured-output
preference, kept intentionally simple so the same parsing works for
both providers). Whatever the model returns is NEVER trusted on its own
- domain/truth/claim_validation.py independently checks it before it
can become part of the result (section 18), and any parsing/provider
failure here falls back to the original text unchanged, since "no
change" is always a safe result.
"""
import json
import logging
import re

from domain.tailoring.enums import TailoringMode
from domain.truth.entities import CandidateFact
from domain.truth.enums import FactType
from infrastructure.llm.base import LLMProvider, LLMProviderError

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are helping a candidate present real, already-verified work experience more \
clearly for a specific job application.

STRICT RULES - follow all of them:
- You are not allowed to invent candidate facts.
- You may only use facts already present in the original text below.
- Never introduce a new technology, tool, certification, degree, language proficiency, or duration \
that is not already stated in the original text.
- If the requested improvement cannot be supported by the original text, return the original text unchanged.
- Keep the result concise, natural, and human-readable. Do not stuff keywords.

Job requirement this should better address: {requirement}

Original text:
{original_text}

Return ONLY a JSON object of the exact shape {{"proposed_text": "..."}} with no other text before or after it.
"""

_JSON_FIELD_PATTERN = re.compile(r'"proposed_text"\s*:\s*"((?:[^"\\]|\\.)*)"', re.DOTALL)


def _extract_proposed_text(raw_response: str) -> str | None:
    try:
        parsed = json.loads(raw_response)
        if isinstance(parsed, dict) and isinstance(parsed.get("proposed_text"), str):
            return parsed["proposed_text"]
    except (json.JSONDecodeError, TypeError):
        pass

    match = _JSON_FIELD_PATTERN.search(raw_response)
    if match:
        return match.group(1).encode().decode("unicode_escape")
    return None


def generate_section_text(
    *,
    fact: CandidateFact,
    mode: TailoringMode,
    requirement_text: str,
    target_state: str | None,
    llm_provider: LLMProvider | None,
) -> str:
    if fact.type == FactType.SKILL:
        # Keyword normalization needs no creativity in either mode.
        return target_state or fact.normalized_value or fact.value

    if mode == TailoringMode.CONSERVATIVE or llm_provider is None:
        return fact.value

    prompt = PROMPT_TEMPLATE.format(requirement=requirement_text, original_text=fact.value)
    try:
        raw_response = llm_provider.generate(prompt)
    except LLMProviderError as exc:
        logger.warning("tailoring.llm_unavailable fact_id=%s error=%s", fact.id, exc)
        return fact.value

    proposed_text = _extract_proposed_text(raw_response)
    if proposed_text is None:
        logger.warning("tailoring.llm_response_unparseable fact_id=%s", fact.id)
        return fact.value
    return proposed_text
