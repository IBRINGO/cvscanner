# Phase 6 - Frontend Product Redesign

> **Update (brand refinement pass):** the sections below describe the
> initial redesign. A follow-up pass then applied the CVScanner brand
> palette (logo-derived blue/teal/navy, Inter for UI text), rebuilt the
> sidebar as a collapsible rail with a mobile drawer, added a real
> product hero to the Workspace home, threaded an `ApplicationSessionService`
> through the CV -> Job -> Analysis -> Recommendations -> Tailoring ->
> Editor -> Export journey so tailoring links directly into the editor
> with its accepted changes already applied, and substantially expanded
> the CV editor (drag-and-drop reordering, click-to-select directly on
> the rendered document, and add/duplicate/delete for individual
> experience/education/project entries). See "Brand refinement pass"
> below for the details; the architecture and safety boundaries
> described in the rest of this document are unchanged.

This document describes a full redesign of the Angular frontend built on
top of the working Phase 1-5 backend contracts (see
[phase-4-matching.md](phase-4-matching.md) and
[phase-5-recommendations-and-tailoring.md](phase-5-recommendations-and-tailoring.md)).
No backend endpoint, model, or business rule changed. This phase answers
"how should the existing analysis/recommendations/tailoring capability
actually be presented, so the product reads as a real commercial CV
intelligence tool instead of an admin panel?"

## Why this redesign happened

The prior frontend was functionally complete but presented itself as a
document-management dashboard: a KPI-style home screen, a plain
typographic score, and no real document visualization anywhere in the
product, despite the product being fundamentally about two documents
(a CV and a job offer) and the relationship between them. The redesign
keeps every existing API call and data model and changes only how the
product is composed, navigated, and rendered.

## Design foundation

`frontend/src/styles/_tokens.scss` and `_typography.scss` were replaced,
not extended. The previous system used a single terracotta accent that
doubled as both "brand color" and "needs attention," and a serif display
face chosen for an explicitly editorial register. The new system:

- Decouples the brand accent (a cobalt blue, used only for primary
  actions and "actively processing" states) from the semantic palette
  (`--positive` / `--attention` / `--negative` / `--inferred`), so a
  color always means the same thing everywhere in the product.
- Adds a distinct "paper" surface family (`--paper-surface`,
  `--paper-border`, `--paper-ink`, `--shadow-document`) used only by
  document previews and the CV renderer, so a CV or job offer always
  reads as a real piece of paper sitting inside a dark-capable
  workspace, in both light and dark mode.
- Replaces the serif display face with Space Grotesk, a confident
  geometric grotesk, because the product's identity is precision and
  measurement (scores, evidence, requirements), not editorial reading.

New shared primitives live in `frontend/src/app/shared/components/ui/`:
`score-gauge` (an animated SVG radial gauge - the primary ATS score
visualization), `application-progress` (the persistent CV -> Job ->
Analysis -> Recommendations -> Tailoring -> Export step indicator), and
`document-preview` (a stylized paper preview used instead of a bare file
icon during upload/processing).

## The "Applications" concept is derived, not a new backend entity

The home experience (`features/workspace`) and the Applications index
(`features/applications`) both need to answer "what CV+job pairings is
this person working on, and what's next?" There is no `Application`
table in the backend - an application only becomes a real, addressable
pairing once an `Analysis` links a CV document to a job document.

`features/applications/utils/build-applications.ts` derives this view
client-side: it joins the existing `AnalysisSummary[]` against the
existing CV/job `DocumentSummary[]` and the existing
`TailoringPlanSummary[]`, and computes a stage
(`analysis`/`recommendations`/`tailoring`/`export`) and a single next
action per real analysis. It never invents a pairing - a CV or job with
no analysis behind it surfaces separately as "ready to pair," and a
reference to a document that does not exist is silently dropped rather
than rendered as a broken card. This function and its sort/grouping
rules are unit-tested directly (`build-applications.spec.ts`), since
this is real product logic, not presentation.

## The guided journey

`features/applications/pages/new-application` is a new, separate entry
point (`/applications/new`) implementing the canonical
CV -> Job -> Analysis flow as one linear, auto-advancing experience. It
does not replace the existing `/cvs` and `/jobs` library pages (which
remain for managing or reusing existing documents); it is the answer to
"I want to analyze a new application right now."

Each step polls the real document status (`pollUntilDone`, unchanged
from Phase 1-3) and maps only the statuses the backend actually reports
onto a processing timeline - it never fabricates progress the backend
hasn't reported. On a real `PROCESSED` status it shows a short
transition message and auto-advances (with a manual "Continue now"
escape hatch); on `FAILED` it shows the real backend error and offers a
retry. The final step calls the existing `AnalysisApiService.createAnalysis`
and redirects into the redesigned analysis page - the journey's job ends
there, it does not duplicate the results screen.

## Analysis, recommendations, and tailoring: presentation changes only

`ScorePanelComponent`, `RequirementMatrixComponent`, `RecommendationListComponent`,
and `TailoringDiffComponent`/`TailoringDetailComponent` all keep their
existing inputs and existing backend-sourced data. The changes are:

- The plain percentage is now rendered through `ScoreGaugeComponent`,
  animating from 0 to the exact backend value - never a different
  number, never a guaranteed-to-look-good rounding.
- A new `StrengthListComponent` (`features/analysis/components/strength-list`)
  renders the same `RequirementEvaluation[]` already used by the matrix,
  filtered to `status === 'MET'`, so results read as a story (what's
  working, then what needs attention) instead of only a list of gaps.
- Recommendation detail rows are restructured into explicit
  Why / Evidence / Recommended action fields.
- Tailoring changes render inside a paper-styled card (the same
  `--paper-*` tokens as the document renderer) instead of a bare list
  row, and before/after scores use two `ScoreGauge`s - when tailoring
  did not move the score, both gauges show the same real number, which
  is the intended, honest behavior (see Phase 5's score-integrity rule).

## The template engine and CV editor

`features/templates/components/cv-document-renderer` is the one
component behind every template. It takes a `CandidateProfile` (the
same model `CvApiService.getProfile` already returns), a section order,
a hidden-section list, and a `TemplateDefinition`, and renders through
six ATS-friendly templates (`ats-classic`, `ats-professional`,
`executive`, `modern-split`, `technical`, `minimal`) purely via
`[data-template]`/`[data-columns]` CSS variation - the candidate data is
never duplicated per template.

`features/cvs/pages/cv-editor` (`/cvs/:id/editor`) is a three-panel
workspace (sections, live document, properties) built around this
renderer. Its editing model is intentionally scoped:

- Reordering sections, hiding/showing a standard section, and adding a
  free-text custom section are always safe - they change presentation,
  not facts.
- Editing summary/experience/education text and removing individual
  skills/certifications/languages/projects is the candidate rewording or
  curating their own already-extracted content by hand.
- The editor **never calls a backend endpoint to persist these edits**.
  All state lives in-memory (`CvEditorComponent`'s signals, with a
  snapshot-based undo/redo stack) and feeds only the renderer and the
  print-based export. This is a deliberate boundary: the Phase 5 Truth
  Layer and claim validation (`domain/truth/claim_validation.py`) remain
  the sole authority over what counts as a verified candidate fact for
  anything AI-generated. A free-text CV editor that could silently
  become a second, unvalidated channel for candidate facts would
  undermine that guarantee, so this editor stops at presentation and the
  candidate's own hand-typed wording, and never reaches tailoring's
  generation/validation pipeline.

`features/templates/pages/template-gallery` (`/templates`) previews all
six templates at full size using the visitor's own most recent
processed CV when one exists, falling back to a clearly-labelled sample
profile (`features/templates/models/sample-profile.ts`) - never a
fabricated "real" candidate.

## Export

Export is the CV editor's final step, not a separate page (a separate
route would have needed to persist the editor's working state
somewhere, and there is deliberately no backend endpoint for that - see
above). `CvEditorComponent.downloadPdf()` adds a `cv-printing` class to
`<body>` and calls `window.print()`; a scoped `@media print` rule in
`styles.scss` hides everything except the rendered `.cv-page` and
promotes it to fill the printed page. This needed no new dependency and
preserves the selected template exactly, because it prints the same DOM
the editor already renders. The panel also shows a page-count estimate
computed from the actual rendered height of `.cv-page`, not a guess.

DOCX export was evaluated and deliberately not built in this pass: it
would require either a new client-side library (e.g. `docx`) or backend
work, and the PDF path already gives every template exactly. It is
noted as a known limitation rather than shipped as a non-functional
button.

## Brand refinement pass

A follow-up pass kept the same architecture and safety boundaries above
and added:

- **Brand palette**: `_tokens.scss` values were replaced with the
  CVScanner brand system (a primary/deep blue accent, a teal/cyan
  secondary hue reserved for gradients and brand moments via
  `--gradient-brand`, and a cool near-white `--surface-base` instead of
  a warmer neutral) - the token *names* and the decoupled-semantics
  strategy from the initial pass are unchanged, so this was a values-only
  swap every consuming component picked up automatically. `_typography.scss`
  swapped the UI font from IBM Plex Sans to Inter, keeping Space Grotesk
  for display and IBM Plex Mono for data - still three families total,
  not four.
- **Sidebar**: `layout/sidebar` is now collapsible (264px/72px, remembered
  via `SidebarStateService` + `localStorage`) with native-title tooltips
  when collapsed, and a mobile slide-in drawer (left-anchored,
  `transform: translateX(-100%)` when closed) opened from a new header
  hamburger trigger - replacing the old horizontal-scrolling nav row.
- **Workspace hero**: the home page leads with a real product
  introduction (headline, explanation, primary/secondary CTAs, and a
  `DocumentPreview`-based CV+Job -> Analysis -> Tailored CV diagram)
  above the existing Active Applications list, rather than starting
  directly with the applications utility.
- **`ApplicationSessionService`** (`features/applications/services`):
  persists the current cv/job/analysis/tailoring/template ids in
  `sessionStorage` as the guided journey progresses. Its main practical
  effect is that `TailoringDetailComponent`, once a plan is `COMPLETED`,
  resolves the real candidate document id (via the analysis) and offers
  "Continue to templates & CV editor," opening the editor with
  `?tailoringId=<id>` so `applyTailoringChanges` (`features/cvs/utils`)
  projects the plan's *accepted* changes onto the original profile
  before rendering - the tailored CV is now viewed through the same
  template engine as any other CV, per the brief's requirement that
  tailoring output not stop at diff cards.
- **CV editor upgrades**: section reordering is now drag-and-drop
  (`@angular/cdk/drag-drop` - the one new dependency this pass added,
  justified because arrow buttons cannot express "move to any position
  in one gesture" the way the brief's example does); `CvDocumentRenderer`
  gained an opt-in `interactive`/`selectedSectionId` mode so clicking a
  section directly in the rendered document selects it (off by default,
  so the template gallery and any future read-only preview stay
  non-interactive); and experience/education/project entries can now be
  individually added, duplicated, and deleted, with skills/
  certifications/languages gaining an "add" row alongside the existing
  per-item remove control.

A real bug surfaced while stabilizing tests for this pass: an `effect()`
registered in the editor's constructor (to mirror `templateId` into the
session service) leaked across component instances in the test runner
and pegged the browser's event loop, causing widespread flaky
disconnects across the whole suite. It was replaced with a plain method
call at the two actual template-change call sites - no reactive
`effect()` is used in the editor.

## Known limitations

- DOCX export is not implemented (see "Export" above).
- The page-count estimate in the export panel is a real DOM measurement
  but is still an estimate, not a guarantee of the final printed PDF's
  exact pagination (actual page breaks depend on the browser's print
  engine).
- The CV editor covers full add/duplicate/delete/edit for experience,
  education, and project entries, an add/remove row for skills/
  certifications/languages, and reordering for sections; it does not
  expose reordering of repeated items *within* one section (e.g.
  moving one experience entry above another) or achievement-bullet-level
  editing.
- Tailoring is viewable as a real rendered CV via "Continue to templates
  & CV editor," but the tailoring results page itself still shows
  changes as diff cards rather than a full document preview inline.
- The template gallery's preview cards are scaled-down full renders
  (not separately generated thumbnail images), which keeps them exactly
  in sync with the real templates at the cost of some fine text being
  small at a glance before a template is opened in the editor.
