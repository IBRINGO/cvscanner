"""PDF parsing via pdfplumber, with layout-aware column detection.

pdfplumber is built on pdfminer.six (permissive license, pure Python plus
a pypdfium2 wheel for rendering) - no AGPL/vendor lock-in concern, and no
system-level dependency to install. Chosen specifically because it keeps
reliable page boundaries, which is required for page-aware evidence
(section 12 of the Phase 2 brief).

Two-column reading order (document-intelligence overhaul):

pdfplumber's own `extract_text_lines()` clusters words into lines purely
by vertical (y) proximity - it has no notion of columns, so on a
two-column page it silently *merges* same-row left-column and
right-column text into one interleaved line (confirmed empirically: a
"SKILLS" / "EXPERIENCE" side-by-side header comes back as the single
string "SKILLS EXPERIENCE"). That is the exact bug this module used to
have, and it stayed hidden because every existing fixture was single-
column.

The fix works entirely from `page.extract_words()` - never from
`extract_text_lines()` or `within_bbox()` cropping, both of which turned
out to have their own column-breaking failure mode: a *geometric* crop
clips objects at an exact x-coordinate regardless of word boundaries, so
a word (or a full-width header line) that happens to straddle the
column-gutter x-coordinate gets truncated mid-character, or a full-width
header line gets sliced into two pieces that each leak into the "wrong"
column. Instead:

    1. `_build_runs()` merges words into same-row, horizontally-
       contiguous *runs* - a run only breaks at a new row or an unusually
       large horizontal gap, so normal prose (small inter-word gaps)
       always stays one run, even a full-width header line that happens
       to extend past where a column boundary will end up.
    2. `_detect_column_boundary()` looks for a real column gutter using
       run *start* positions (see its docstring for why raw word
       positions don't work for this).
    3. Once a boundary is found, each *run* (never each word, never a
       geometric slice) is assigned wholesale to the column its start
       position falls in, then runs are regrouped into lines within
       each column. A run - and therefore a whole header line, or a
       whole word like "2022" that happens to end just past the gutter -
       is never split.

`extract_text()` alone joins every line with a single "\\n" regardless of
how much vertical whitespace separated them on the page - a blank line
between two CV entries (e.g. two Experience blocks) is visually obvious
but textually invisible. `_reconstruct_lines_from_runs` restores it by
comparing each row's vertical gap to its column's typical single-row
gap: a gap of roughly 1.6x or more means "there was a blank line here",
which is what domain/cv/policies.py's block-splitting (`\\n\\n`) depends
on to separate multiple entries within one section.

Each reconstructed line also carries font size and boldness (from
pdfplumber's per-word `size`/`fontname`) as a `LineRecord`, so
domain/cv/policies.py's heading scoring can use a genuinely larger/bolder
line as a heading signal, not just its text.
"""
import io
from statistics import median
from typing import NamedTuple

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException

from domain.documents.entities import LineRecord, ParsedBlock, ParsedDocument, ParsedPage
from domain.documents.exceptions import DocumentParsingError

_GAP_MULTIPLIER_FOR_BLANK_LINE = 1.6

# pdfplumber's own default (x_tolerance=3, a fixed point value) assumes
# real space characters exist in the PDF's text layer. Some real-world CV
# generators never emit one - they simulate a space purely by positioning
# the next glyph slightly further right, so the ONLY signal a word ended
# is a marginally bigger horizontal gap than the near-zero (often
# slightly negative, i.e. overlapping) kerning between letters *within*
# a word. Observed on a real CV: within-word gaps were -0.66..0.0pt,
# cross-word gaps were 1.38..2.48pt, at an ~9pt font - comfortably
# separated, but the "cross-word" gap can be *smaller* than pdfplumber's
# fixed 3pt default, which silently glues entire sentences into one
# "word" (confirmed: "Ingénieurd'Étatdiplômé..." as a single 357pt-wide
# token). A tolerance expressed as a *ratio* of font size, not a fixed
# point value, generalizes across the font sizes real CVs actually use;
# 0.12 sits with a wide safety margin above the observed kerning ceiling
# (~0.0) and below the observed real-space floor (~1.38/8.97 =~ 0.15) for
# that document, and produces byte-identical results to the pdfplumber
# default on this repo's synthetic (real-space-using) PDF fixtures.
_WORD_X_TOLERANCE_RATIO = 0.12

# Column-detection thresholds - see _detect_column_boundary()'s docstring
# for what each guards against. Deliberately conservative: it is far
# worse to scramble a normal single-column CV into a false two-column
# split than to miss a genuine (but unusually laid out) two-column CV.
_MIN_WORDS_FOR_COLUMN_DETECTION = 20
_MIN_RUNS_PER_COLUMN = 3
_MIN_GAP_POINTS = 30.0
_MIN_GAP_RATIO_OF_WIDTH = 0.04
_ROW_TOLERANCE = 2.0
_BIG_GAP_WITHIN_ROW = 25.0


class _RawLine(NamedTuple):
    text: str
    font_size: float | None
    is_bold: bool | None
    column_index: int | None


class PDFParser:
    """Implements infrastructure.document_processing.parsers.base.DocumentParser."""

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages: list[ParsedPage] = []
                blocks: list[ParsedBlock] = []
                line_records: list[LineRecord] = []
                position = 0

                for index, page in enumerate(pdf.pages, start=1):
                    page_lines = _extract_page_lines(page)
                    text = "\n".join(line.text for line in page_lines)
                    pages.append(ParsedPage(page_number=index, text=text))

                    for line in page_lines:
                        line_records.append(
                            LineRecord(
                                page_number=index,
                                text=line.text,
                                font_size=line.font_size,
                                is_bold=line.is_bold,
                                column_index=line.column_index,
                            )
                        )

                    for paragraph in _split_into_blocks(text):
                        blocks.append(
                            ParsedBlock(text=paragraph, page_number=index, position=position)
                        )
                        position += 1

                raw_text = "\n".join(page.text for page in pages)
        except PdfminerException as exc:
            raise DocumentParsingError(
                f"Could not parse PDF '{filename}': corrupted or unreadable content."
            ) from exc
        except Exception as exc:  # pdfplumber/pypdfium2 raise various backend-specific errors
            raise DocumentParsingError(
                f"Could not parse PDF '{filename}': {exc.__class__.__name__}."
            ) from exc

        if not raw_text.strip():
            raise DocumentParsingError(
                f"PDF '{filename}' contains no extractable text "
                "(it may be a scanned image - OCR is not implemented in Phase 2)."
            )

        return ParsedDocument(
            raw_text=raw_text,
            pages=pages,
            blocks=blocks,
            line_records=line_records,
            metadata={"parser": "pdfplumber", "page_count": len(pages)},
        )


def _extract_page_lines(page) -> list[_RawLine]:
    words = page.extract_words(extra_attrs=["fontname", "size"], x_tolerance_ratio=_WORD_X_TOLERANCE_RATIO)
    if not words:
        text = page.extract_text() or ""
        return [_RawLine(line, None, None, None) for line in text.splitlines()]

    runs = _build_runs(words)
    boundary = _detect_column_boundary(page.width, runs)

    if boundary is None:
        return _reconstruct_lines_from_runs(runs, column_index=None)

    left_runs = [run for run in runs if run["x0"] < boundary]
    right_runs = [run for run in runs if run["x0"] >= boundary]
    left_lines = _reconstruct_lines_from_runs(left_runs, column_index=0)
    right_lines = _reconstruct_lines_from_runs(right_runs, column_index=1)

    if not left_lines:
        return right_lines
    if not right_lines:
        return left_lines

    # A blank separator so extraction's blank-line block splitting never
    # silently merges the left column's last entry with the right
    # column's first one.
    return [*left_lines, _RawLine("", None, None, None), *right_lines]


def _build_runs(words: list[dict]) -> list[dict]:
    """Groups words into same-row, horizontally-contiguous runs, each
    carrying its own joined text and font metadata. A run only breaks at
    a new row or an unusually large horizontal gap - normal prose (small
    inter-word gaps) always stays one run, which is what makes a run's
    *start* x-position meaningful for column detection (every line's
    first run starts at that column's left margin - a raw word's x0
    does not, since every word past the first on a line starts wherever
    the previous word happened to end) and what makes assigning a whole
    run - never an individual word, never a geometric slice - to a
    column safe (see module docstring's part 3).
    """
    ordered = sorted(words, key=lambda w: (round(w["top"] / _ROW_TOLERANCE), w["x0"]))
    runs: list[dict] = []
    current: dict | None = None
    for word in ordered:
        if current is not None:
            same_row = abs(word["top"] - current["top"]) <= _ROW_TOLERANCE
            gap = word["x0"] - current["x1"]
            if same_row and gap < _BIG_GAP_WITHIN_ROW:
                current["x1"] = word["x1"]
                current["texts"].append(word["text"])
                current["sizes"].append(word.get("size"))
                current["fontnames"].append(word.get("fontname"))
                continue
            runs.append(current)
        current = {
            "top": word["top"],
            "x0": word["x0"],
            "x1": word["x1"],
            "texts": [word["text"]],
            "sizes": [word.get("size")],
            "fontnames": [word.get("fontname")],
        }
    if current is not None:
        runs.append(current)
    return runs


def _detect_column_boundary(page_width: float, runs: list[dict]) -> float | None:
    """Returns the x-coordinate splitting a two-column page into left and
    right halves, or None if the page looks single-column (including
    "not enough text to tell", which is treated as single-column).

    The largest gap between sorted run-start positions is the column
    gutter candidate; it is only accepted if it falls away from the
    page's own margins (15%-85% of page width), is wide enough to be a
    real gutter (not word spacing), and both sides have enough runs
    spread across enough of the page to be a real column rather than one
    stray right-aligned date next to a normal single-column line (a very
    common single-column pattern this must not misfire on).
    """
    total_words = sum(len(run["texts"]) for run in runs)
    if total_words < _MIN_WORDS_FOR_COLUMN_DETECTION:
        return None

    starts = sorted(run["x0"] for run in runs)
    if len(starts) < _MIN_RUNS_PER_COLUMN * 2:
        return None

    best_gap = 0.0
    best_split: float | None = None
    for left_x, right_x in zip(starts, starts[1:], strict=False):
        gap = right_x - left_x
        midpoint = (left_x + right_x) / 2
        if gap > best_gap and 0.15 * page_width < midpoint < 0.85 * page_width:
            best_gap = gap
            best_split = midpoint

    if best_split is None:
        return None

    threshold = max(_MIN_GAP_POINTS, page_width * _MIN_GAP_RATIO_OF_WIDTH)
    if best_gap < threshold:
        return None

    left_count = sum(1 for x in starts if x < best_split)
    right_count = len(starts) - left_count
    if left_count < _MIN_RUNS_PER_COLUMN or right_count < _MIN_RUNS_PER_COLUMN:
        return None

    return best_split


def _reconstruct_lines_from_runs(runs: list[dict], column_index: int | None) -> list[_RawLine]:
    """Regroups runs (already confined to one column, or all of them
    for a single-column page) into rows, joining same-row runs left to
    right with a single space - this is what lets e.g. a right-aligned
    date on the same visual row as a title still end up on one line,
    matching what pdfplumber's own line-grouping does for a single-
    column page. Then inserts a blank line wherever the vertical gap
    between consecutive rows is unusually large (same gap-based
    reasoning the pre-overhaul parser used, just applied to rows this
    module builds itself instead of pdfplumber's).
    """
    if not runs:
        return []

    rows: list[dict] = []
    for run in sorted(runs, key=lambda r: (round(r["top"] / _ROW_TOLERANCE), r["x0"])):
        if rows and abs(run["top"] - rows[-1]["top"]) <= _ROW_TOLERANCE:
            rows[-1]["runs"].append(run)
        else:
            rows.append({"top": run["top"], "runs": [run]})

    row_records: list[tuple[float, str, float | None, bool | None]] = []
    for row in rows:
        ordered_runs = sorted(row["runs"], key=lambda r: r["x0"])
        text = " ".join(" ".join(run["texts"]) for run in ordered_runs)
        sizes = [size for run in ordered_runs for size in run["sizes"] if size is not None]
        fontnames = [name for run in ordered_runs for name in run["fontnames"] if name]
        font_size = median(sizes) if sizes else None
        is_bold = any("bold" in name.lower() for name in fontnames) if fontnames else None
        row_records.append((row["top"], text, font_size, is_bold))

    tops = [top for top, *_ in row_records]
    gaps = [round(b - a, 1) for a, b in zip(tops, tops[1:], strict=False) if b > a]
    typical_gap = median(gaps) if gaps else 0

    _, first_text, first_size, first_bold = row_records[0]
    result: list[_RawLine] = [_RawLine(first_text, first_size, first_bold, column_index)]
    for previous, current in zip(row_records, row_records[1:], strict=False):
        gap = current[0] - previous[0]
        if typical_gap and gap > typical_gap * _GAP_MULTIPLIER_FOR_BLANK_LINE:
            result.append(_RawLine("", None, None, column_index))
        _, text, size, bold = current
        result.append(_RawLine(text, size, bold, column_index))
    return result


def _split_into_blocks(text: str) -> list[str]:
    return [block.strip() for block in text.split("\n\n") if block.strip()]
