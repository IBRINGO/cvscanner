"""LLMProvider abstraction (Phase 5 section 24-26). Mirrors
infrastructure/embeddings/base.py's shape exactly: the domain/
application layers never import a concrete provider, and
config/container.py decides which implementation to build.

`generate` takes a single prompt and returns raw text. Structured
output (section 25) is achieved by instructing the model, in the
prompt, to return a specific JSON shape, and having the caller
(application/tailoring/generation.py) parse and validate that JSON -
not by relying on a provider-specific function-calling API, so the same
call shape works identically across Gemini and OpenAI. The Truth Layer
(domain/truth/claim_validation.py) validates the result independently
of whatever the model claims about its own output (section 18) -
`generate` returning cleanly is not, by itself, proof of anything.
"""
from typing import Protocol


class LLMProvider(Protocol):
    @property
    def name(self) -> str: ...

    def generate(self, prompt: str) -> str: ...


class LLMProviderError(Exception):
    """Raised when a provider cannot produce a completion (network
    failure, missing credentials, rate limit, malformed response, ...).
    Callers must catch this and degrade - for CONSERVATIVE-mode
    tailoring this never even applies (no LLM call is made); for
    AGGRESSIVE_SAFE, a failed generation for one section means that
    section's original text is kept unchanged, never that the whole
    tailoring run fails (mirrors section 25/80's embedding-failure
    handling from Phase 3/4).
    """
