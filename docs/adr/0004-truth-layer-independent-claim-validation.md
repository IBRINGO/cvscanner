# ADR 0004: An independent, deterministic Truth Layer validates every generated claim

* Status: Accepted
* Date: 2026-09-23

## Context

Phase 5 lets CVScanner rewrite CV wording - normalize a skill's name,
clarify a bullet to better match a job's responsibilities, and (in
`AGGRESSIVE_SAFE` mode) call an LLM to rephrase an experience
description. Any system that rewrites text toward a target (here: a
job's requirements) has an obvious failure mode: the rewrite quietly
inflates or invents facts to score better, because "score higher"
becomes a stronger optimization pressure than "stay true."

The brief is explicit and non-negotiable about this
(`Principle 1: Truth before optimization`, `Principle 3: No
hallucinated experience`): a candidate with Docker on their CV must
never see a job requiring Kubernetes turn into a claim of Kubernetes
experience, regardless of how much that would improve the analyzed
match.

Simply instructing the LLM not to hallucinate (a system prompt like
"you are not allowed to invent candidate facts") is necessary but not
sufficient - prompts are not guarantees, and a prompt cannot be tested
the way code can.

## Decision

Introduce a Truth Layer as an architectural boundary the LLM sits
behind, with two parts:

1. **`CandidateFact`** (`domain/truth/entities.py` +
   `fact_extraction.py`) - a read-only, structured re-projection of the
   already-verified `CandidateProfile` (Phase 2/3's evidence-backed
   facts), stating what each fact is, how sure we are of it
   (`VerificationStatus`), and what may safely happen to its wording
   (`AllowedTransformation`). This is the *only* context a rewrite step
   may draw from.
2. **Deterministic claim validation**
   (`domain/truth/claim_validation.py`) - plain Python functions that
   independently re-check every proposed sentence against the fact set,
   regardless of whether the sentence came from a deterministic
   template (`CONSERVATIVE` mode) or an LLM (`AGGRESSIVE_SAFE` mode).
   The LLM's own claim that it followed the rules carries no special
   weight; the same five checks run every time:
   `validate_technology_claims`, `validate_certification_claims`,
   `validate_duration_claims`, `validate_education_claims`,
   `validate_language_claims`.

A rejected proposal keeps the fact's original text and records why it
was rejected (`ClaimRejectionReason`) - visible to the candidate
(section 57), never silently dropped.

## Consequences

**Why this is worth a dedicated layer rather than "a good prompt":**

* **Testable in isolation.** Each of the five checks is a pure function
  with unit tests, including the exact five adversarial scenarios the
  brief lists verbatim (Kubernetes-from-Docker, AWS-certification-from-
  AWS-skill, 5-years-from-2-verified-years, native-English-from-B2,
  Master's-from-Bachelor's) -
  `tests/unit/domain/truth/test_claim_validation.py::TestAdversarialCases`.
  A prompt cannot be unit tested the same way; a regex/keyword check
  can.
* **Provider-independent.** Gemini and OpenAI (and any future provider)
  all pass through the identical validation step. Switching providers,
  or a provider changing its own behavior over time, cannot weaken the
  safety guarantee - the guarantee lives in `domain/truth/`, not in
  whichever provider happened to answer the prompt.
* **CONSERVATIVE mode gets the same guarantee for free.** Even though
  CONSERVATIVE mode never calls an LLM, its deterministic rewrites still
  pass through claim validation. This is deliberately not treated as
  "trusted because it's not an LLM" - a bug in a deterministic template
  is caught by the exact same net.
* **Explainable rejection, not silent failure.** Section 57 asks that a
  rejected change be explained, not hidden. Because rejection reasons
  are typed (`ClaimRejectionReason`), the frontend can render a
  specific, human-readable explanation ("introduces a certification
  claim not present in the original") instead of a generic "something
  went wrong."

**What this costs, on purpose:**

* Real hallucinations that don't match one of the five checked
  categories (a fabricated *responsibility* with no technology,
  certification, duration, education, or language keyword in it, for
  example) are not caught by this layer. This is a deliberate, bounded
  first version - the five categories were chosen because they map
  directly to the brief's own adversarial examples and to Phase 2/3's
  existing structured fact types (skills, certifications, experience
  duration, education level, language proficiency). A fabricated but
  keyword-free claim is a known gap, not a false sense of completeness.
* Technology-claim detection depends on Phase 3's skill taxonomy
  (`TechnologyMentionScanner`) - a technology not in the taxonomy is
  invisible to `validate_technology_claims` in either direction (it can
  neither be flagged as invented nor recognized as already known).
* Duration/education/language claim detection is keyword/regex-based,
  not full natural-language understanding - see
  [phase-5-recommendations-and-tailoring.md](../architecture/phase-5-recommendations-and-tailoring.md)
  "Known limitations" for the exact boundaries.
