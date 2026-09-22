"""Small regex helpers shared by the candidate and job extractors.

Deliberately not in domain/ - regex is an implementation detail of "how
we currently pull contact facts out of raw text", not a business rule.
A future LLM-assisted extractor would not need any of this.
"""
import re

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)[\s.-]?)?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{2,4}(?:[\s.-]?\d{2,4})?"
)
_LINK_RE = re.compile(r"(?:https?://|www\.)[^\s,;]+|(?:linkedin\.com|github\.com)/[^\s,;]+")


def extract_email(text: str) -> str | None:
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    for line in text.splitlines():
        # A phone number often shares a line with an email (e.g. "email |
        # phone") - strip the email substring rather than skipping the
        # whole line, so the phone after it is still found.
        line_without_email = _EMAIL_RE.sub("", line)
        match = _PHONE_RE.search(line_without_email)
        if match and sum(c.isdigit() for c in match.group(0)) >= 7:
            return match.group(0).strip()
    return None


def extract_links(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(match.group(0) for match in _LINK_RE.finditer(text)))


def split_delimited_tokens(text: str) -> list[str]:
    """Splits a skills/languages/certifications line-or-block on common
    CV delimiters (comma, semicolon, pipe, bullet, newline) into
    individual candidate tokens.
    """
    raw_tokens = re.split(r"[,;|•\n]", text)
    return [token.strip(" -\t") for token in raw_tokens if token.strip(" -\t")]
