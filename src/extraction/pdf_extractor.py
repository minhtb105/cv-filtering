"""
PDF Extraction Module — Geometric 5-Step Pipeline

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

import re
import unicodedata
import statistics
import logging
from typing import List, Tuple, Dict

from src.models.extraction.pdf_dataclasses import (
    Word, Line, Block, PageGeometry, ExtractionResult
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# STEP 1 — Word extraction
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def extract_words_from_page(page, page_num: int) -> Tuple[List[Word], PageGeometry]:
    """Extract all words with coordinates from a PyMuPDF page."""
    rect = page.rect
    geom = PageGeometry(width=rect.width, height=rect.height, page_num=page_num)

    raw_words = page.get_text("words")  # (x0, y0, x1, y1, text, block_no, line_no, word_no)
    words = []
    for w in raw_words:
        x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
        text = _normalize(text.strip())
        if not text:
            continue
        words.append(Word(text=text, x0=x0, y0=y0, x1=x1, y1=y1, page=page_num))

    return words, geom


# ---------------------------------------------------------------------------
# STEP 2 — Line assembly
# ---------------------------------------------------------------------------

def assemble_lines(words: List[Word], page_num: int) -> List[Line]:
    """Group words into lines by Y proximity, sort each line by X."""
    if not words:
        return []

    # Sort words top-to-bottom, then left-to-right
    words_sorted = sorted(words, key=lambda w: (w.y_center, w.x0))

    lines: List[Line] = []
    current: List[Word] = [words_sorted[0]]

    for word in words_sorted[1:]:
        ref = current[-1]
        y_diff = abs(word.y_center - ref.y_center)
        max_h = max(word.height, ref.height)
        threshold = max_h * 0.4

        if y_diff <= threshold:
            current.append(word)
        else:
            # Sort current line by x0 before saving
            current.sort(key=lambda w: w.x0)
            lines.append(Line(words=current, page=page_num))
            current = [word]

    if current:
        current.sort(key=lambda w: w.x0)
        lines.append(Line(words=current, page=page_num))

    return lines


# ---------------------------------------------------------------------------
# STEP 3a — Group lines into blocks
# ---------------------------------------------------------------------------

def _median_line_height(lines: List[Line]) -> float:
    heights = [ln.height for ln in lines if ln.height > 0]
    if not heights:
        return 12.0
    return statistics.median(heights)


def group_lines_into_blocks(lines: List[Line], page_geom: PageGeometry) -> List[Block]:
    """Group consecutive lines into blocks based on vertical gap and x alignment."""
    if not lines:
        return []

    med_h = _median_line_height(lines)
    page_w = page_geom.width

    blocks: List[Block] = []
    current: List[Line] = [lines[0]]

    for ln in lines[1:]:
        prev = current[-1]
        v_gap = ln.y0 - prev.y1
        x_shift = abs(ln.x_center - prev.x_center)

        same_block = (
            v_gap < 1.0 * med_h
            and x_shift < 0.20 * page_w
        )

        if same_block:
            current.append(ln)
        else:
            blocks.append(Block(lines=current, page=current[0].page))
            current = [ln]

    if current:
        blocks.append(Block(lines=current, page=current[0].page))

    return blocks


# ---------------------------------------------------------------------------
# STEP 3b — Table detection via 1D gap clustering
# ---------------------------------------------------------------------------

def _detect_table_lines(lines: List[Line], page_w: float) -> List[bool]:
    """Return bool mask: True if line looks like a table row."""
    is_table = []
    for ln in lines:
        xs = sorted(w.x0 for w in ln.words)
        if len(xs) < 2:
            is_table.append(False)
            continue
        gaps = [xs[i+1] - xs[i] for i in range(len(xs)-1)]
        max_gap = max(gaps)
        is_table.append(max_gap > 0.08 * page_w)
        
    return is_table


def lines_to_markdown_table(table_lines: List[Line]) -> str:
    """Convert a sequence of table rows to Markdown table."""
    rows = []
    for ln in table_lines:
        cells = [w.text for w in ln.words]
        rows.append(cells)

    if not rows:
        return ""

    max_cols = max(len(r) for r in rows)
    header = rows[0]
    # Pad header to max_cols
    header = header + [""] * (max_cols - len(header))
    separator = ["---"] * max_cols
    body = rows[1:] if len(rows) > 1 else []

    lines_out = []
    lines_out.append("| " + " | ".join(header) + " |")
    lines_out.append("| " + " | ".join(separator) + " |")
    for row in body:
        padded = row[:max_cols] + [""] * max(0, max_cols - len(row))
        lines_out.append("| " + " | ".join(padded) + " |")

    return "\n".join(lines_out)


# ---------------------------------------------------------------------------
# STEP 3c — Block classification (FIXED: Rule 5 mở rộng)
# ---------------------------------------------------------------------------

SENTENCE_ENDING = re.compile(r'[.!?,;]$')


def _looks_like_header(text: str) -> bool:
    """
    Rule 4: text không kết thúc bằng . ! ? , (nhưng : được phép).
    """
    text = text.strip()
    if not text:
        return False
    return text[-1] not in ".!?,"


def classify_blocks(
    blocks: List[Block],
    all_lines: List[Line],
    page_geom: PageGeometry,
    med_h: float,
) -> List[Block]:
    """
    Classify blocks với 5 geometric rules.
    
    FIX v1.1: Rule 5 mở rộng từ [0.30, 0.70] → [0.05, 0.95]
    Lý do: CV headers thường căn trái (x_center ~0.10-0.25 với 2-column layout),
    cũng có thể căn giữa (x_center ~0.45-0.55). Rule 5 ban đầu loại hết left-aligned headers.
    
    Thực tế: Rules 1-3 đã đủ mạnh để loại false positives. Rule 5 chỉ nên
    loại bỏ content nằm TẬN CÙNG LỀ (< 5% hoặc > 95%) — thường là page numbers,
    watermarks, không phải section headers.
    """
    page_w = page_geom.width
    all_words_on_page = [wd for ln in all_lines for wd in ln.words]

    for block in blocks:
        # Chỉ single-line blocks mới có thể là full_width_header
        if len(block.lines) == 1:
            ln = block.lines[0]
            text = ln.text.strip()

            # RULE 1: Không có word nào khác cùng Y-band trên toàn trang
            y_band = ln.y_center
            y_tol = ln.height * 0.5
            others = [
                wd for wd in all_words_on_page
                if abs(wd.y_center - y_band) <= y_tol
                and (wd.x1 < ln.x0 - 5 or wd.x0 > ln.x1 + 5)
            ]
            rule1 = len(others) == 0

            # RULE 2: x_span < 60% page width
            rule2 = ln.x_span < 0.60 * page_w

            # RULE 3: Gap trên VÀ dưới > 1.5 × median_line_height
            gap_above = float('inf')
            gap_below = float('inf')
            lines_above = [l for l in all_lines if l.y1 < ln.y0]
            if lines_above:
                closest_above = max(lines_above, key=lambda l: l.y1)
                gap_above = ln.y0 - closest_above.y1
            lines_below = [l for l in all_lines if l.y0 > ln.y1]
            if lines_below:
                closest_below = min(lines_below, key=lambda l: l.y0)
                gap_below = closest_below.y0 - ln.y1
            threshold_gap = 1.5 * med_h
            rule3 = (gap_above > threshold_gap) and (gap_below > threshold_gap)

            # RULE 4: Không kết thúc bằng sentence-ending punctuation
            rule4 = _looks_like_header(text)

            # RULE 5 (FIXED): x_center không ở tận cùng lề trang
            # Mở rộng từ [0.30, 0.70] → [0.05, 0.95]
            # Loại: page numbers, watermarks ở tận góc
            # Giữ: left-aligned headers, centered headers, right-aligned headers
            x_center_normalized = ln.x_center / page_w
            rule5 = 0.05 <= x_center_normalized <= 0.95

            if rule1 and rule2 and rule3 and rule4 and rule5:
                block.block_type = "full_width_header"
                continue

        # Position-based classification
        b_xc = block.x_center / page_w
        b_xs = block.x_span / page_w

        if b_xs >= 0.75:
            block.block_type = "full_width_body"
        elif b_xc < 0.45:
            block.block_type = "left_col"
        else:
            block.block_type = "right_col"

    return blocks


# ---------------------------------------------------------------------------
# STEP 4 — Reading order assembly (FIXED: y0 làm primary sort key)
# ---------------------------------------------------------------------------

def assemble_reading_order(
    page_blocks: Dict[int, List[Block]],
    page_geoms: Dict[int, PageGeometry],
) -> str:
    """
    Produce intermediate markdown dump.
    
    FIX v1.1: Reading order cho single-column CVs
    
    Vấn đề cũ: sort by (type_priority, y0) → tất cả headers lên đầu,
    mất interleaving header-content trong trang. Output lộn xộn với LLM.
    
    Fix mới: detect layout type:
    - Two-column layout (có cả left_col và right_col): dùng sort cũ
      (full_width_header → left_col → right_col → body)
    - Single-column layout: dùng y0 làm primary key, giữ đúng thứ tự dọc
    
    Kết quả: LLM nhận được text đúng thứ tự, context tốt hơn.
    """
    output_parts = []

    for page_num in sorted(page_blocks.keys()):
        blocks = page_blocks[page_num]
        geom = page_geoms[page_num]

        if not blocks:
            continue

        left_blocks = [b for b in blocks if b.block_type == "left_col"]
        right_blocks = [b for b in blocks if b.block_type == "right_col"]
        has_two_cols = bool(left_blocks and right_blocks)

        if has_two_cols:
            # Two-column layout: full_width_header → left_col → right_col
            def sort_key_two_col(b: Block):
                order = {
                    "full_width_header": 0,
                    "left_col": 1,
                    "right_col": 2,
                    "full_width_body": 3,
                    "table": 4,
                    "unknown": 5,
                }
                return (order.get(b.block_type, 5), b.y0)
            sorted_blocks = sorted(blocks, key=sort_key_two_col)
        else:
            # Single-column layout: dùng y0 làm primary key
            # type chỉ là tiebreaker (header trước body nếu cùng y0)
            def sort_key_single_col(b: Block):
                type_order = {
                    "full_width_header": 0,
                    "full_width_body": 1,
                    "left_col": 2,
                    "right_col": 3,
                    "table": 4,
                    "unknown": 5,
                }
                return (b.y0, type_order.get(b.block_type, 5))
            sorted_blocks = sorted(blocks, key=sort_key_single_col)

        block_idx = 0
        for block in sorted_blocks:
            block_idx += 1
            sep = "=" * 40
            label = f"PAGE: {page_num} | TYPE: {block.block_type.upper()}"
            if block.block_type not in ("full_width_header", "full_width_body"):
                label += f" | BLOCK: {block_idx}"
            header_line = f"{sep}\n{label}\n{sep}"

            content = getattr(block, "_md_override", None) or block.text
            content = content.strip()
            if content:
                output_parts.append(f"{header_line}\n{content}")

    return "\n\n".join(output_parts)


def assemble_plain_text(
    page_blocks: Dict[int, List[Block]],
) -> str:
    """Produce clean ordered plain text for downstream LLM use."""
    parts = []
    for page_num in sorted(page_blocks.keys()):
        blocks = page_blocks[page_num]

        left_blocks = [b for b in blocks if b.block_type == "left_col"]
        right_blocks = [b for b in blocks if b.block_type == "right_col"]
        has_two_cols = bool(left_blocks and right_blocks)

        if has_two_cols:
            def sort_key(b):
                order = {"full_width_header": 0, "left_col": 1, "right_col": 2,
                         "full_width_body": 3, "table": 4, "unknown": 5}
                return (order.get(b.block_type, 5), b.y0)
        else:
            def sort_key(b):
                type_order = {"full_width_header": 0, "full_width_body": 1,
                              "left_col": 2, "right_col": 3, "table": 4, "unknown": 5}
                return (b.y0, type_order.get(b.block_type, 5))

        for block in sorted(blocks, key=sort_key):
            text = getattr(block, "_md_override", None) or block.text
            text = text.strip()
            if text:
                parts.append(text)

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Main extractor class
# ---------------------------------------------------------------------------

class PDFExtractor:
    """Geometric PDF extractor — 5-step pipeline (fixed v1.1)."""

    def extract(self, pdf_path: str) -> ExtractionResult:
        try:
            import fitz
        except ImportError:
            logger.warning("PyMuPDF not installed, falling back to pdfplumber")
            return self._fallback_pdfplumber(pdf_path)

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            return ExtractionResult(
                intermediate_markdown="",
                full_text="",
                total_pages=0,
                is_success=False,
                error=str(e),
            )

        page_blocks: Dict[int, List[Block]] = {}
        page_geoms: Dict[int, PageGeometry] = {}

        for page_num, page in enumerate(doc, start=1):
            words, geom = extract_words_from_page(page, page_num)
            page_geoms[page_num] = geom

            if not words:
                page_blocks[page_num] = []
                continue

            lines = assemble_lines(words, page_num)
            med_h = _median_line_height(lines)
            blocks = group_lines_into_blocks(lines, geom)

            processed_blocks: List[Block] = []
            table_accum: List[Line] = []

            def flush_table(page_num=page_num):
                if len(table_accum) >= 2:
                    md_table = lines_to_markdown_table(table_accum)
                    tb = Block(lines=list(table_accum), page=page_num, block_type="table")
                    tb._md_override = md_table
                    processed_blocks.append(tb)
                elif table_accum:
                    processed_blocks.append(Block(lines=list(table_accum), page=page_num))
                table_accum.clear()

            for block in blocks:
                is_tbl = _detect_table_lines(block.lines, geom.width)
                if all(is_tbl) and len(block.lines) >= 2:
                    table_accum.extend(block.lines)
                else:
                    flush_table()
                    processed_blocks.append(block)

            flush_table()
            classify_blocks(processed_blocks, lines, geom, med_h)
            page_blocks[page_num] = processed_blocks

        doc.close()

        intermediate_md = assemble_reading_order(page_blocks, page_geoms)
        full_text = assemble_plain_text(page_blocks)

        return ExtractionResult(
            intermediate_markdown=intermediate_md,
            full_text=full_text,
            total_pages=len(page_blocks),
            is_success=True,
        )

    def _fallback_pdfplumber(self, pdf_path: str) -> ExtractionResult:
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
            full_text = "\n\n".join(text_parts)
            return ExtractionResult(
                intermediate_markdown=full_text,
                full_text=full_text,
                total_pages=len(text_parts),
                is_success=bool(full_text),
                error="" if full_text else "No text extracted",
            )
        except Exception as e:
            return ExtractionResult(
                intermediate_markdown="",
                full_text="",
                total_pages=0,
                is_success=False,
                error=str(e),
            )
