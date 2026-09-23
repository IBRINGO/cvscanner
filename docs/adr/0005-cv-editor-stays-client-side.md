# ADR 0005: The CV editor never persists edits to the backend

* Status: Accepted
* Date: 2026-09-23

## Context

The Phase 6 frontend redesign added a structured CV editor
(`features/cvs/pages/cv-editor`) so a candidate can reorder sections,
hide ones they don't want on a given version, rework their own wording,
and remove entries before exporting a tailored document. This is a
genuinely useful, product-expected feature (`FINAL ACCEPTANCE CRITERIA:
"The CV editor supports structured editing"`).

The obvious next question is where an edit made in this editor should
live: does it get saved back to the CV document's stored
`CandidateProfile`, does it create a new document version, or does it
stay local to the browser session?

Saving edits back to the backend would require either (a) a new
mutation endpoint that writes arbitrary candidate-authored free text
into the same `CandidateProfile` structure the Truth Layer treats as
ground truth for future tailoring runs, or (b) routing every edit
through the existing tailoring/generation pipeline (which is designed
for a fixed set of recommendation-driven transformations, not
open-ended manual editing, and would force every simple wording tweak
through LLM generation and claim validation it doesn't need).

Option (a) is the concerning one: once free-text edits can be written
back into the same profile structure the Truth Layer (ADR 0004) treats
as verified ground truth, that structure is no longer reliably "what
was actually extracted from the candidate's real CV with evidence" -
it becomes partially "whatever the candidate most recently typed into
an editor," with no distinction between the two. Every downstream
consumer of `CandidateProfile` (the analysis engine, the recommendation
engine, the Truth Layer's fact extraction) implicitly assumes it is the
former.

## Decision

The CV editor is client-side only. All editing state (the working
`CandidateProfile` copy, section order, hidden sections, undo/redo
history) lives in `CvEditorComponent`'s signals for the lifetime of that
page. It is never sent to the backend. Its only two consumers are the
live `CvDocumentRenderer` preview and the print-based PDF export - both
read-only projections of the in-memory state, not persistence.

This means:

- Editing is always available and instant (no network round-trip, no
  save/conflict states to design).
- The backend's `CandidateProfile` and the Truth Layer's authority over
  it are completely unaffected by anything that happens in the editor -
  reordering, hiding, or rewording here can never leak into a future
  tailoring run's "verified" facts.
- Refreshing the page or navigating away loses in-progress edits. This
  is an accepted, explicit tradeoff, not an oversight - the template
  gallery's "Use this template" link and the CV detail page's "Open in
  CV editor" link both start a fresh editing session from the real
  extracted profile every time.

## Consequences

- If a future phase wants edits to persist across sessions (e.g. "save
  my tailored resume version"), that needs a deliberately separate data
  model - e.g. a `CvVersion`/export artifact that snapshots the edited
  structure - not a write path into `CandidateProfile` itself. That is
  explicitly out of scope for this phase.
- The export panel's page-count estimate and PDF output always reflect
  exactly what is currently in memory, so there is no drift between
  "what you see in the editor" and "what gets exported."
