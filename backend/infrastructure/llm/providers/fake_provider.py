"""A deterministic, dependency-free LLM provider for development and
tests (mirrors infrastructure/embeddings/providers/fake_provider.py's
role for embeddings). Its default behavior echoes the original text
back unchanged, wrapped in the same JSON shape a real provider is asked
for (see application/tailoring/generation.py's PROMPT_TEMPLATE) - a safe
no-op "rewrite" that lets integration tests exercise the full tailoring
pipeline deterministically, without ever needing to guess what a real
model would say.

Tests that need to exercise the Truth Layer's rejection path pass a
`response_fn` that deliberately returns unsafe text (e.g. inventing
Kubernetes) - see tests/unit/application/tailoring/test_run_tailoring.py.
"""
import re
from collections.abc import Callable

_ORIGINAL_TEXT_PATTERN = re.compile(r"Original text:\n(.*?)\n\nReturn ONLY", re.DOTALL)


def _default_response(prompt: str) -> str:
    match = _ORIGINAL_TEXT_PATTERN.search(prompt)
    original_text = match.group(1).strip() if match else ""
    escaped = original_text.replace("\\", "\\\\").replace('"', '\\"')
    return f'{{"proposed_text": "{escaped}"}}'


class FakeLLMProvider:
    """Implements infrastructure.llm.base.LLMProvider."""

    def __init__(self, response_fn: Callable[[str], str] | None = None) -> None:
        self._response_fn = response_fn or _default_response

    @property
    def name(self) -> str:
        return "fake"

    def generate(self, prompt: str) -> str:
        return self._response_fn(prompt)
