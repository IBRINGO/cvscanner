"""Pure vector math for semantic matching (Phase 4 section 32-33).
Deliberately framework-free (no numpy) - embedding vectors here are at
most a few thousand floats, far too small to need a vectorized library,
and keeping this dependency-free matches the rest of domain/.
"""
import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
