"""
PDF Extraction Data Classes

STEP 1 — WORD EXTRACTION
  PyMuPDF: words with (text, x0, y0, x1, y1, block_no, line_no, word_no)
  Unicode NFC normalize all text

STEP 2 — LINE ASSEMBLY
  Group words into lines:
    abs(y_center1 - y_center2) < max(h1, h2) * 0.4
  Sort words within line by x0

STEP 3 — BLOCK DETECTION
  3a. Group lines → blocks
      vertical gap < 1.0 * median_line_height
      x_center shift < 20% page width
  3b. 1D gap clustering on x0 per line
      gap > 8% page width → "table_row"
      consecutive table_rows → Markdown table
  3c. Classify block:
      full_width_header | left_col | right_col | full_width_body
      Header criteria (5 geometric conditions):
        1. No other word at same Y band across full page width (cross-column)
        2. x_span < 60% page width
        3. Vertical gap above+below > 1.5 * median_line_height
        4. Does not end with sentence-ending punctuation (except ":")
        5. x_center is in left 30% OR center 50% of page

STEP 4 — READING ORDER ASSEMBLY
  Per page: full_width_header → left_col → right_col
  Output intermediate markdown dump (not pretty, just structured)

STEP 5A — NO-LLM (regex only, ~75-80% accuracy)
  Regex matches standalone single-line headers
  No trailing punctuation, no font-size dependency

STEP 5B — LLM (optional, ~95%+ accuracy)
  Pure ordered text → JSON schema via prompt
"""

import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page: int

    @property
    def y_center(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def x_center(self) -> float:
        return (self.x0 + self.x1) / 2


@dataclass
class Line:
    words: List[Word]
    page: int

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)

    @property
    def x0(self) -> float:
        return min(w.x0 for w in self.words)

    @property
    def x1(self) -> float:
        return max(w.x1 for w in self.words)

    @property
    def y0(self) -> float:
        return min(w.y0 for w in self.words)

    @property
    def y1(self) -> float:
        return max(w.y1 for w in self.words)

    @property
    def y_center(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def x_center(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def x_span(self) -> float:
        return self.x1 - self.x0


@dataclass
class Block:
    lines: List[Line]
    page: int
    block_type: str = "unknown"  # full_width_header | left_col | right_col | full_width_body | table

    @property
    def text(self) -> str:
        return "\n".join(ln.text for ln in self.lines)

    @property
    def x0(self) -> float:
        return min(ln.x0 for ln in self.lines)

    @property
    def x1(self) -> float:
        return max(ln.x1 for ln in self.lines)

    @property
    def y0(self) -> float:
        return self.lines[0].y0 if self.lines else 0

    @property
    def y1(self) -> float:
        return self.lines[-1].y1 if self.lines else 0

    @property
    def x_center(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def x_span(self) -> float:
        return self.x1 - self.x0


@dataclass
class PageGeometry:
    width: float
    height: float
    page_num: int


@dataclass
class ExtractionResult:
    intermediate_markdown: str  # Step-4 dump
    full_text: str              # Plain ordered text (for LLM)
    total_pages: int
    is_success: bool
    error: str = ""