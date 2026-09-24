"""Server-side PDF rendering for the CV editor's "Download PDF" action.

The editor is deliberately client-side only for *editing* (see the
CvEditorComponent doc comment on the frontend) - nothing typed there is
ever validated as a candidate fact server-side. This module is the one
exception to "the editor never calls the backend": it is a pure,
stateless rendering service. It receives whatever profile JSON the
browser currently has in memory, turns it into an HTML document that
mirrors the Angular CvDocumentRenderer's structure, and rasterizes that
HTML to a real, selectable-text A4 PDF via WeasyPrint. Nothing here is
persisted or treated as a verified fact - it is the printing press, not
the Truth Layer.

Keeping this a *separate* stylesheet (not a shared build with the
Angular SCSS) is a real, accepted limitation: visual parity with the
live browser preview is "close", not pixel-guaranteed. See
docs/architecture for the tradeoff this was chosen over (a headless
Chromium dependency would guarantee pixel parity but is a much heavier
addition for this project's infrastructure).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.utils.html import escape

SIDEBAR_SECTION_KINDS = {"skills", "languages", "certifications"}

SANS = "'Liberation Sans', Arial, sans-serif"
SERIF = "'Liberation Serif', 'Times New Roman', serif"
MONO = "'Liberation Mono', 'DejaVu Sans Mono', monospace"


@dataclass(frozen=True)
class TemplateStyle:
    columns: int
    name_font: str
    name_transform: str
    name_align: str
    accent: str
    heading_color: str
    heading_border: str
    body_padding: str
    sidebar_bg: str | None


TEMPLATES: dict[str, TemplateStyle] = {
    "ats-classic": TemplateStyle(
        columns=1,
        name_font=SERIF,
        name_transform="uppercase",
        name_align="left",
        accent="#1b1a17",
        heading_color="#1b1a17",
        heading_border="#1b1a17",
        body_padding="48px 44px",
        sidebar_bg=None,
    ),
    "ats-professional": TemplateStyle(
        columns=1,
        name_font=SANS,
        name_transform="none",
        name_align="left",
        accent="#2563eb",
        heading_color="#2563eb",
        heading_border="#2563eb",
        body_padding="48px 44px",
        sidebar_bg=None,
    ),
    "executive": TemplateStyle(
        columns=1,
        name_font=SANS,
        name_transform="none",
        name_align="center",
        accent="#2563eb",
        heading_color="#5c584f",
        heading_border="transparent",
        body_padding="56px 56px",
        sidebar_bg=None,
    ),
    "modern-split": TemplateStyle(
        columns=2,
        name_font=SANS,
        name_transform="none",
        name_align="left",
        accent="#1d4ed8",
        heading_color="#1d4ed8",
        heading_border="#e3ded2",
        body_padding="0",
        sidebar_bg="#e8eefd",
    ),
    "technical": TemplateStyle(
        columns=2,
        name_font=MONO,
        name_transform="none",
        name_align="left",
        accent="#0284c7",
        heading_color="#5c584f",
        heading_border="#e3ded2",
        body_padding="48px 44px",
        sidebar_bg=None,
    ),
    "minimal": TemplateStyle(
        columns=1,
        name_font=SANS,
        name_transform="none",
        name_align="left",
        accent="#5c584f",
        heading_color="#5c584f",
        heading_border="transparent",
        body_padding="48px 44px",
        sidebar_bg=None,
    ),
}

DEFAULT_TEMPLATE = "ats-classic"


def _text(value: Any) -> str:
    return escape(str(value)) if value not in (None, "") else ""


def _contact_line(profile: dict) -> str:
    items = [profile.get("email"), profile.get("phone"), profile.get("location"), *(profile.get("links") or [])]
    return "&nbsp;&nbsp;|&nbsp;&nbsp;".join(escape(i) for i in items if i)


def _summary_html(profile: dict) -> str:
    summary = profile.get("summary")
    if not summary:
        return ""
    return f'<section class="section"><h2>Summary</h2><p>{_text(summary)}</p></section>'


def _experience_html(profile: dict) -> str:
    experiences = profile.get("experiences") or []
    if not experiences:
        return ""
    entries = []
    for exp in experiences:
        title = _text(exp.get("title") or "Role")
        company = f", {_text(exp.get('company'))}" if exp.get("company") else ""
        dates = ""
        if exp.get("start_date_raw"):
            dates = f'<span class="dates">{_text(exp["start_date_raw"])} - {_text(exp.get("end_date_raw") or "Present")}</span>'
        desc = f'<p class="desc">{_text(exp["description"])}</p>' if exp.get("description") else ""
        achievements = exp.get("achievements") or []
        bullets = (
            "<ul>" + "".join(f"<li>{_text(a)}</li>" for a in achievements) + "</ul>" if achievements else ""
        )
        entries.append(
            f'<div class="entry"><div class="entry-head"><span class="entry-title">{title}{company}</span>'
            f"{dates}</div>{desc}{bullets}</div>"
        )
    return f'<section class="section"><h2>Experience</h2>{"".join(entries)}</section>'


def _education_html(profile: dict) -> str:
    education = profile.get("education") or []
    if not education:
        return ""
    entries = []
    for entry in education:
        degree = _text(entry.get("degree") or "Program")
        institution = f", {_text(entry.get('institution'))}" if entry.get("institution") else ""
        dates = ""
        if entry.get("start_date_raw"):
            dates = f'<span class="dates">{_text(entry["start_date_raw"])} - {_text(entry.get("end_date_raw") or "")}</span>'
        entries.append(f'<div class="entry"><div class="entry-head"><span class="entry-title">{degree}{institution}</span>{dates}</div></div>')
    return f'<section class="section"><h2>Education</h2>{"".join(entries)}</section>'


def _skills_html(profile: dict) -> str:
    skills = profile.get("skills") or []
    if not skills:
        return ""
    names = []
    for s in skills:
        skill_ref = s.get("skill")
        names.append(_text((skill_ref or {}).get("canonical_name") if skill_ref else s.get("raw_text")))
    return f'<section class="section"><h2>Skills</h2><p class="skill-line">{", ".join(names)}</p></section>'


def _projects_html(profile: dict) -> str:
    projects = profile.get("projects") or []
    if not projects:
        return ""
    entries = []
    for project in projects:
        name = _text(project.get("name"))
        desc = f'<p class="desc">{_text(project["description"])}</p>' if project.get("description") else ""
        entries.append(f'<div class="entry"><span class="entry-title">{name}</span>{desc}</div>')
    return f'<section class="section"><h2>Projects</h2>{"".join(entries)}</section>'


def _certifications_html(profile: dict) -> str:
    certifications = profile.get("certifications") or []
    if not certifications:
        return ""
    entries = []
    for cert in certifications:
        name = _text(cert.get("name"))
        issuer = f", {_text(cert.get('issuer'))}" if cert.get("issuer") else ""
        entries.append(f'<div class="entry entry-tight"><span class="entry-title">{name}{issuer}</span></div>')
    return f'<section class="section"><h2>Certifications</h2>{"".join(entries)}</section>'


def _languages_html(profile: dict) -> str:
    languages = profile.get("languages") or []
    if not languages:
        return ""
    parts = []
    for lang in languages:
        name = _text(lang.get("canonical_name") or lang.get("name"))
        proficiency = lang.get("proficiency_normalized")
        if proficiency and proficiency != "UNKNOWN":
            name += f" ({_text(proficiency.replace('_', ' ').title())})"
        parts.append(name)
    return f'<section class="section"><h2>Languages</h2><p class="skill-line">{", ".join(parts)}</p></section>'


def _custom_html(ref: dict) -> str:
    title = _text(ref.get("title") or "")
    content = _text(ref.get("content") or "")
    return f'<section class="section"><h2>{title}</h2><p>{content}</p></section>'


_SECTION_RENDERERS = {
    "summary": _summary_html,
    "experience": _experience_html,
    "education": _education_html,
    "skills": _skills_html,
    "projects": _projects_html,
    "certifications": _certifications_html,
    "languages": _languages_html,
}


def _render_sections(profile: dict, section_order: list[dict], hidden_ids: set[str]) -> tuple[str, str]:
    """Returns (main_html, sidebar_html) - sidebar is only used by
    2-column templates; single-column templates get everything in main."""
    main_parts: list[str] = []
    sidebar_parts: list[str] = []
    for ref in section_order:
        ref_id = ref.get("id")
        if ref_id in hidden_ids:
            continue
        kind = ref.get("kind")
        if kind == "custom":
            html = _custom_html(ref)
        else:
            renderer = _SECTION_RENDERERS.get(kind)
            html = renderer(profile) if renderer else ""
        if not html:
            continue
        if kind in SIDEBAR_SECTION_KINDS:
            sidebar_parts.append(html)
        else:
            main_parts.append(html)
    return "".join(main_parts), "".join(sidebar_parts)


def render_cv_pdf(
    profile: dict,
    template_id: str,
    section_order: list[dict],
    hidden_section_ids: list[str],
) -> bytes:
    # Imported lazily: WeasyPrint needs native Pango/Cairo/GDK-pixbuf
    # libraries that are installed in the backend Docker image (see
    # infrastructure/docker/backend.Dockerfile) but not on a bare
    # Windows/macOS dev machine. A module-level import would break the
    # whole URL conf (and therefore every API test that calls reverse())
    # for anyone running `pytest` outside Docker - see Makefile's
    # `test-backend` target, which runs locally against SQLite.
    from weasyprint import HTML

    style = TEMPLATES.get(template_id, TEMPLATES[DEFAULT_TEMPLATE])
    hidden_ids = set(hidden_section_ids or [])
    main_html, sidebar_html = _render_sections(profile, section_order, hidden_ids)

    name = _text(profile.get("full_name") or "Unnamed candidate")
    contact = _contact_line(profile)
    contact_html = f'<p class="contact">{contact}</p>' if contact else ""

    if style.columns == 2:
        body_html = (
            f'<div class="body split">'
            f'<aside class="sidebar">{sidebar_html}</aside>'
            f'<div class="main">{main_html}</div>'
            f"</div>"
        )
    else:
        body_html = f'<div class="body">{main_html}{sidebar_html}</div>'

    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <style>{_css(style)}</style>
      </head>
      <body>
        <article class="cv-page">
          <header class="header">
            <h1>{name}</h1>
            {contact_html}
          </header>
          {body_html}
        </article>
      </body>
    </html>
    """
    return HTML(string=html).write_pdf()


def _css(style: TemplateStyle) -> str:
    sidebar_css = (
        f".sidebar {{ background: {style.sidebar_bg}; padding: 24px 28px 40px; flex: 0 0 34%; }}"
        if style.sidebar_bg
        else ".sidebar { flex: 0 0 34%; }"
    )
    return f"""
      @page {{ size: A4; margin: 0; }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: {SANS}; color: #1b1a17; }}
      .cv-page {{ padding: {style.body_padding}; }}
      .header {{ margin-bottom: 24px; text-align: {style.name_align}; }}
      .header h1 {{
        font-family: {style.name_font};
        font-size: 28px;
        font-weight: 700;
        text-transform: {style.name_transform};
        letter-spacing: 0.02em;
        margin: 0;
        color: #1b1a17;
      }}
      .contact {{ margin: 4px 0 0; color: #5c584f; font-size: 12px; }}
      .body {{ display: flex; flex-direction: column; gap: 20px; }}
      .body.split {{ flex-direction: row; align-items: flex-start; gap: 0; }}
      .main {{ flex: 1; min-width: 0; padding: {"24px 40px 40px" if style.sidebar_bg else "0"}; display: flex; flex-direction: column; gap: 20px; }}
      {sidebar_css}
      .sidebar {{ display: flex; flex-direction: column; gap: 20px; }}
      .section h2 {{
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: {style.heading_color};
        margin: 0 0 10px;
        padding-bottom: 4px;
        border-bottom: 1px solid {style.heading_border};
      }}
      .section p {{ margin: 0; font-size: 13px; line-height: 1.5; }}
      .entry {{ margin-bottom: 14px; }}
      .entry:last-child {{ margin-bottom: 0; }}
      .entry-tight {{ margin-bottom: 6px; }}
      .entry-head {{ display: flex; justify-content: space-between; gap: 12px; }}
      .entry-title {{ font-weight: 600; font-size: 13px; }}
      .dates {{ font-size: 11px; color: #5c584f; white-space: nowrap; font-family: {MONO}; }}
      .desc {{ margin: 4px 0 0; color: #5c584f; font-size: 12.5px; line-height: 1.5; }}
      .entry ul {{ margin: 6px 0 0; padding-left: 18px; color: #5c584f; font-size: 12.5px; line-height: 1.5; }}
      .skill-line {{ color: #5c584f; font-size: 12.5px; line-height: 1.6; }}
    """
