"""
PDF Layout Analyzer 

BƯỚC 1: WORD EXTRACTION
  - pdfplumber: words với (text, x0, x1, top, bottom, size)
  - Unicode NFC normalize

BƯỚC 2: LINE ASSEMBLY
  - Gom words thành lines theo Y-coordinate similarity
  - abs(y_center1 - y_center2) < max(h1, h2) * 0.4
  - Sort words trong line theo x0

BƯỚC 3: BLOCK DETECTION
  - Gom lines → blocks
  - 1D gap clustering (tables)
  - Classify block: full_width_header | left_col | right_col | full_width_body

BƯỚC 4: READING ORDER ASSEMBLY
  - Output: list[{page, type, text}]
  - Join: full_width_header → left_col → right_col
"""

import logging
import unicodedata
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class Word:
    """Từ trong PDF với tọa độ"""
    text: str
    x0: float
    x1: float
    top: float
    bottom: float
    size: float
    
    @property
    def height(self) -> float:
        return self.bottom - self.top
    
    @property
    def width(self) -> float:
        return self.x1 - self.x0


@dataclass
class PDFLine:
    """Dòng trong PDF gồm nhiều words"""
    words: List[Word] = field(default_factory=list)
    
    @property
    def text(self) -> str:
        """Ghép text của tất cả words"""
        return " ".join(w.text for w in self.words)
    
    @property
    def y_center(self) -> float:
        """Y coordinate trung tâm"""
        if not self.words:
            return 0
        tops = [w.top for w in self.words]
        bottoms = [w.bottom for w in self.words]
        return (sum(tops) + sum(bottoms)) / (2 * len(self.words))
    
    @property
    def height(self) -> float:
        """Chiều cao của line"""
        if not self.words:
            return 0
        return max(w.bottom for w in self.words) - min(w.top for w in self.words)
    
    @property
    def x_span_start(self) -> float:
        """X start (leftmost)"""
        return min(w.x0 for w in self.words) if self.words else 0
    
    @property
    def x_span_end(self) -> float:
        """X end (rightmost)"""
        return max(w.x1 for w in self.words) if self.words else 0
    
    @property
    def x_span(self) -> float:
        """Chiều rộng content"""
        return self.x_span_end - self.x_span_start
    
    @property
    def x_center(self) -> float:
        """X coordinate trung tâm"""
        return (self.x_span_start + self.x_span_end) / 2


@dataclass
class PDFBlock:
    """Block (nhóm lines) trong PDF"""
    lines: List[PDFLine] = field(default_factory=list)
    block_type: str = ""  # "full_width_header", "left_col", "right_col", "full_width_body", "table_row"
    
    @property
    def text(self) -> str:
        """Ghép text của tất cả lines"""
        # Nếu là table block, return markdown table
        if self.block_type == "table":
            return self._format_table()
        return "\n".join(line.text for line in self.lines)
    
    def _format_table(self) -> str:
        """Format lines thành Markdown table"""
        if not self.lines:
            return ""
        
        # Parse cells từ dari mỗi line
        rows = []
        for line in self.lines:
            cells = [w.text for w in line.words]
            rows.append("| " + " | ".join(cells) + " |")
        
        if len(rows) < 2:
            return "\n".join(rows)
        
        # Add separator
        header = rows[0]
        separator = "|" + "|".join(["---"] * (header.count("|") - 1)) + "|"
        body = "\n".join(rows[1:])
        
        return f"{header}\n{separator}\n{body}"


class PDFLayoutAnalyzer:
    """Analyzer cho PDF layout theo 4 bước"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pages_data: List[Dict] = []
        
    def analyze(self, page_range: Optional[Tuple[int, int]] = None) -> List[Dict]:
        """
        Full analysis pipeline: extract → line assembly → block detection → reading order
        
        Args:
            page_range: (start, end) page indices (0-based), None for all pages
        
        Returns:
            list[{page: int, type: str, text: str}]
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Determine page range
                if page_range:
                    start, end = page_range
                else:
                    start, end = 0, len(pdf.pages)
                
                for page_idx in range(start, min(end, len(pdf.pages))):
                    page = pdf.pages[page_idx]
                    self._analyze_page(page, page_idx)
            
            return self.pages_data
        
        except Exception as e:
            logger.error(f"Error analyzing PDF {self.pdf_path}: {e}")
            return []
    
    def _analyze_page(self, page: Any, page_idx: int) -> None:
        """Analyze một trang"""
        # Bước 1: Word Extraction
        words = self._extract_words(page)
        if not words:
            return
        
        # Bước 2: Line Assembly
        lines = self._assemble_lines(words)
        if not lines:
            return
        
        # Bước 3: Block Detection
        blocks = self._detect_blocks(lines, page)
        
        # Bước 4: Reading Order Assembly
        self._assemble_reading_order(blocks, page_idx)
    
    def _extract_words(self, page: Any) -> List[Word]:
        """
        BƯỚC 1: Word Extraction
        Extract words từ page với tọa độ
        """
        words = []
        
        for word_obj in page.extract_words():
            # Unicode NFC normalize
            text = unicodedata.normalize('NFC', word_obj['text'])
            
            word = Word(
                text=text,
                x0=word_obj['x0'],
                x1=word_obj['x1'],
                top=word_obj['top'],
                bottom=word_obj['bottom'],
                size=word_obj.get('size', 0)
            )
            words.append(word)
        
        logger.debug(f"Extracted {len(words)} words")
        return words
    
    def _assemble_lines(self, words: List[Word]) -> List[PDFLine]:
        """
        BƯỚC 2: Line Assembly
        Gom words thành lines:
        abs(y_center1 - y_center2) < max(h1, h2) * 0.4
        Sort words trong line theo x0
        """
        if not words:
            return []
        
        # Sort words by top position first
        sorted_words = sorted(words, key=lambda w: (w.top, w.x0))
        
        lines = []
        current_line_words = [sorted_words[0]]
        
        for word in sorted_words[1:]:
            # Check if word should be in current line
            last_word = current_line_words[-1]
            
            # Calculate y_center of last word in line
            if len(current_line_words) > 1:
                y_centers = [(w.top + w.bottom) / 2 for w in current_line_words]
                y_center_last = sum(y_centers) / len(y_centers)
            else:
                y_center_last = (last_word.top + last_word.bottom) / 2
            
            y_center_current = (word.top + word.bottom) / 2
            
            # Threshold
            max_h = max(last_word.height, word.height)
            threshold = max_h * 0.4
            
            if abs(y_center_current - y_center_last) < threshold:
                # Same line
                current_line_words.append(word)
            else:
                # New line
                if current_line_words:
                    # Sort words in line by x0
                    current_line_words.sort(key=lambda w: w.x0)
                    lines.append(PDFLine(words=current_line_words))
                current_line_words = [word]
        
        # Don't forget last line
        if current_line_words:
            current_line_words.sort(key=lambda w: w.x0)
            lines.append(PDFLine(words=current_line_words))
        
        logger.debug(f"Assembled {len(lines)} lines")
        return lines
    
    def _detect_blocks(self, lines: List[PDFLine], page: Any) -> List[PDFBlock]:
        """
        BƯỚC 3: Block Detection
        3a. Gom lines → blocks (gap < 1.0 * median_line_height + x_center lệch < 20%)
        3b. 1D gap clustering (tables)
        3c. Classify block
        """
        if not lines:
            return []
        
        page_width = page.width
        page_height = page.height
        
        # Calculate median line height
        line_heights = [line.height for line in lines if line.height > 0]
        median_line_height = sorted(line_heights)[len(line_heights) // 2] if line_heights else 10
        
        # 3a: Group lines into blocks
        blocks_raw = []
        current_block_lines = [lines[0]]
        
        for i in range(1, len(lines)):
            prev_line = lines[i - 1]
            curr_line = lines[i]
            
            # Gap between lines
            gap = curr_line.y_center - prev_line.y_center - prev_line.height / 2
            
            # X-center deviation
            x_deviation = abs(curr_line.x_center - prev_line.x_center)
            x_threshold = page_width * 0.2
            
            # Check if same block
            if gap < 1.0 * median_line_height and x_deviation < x_threshold:
                current_block_lines.append(curr_line)
            else:
                # New block
                if current_block_lines:
                    blocks_raw.append(PDFBlock(lines=current_block_lines))
                current_block_lines = [curr_line]
        
        if current_block_lines:
            blocks_raw.append(PDFBlock(lines=current_block_lines))
        
        # 3b: Detect table rows via 1D gap clustering
        blocks_with_tables = self._detect_table_rows(blocks_raw, page_width)
        
        # 3c: Classify blocks
        blocks = self._classify_blocks(blocks_with_tables, page_width)
        
        logger.debug(f"Detected {len(blocks)} blocks")
        return blocks
    
    def _detect_table_rows(self, blocks: List[PDFBlock], page_width: float) -> List[PDFBlock]:
        """
        3b: Detect table rows via 1D gap clustering
        gap > 8% page width → "table_row"
        table_rows liên tiếp → Markdown table
        """
        result_blocks = []
        
        for block in blocks:
            if len(block.lines) < 2:
                result_blocks.append(block)
                continue
            
            # Analyze gaps in x0 coordinates for each line
            table_candidate = True
            for line in block.lines:
                if len(line.words) < 2:
                    table_candidate = False
                    break
                
                # Calculate gaps between consecutive words
                gaps = []
                for i in range(1, len(line.words)):
                    gap = line.words[i].x0 - line.words[i - 1].x1
                    gaps.append(gap)
                
                # Check if there's a significant gap (> 8% page width)
                large_gap_threshold = page_width * 0.08
                has_large_gap = any(gap > large_gap_threshold for gap in gaps)
                
                if not has_large_gap:
                    table_candidate = False
                    break
            
            if table_candidate and len(block.lines) >= 2:
                block.block_type = "table"
            
            result_blocks.append(block)
        
        return result_blocks
    
    def _classify_blocks(self, blocks: List[PDFBlock], page_width: float) -> List[PDFBlock]:
        """
        3c: Classify blocks
        Tiêu chí header (5 conditions):
          1. Không có word khác cùng dải Y
          2. x_span < 60% page width
          3. Vertical gap trên+dưới > 1.5 * median_line_height
          4. Không kết thúc bằng dấu câu (trừ ":")
          5. x_center thuộc 30% trái hoặc 50% giữa trang
        """
        # Calculate median line height for vertical gap calculation
        all_heights = []
        for block in blocks:
            for line in block.lines:
                if line.height > 0:
                    all_heights.append(line.height)
        
        median_line_height = sorted(all_heights)[len(all_heights) // 2] if all_heights else 10
        
        # Classify each block
        for block in blocks:
            if block.block_type == "table":
                continue  # Already classified
            
            is_header = self._is_header_block(block, page_width, median_line_height)
            
            if is_header:
                block.block_type = "full_width_header"
            else:
                block.block_type = "full_width_body"
        
        # Detect left/right columns
        blocks = self._detect_columns(blocks, page_width)
        
        return blocks
    
    def _is_header_block(self, block: PDFBlock, page_width: float, median_line_height: float) -> bool:
        """Check if block is header based on 5 conditions"""
        
        # Condition 1: Only one line (single row)
        if len(block.lines) != 1:
            return False
        
        line = block.lines[0]
        
        # Condition 2: x_span < 60% page width
        if line.x_span > page_width * 0.6:
            return False
        
        # Condition 3: Vertical gap > 1.5 * median_line_height (skip for now - need page layout)
        # This would require tracking gaps above/below the block in page context
        
        # Condition 4: Không kết thúc bằng dấu câu (trừ ":")
        text = line.text.strip()
        if text and text[-1] in '.,:;!?':
            if text[-1] != ':':
                return False
        
        # Condition 5: x_center thuộc 30% trái hoặc 50% giữa
        x_center = line.x_center
        left_bound = page_width * 0.3
        middle_start = page_width * 0.25
        middle_end = page_width * 0.75
        
        if x_center <= left_bound or (middle_start <= x_center <= middle_end):
            return True
        
        return False
    
    def _detect_columns(self, blocks: List[PDFBlock], page_width: float) -> List[PDFBlock]:
        """
        Detect left vs right columns
        gap > 10% page width → 2 columns
        """
        if len(blocks) < 2:
            return blocks
        
        # Group blocks by columns
        left_blocks = []
        right_blocks = []
        col_threshold = page_width * 0.5  # Middle of page
        
        for block in blocks:
            # Use first line's x_center to decide
            if block.lines:
                x_center = block.lines[0].x_center
                if x_center < col_threshold:
                    left_blocks.append(block)
                else:
                    right_blocks.append(block)
        
        # Check if we have significant gap between columns
        if left_blocks and right_blocks:
            max_right_of_left = max(b.lines[0].x_span_end for b in left_blocks if b.lines)
            min_left_of_right = min(b.lines[0].x_span_start for b in right_blocks if b.lines)
            
            gap = min_left_of_right - max_right_of_left
            
            if gap > page_width * 0.10:
                # 2 columns detected
                for block in left_blocks:
                    if block.block_type not in ["full_width_header", "table"]:
                        block.block_type = "left_col"
                
                for block in right_blocks:
                    if block.block_type not in ["full_width_header", "table"]:
                        block.block_type = "right_col"
        
        return blocks
    
    def _assemble_reading_order(self, blocks: List[PDFBlock], page_idx: int) -> None:
        """
        BƯỚC 4: Reading Order Assembly
        Output: list[{page, type, text}]
        Thứ tự: full_width_header → left_col → right_col → full_width_body → table
        """
        if not blocks:
            return
        
        # Sort blocks by type (reading order)
        type_order = {
            "full_width_header": 0,
            "left_col": 1,
            "right_col": 2,
            "full_width_body": 3,
            "table": 4,
        }
        
        blocks_sorted = sorted(blocks, key=lambda b: type_order.get(b.block_type, 99))
        
        for block in blocks_sorted:
            if block.lines:  # Only add non-empty blocks
                self.pages_data.append({
                    "page": page_idx + 1,
                    "type": block.block_type,
                    "text": block.text.strip()
                })


def format_markdown_dump(pages_data: List[Dict]) -> str:
    """
    Format BƯỚC 4 output thành Markdown dump
    (Dump format, không phải Markdown đẹp)
    """
    output = []
    
    for item in pages_data:
        page = item["page"]
        block_type = item["type"].upper()
        text = item["text"]
        
        output.append("=" * 40)
        output.append(f"PAGE: {page} | TYPE: {block_type}")
        output.append("=" * 40)
        output.append(text)
        output.append("")
    
    return "\n".join(output)
