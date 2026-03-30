"""
Enhanced Section Detection Module

Comprehensive section detection combining:
- Lightweight header detection (existing functionality)
- Regex-based section extraction (NoLLMExtractor from cv_reading_order.py)
- Multilingual support for section headers
- Integration with Geometric 5-step filter

No fuzzy matching, no heavy dependencies, but enhanced regex patterns.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ExtractedSection:
    """Extracted section data with confidence scoring"""
    section_type: str
    content: str
    confidence: float  # 0.0 to 1.0
    header_line: Optional[int] = None
    header_text: Optional[str] = None


class HeaderDetector:
    """
    Lightweight header detection using simple heuristics.
    
    Designed for integration with the Geometric 5-step filter pipeline.
    Focuses purely on header detection without complex matching or scoring.
    """
    
    @staticmethod
    def is_header_line(line: str) -> bool:
        """
        Check if line is likely a section header based on simple heuristics.
        
        Args:
            line: Text line to check
            
        Returns:
            True if line appears to be a section header, False otherwise
        """
        line_stripped = line.strip()
        
        # Empty or too long
        if not line_stripped or len(line_stripped) > 100:
            return False
            
        # Word count heuristic (sections are typically short phrases)
        word_count = len(line_stripped.split())
        if word_count > 6 or word_count < 1:
            return False
            
        # ALL CAPS → strong signal for section headers
        if line_stripped.isupper() and len(line_stripped) > 3:
            return True
            
        # Ends with colon or dash (common section markers)
        if line_stripped.endswith(':') or line_stripped.endswith('-'):
            return True
            
        # Contains common section keywords (simplified check)
        lower_line = line_stripped.lower()
        if any(keyword in lower_line for keyword in ['experience', 'education', 'skills', 'projects', 'summary']):
            return True
            
        return False
    
    @staticmethod
    def detect_headers(lines: List[str]) -> List[int]:
        """
        Detect header lines from a list of text lines.
        
        Args:
            lines: List of text lines from document
            
        Returns:
            List of line numbers (indices) that appear to be headers
        """
        return [i for i, line in enumerate(lines) if HeaderDetector.is_header_line(line)]
    
    @staticmethod
    def group_content_by_headers(lines: List[str]) -> List[Dict[str, Any]]:
        """
        Group content by detected headers for section extraction.
        
        Args:
            lines: List of text lines from document
            
        Returns:
            List of sections with header line number and content
        """
        header_lines = HeaderDetector.detect_headers(lines)
        sections = []
        
        for i, header_line_num in enumerate(header_lines):
            # Determine content boundaries
            start_line = header_line_num
            end_line = header_lines[i + 1] if i + 1 < len(header_lines) else len(lines)
            
            # Extract header text and content
            header_text = lines[start_line].strip()
            content_lines = lines[start_line + 1:end_line]
            
            # Clean content (remove empty lines at start/end)
            while content_lines and not content_lines[0].strip():
                content_lines.pop(0)
            while content_lines and not content_lines[-1].strip():
                content_lines.pop()
                
            sections.append({
                'header_line': start_line,
                'header_text': header_text,
                'content': content_lines,
                'content_text': '\n'.join(content_lines)
            })
            
        return sections


class RegexSectionExtractor:
    """
    Regex-based section extraction (NoLLMExtractor from cv_reading_order.py).
    Multilingual section header patterns with confidence scoring.
    Accuracy: ~75-80%
    Speed: Very fast (< 100ms)
    """

    # Multilingual section header patterns
    SECTION_PATTERNS = {
        "personal_info": {
            "en": [
                r"^(?:personal\s+info|contact\s+info|profile|personal\s+details)",
                r"^(?:name|email|phone|location|address)",
            ],
            "vi": [
                r"^(?:thông tin cá nhân|thông tin liên hệ|hồ sơ cá nhân)",
            ],
        },
        "summary": {
            "en": [
                r"^(?:summary|professional\s+summary|objective|profile\s+summary)",
                r"^(?:about|about\s+me|background)",
            ],
            "vi": [
                r"^(?:tóm tắt|tóm tắt chuyên môn|mục tiêu)",
            ],
        },
        "experience": {
            "en": [
                r"^(?:work\s+experience|professional\s+experience|employment|career|positions?)",
                r"^(?:experience|work\s+history|job\s+history)",
            ],
            "vi": [
                r"^(?:kinh nghiệm làm việc|kinh nghiệm|quá trình công tác)",
                r"^(?:công việc|lịch sử công việc|vị trí công việc)",
            ],
        },
        "education": {
            "en": [
                r"^(?:education|academic\s+background|academic|qualification|degree)",
                r"^(?:school|university|college|training)",
            ],
            "vi": [
                r"^(?:học vấn|trình độ học vấn|nền tảng học vấn)",
                r"^(?:đào tạo|bằng cấp|trường|đại học)",
            ],
        },
        "skills": {
            "en": [
                r"^(?:skills|technical\s+skills|competencies|expertise|proficiencies)",
                r"^(?:capabilities|technical\s+expertise|technical\s+knowledge)",
            ],
            "vi": [
                r"^(?:kỹ năng|kỹ năng kỹ thuật|năng lực|chuyên môn)",
            ],
        },
        "projects": {
            "en": [
                r"^(?:projects?|portfolio|case\s+studies?)",
                r"^(?:notable\s+projects?|key\s+projects?)",
            ],
            "vi": [
                r"^(?:dự án|danh sách dự án|các dự án)",
            ],
        },
        "certifications": {
            "en": [
                r"^(?:certifications?|credentials?|licenses?)",
                r"^(?:professional\s+certifications?|training\s+certifications?)",
            ],
            "vi": [
                r"^(?:chứng chỉ|chứng chỉ chuyên môn|bằng cấp chứng chỉ)",
            ],
        },
        "languages": {
            "en": [
                r"^(?:languages?|language\s+proficiency|multilingual)",
            ],
            "vi": [
                r"^(?:ngôn ngữ|khả năng ngôn ngữ)",
            ],
        },
        "awards": {
            "en": [
                r"^(?:awards?|recognitions?|honors?)",
            ],
            "vi": [
                r"^(?:giải thưởng|danh dự)",
            ],
        },
        "interests": {
            "en": [
                r"^(?:interests?|hobbies?|activities?)",
            ],
            "vi": [
                r"^(?:sở thích|hoạt động|sở thích cá nhân)",
            ],
        },
    }

    def __init__(self):
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile all regex patterns."""
        compiled = {}
        for section_type, langs in self.SECTION_PATTERNS.items():
            compiled[section_type] = []
            for lang, patterns in langs.items():
                for pattern in patterns:
                    try:
                        compiled[section_type].append(re.compile(pattern, re.IGNORECASE | re.MULTILINE))
                    except re.error as e:
                        import logging
                        logging.warning(f"Invalid regex pattern for {section_type}: {e}")
        return compiled

    def extract(self, markdown_dump: str) -> Dict[str, ExtractedSection]:
        """
        Extract sections from markdown dump using regex patterns with lightweight header pre-filtering.

        Args:
            markdown_dump: Intermediate markdown from Step 4

        Returns:
            Dict[section_type] → ExtractedSection
        """
        lines = markdown_dump.split("\n")
        sections: Dict[str, ExtractedSection] = {}
        current_section = None
        current_content = []
        confidence_accumulator = {}

        # Use lightweight header detection as pre-filter for performance
        potential_headers = HeaderDetector.detect_headers(lines)
        potential_header_lines = set(potential_headers)

        for line_num, line in enumerate(lines):
            line_stripped = line.strip()

            # Quick pre-filter: only check regex patterns if line looks like a header
            matched_section = None
            if line_num in potential_header_lines:
                matched_section = self._match_section_header(line_stripped)

            if matched_section:
                # Save previous section
                if current_section:
                    content = "\n".join(current_content).strip()
                    if content:
                        sections[current_section] = ExtractedSection(
                            section_type=current_section,
                            content=content,
                            confidence=confidence_accumulator.get(current_section, 0.75),
                            header_line=line_num - len(current_content) - 1,
                            header_text=current_section
                        )

                # Start new section
                current_section = matched_section
                current_content = []
                confidence_accumulator[current_section] = 0.80  # Higher confidence for matched headers
            elif current_section and line_stripped and not line_stripped.startswith("="):
                # Add content to current section (skip separator lines)
                if not line_stripped.startswith("PAGE:") and not line_stripped.startswith("TYPE:"):
                    current_content.append(line)

        # Don't forget last section
        if current_section:
            content = "\n".join(current_content).strip()
            if content:
                sections[current_section] = ExtractedSection(
                    section_type=current_section,
                    content=content,
                    confidence=confidence_accumulator.get(current_section, 0.75),
                    header_line=len(lines) - len(current_content) - 1,
                    header_text=current_section
                )

        import logging
        logging.info(f"Regex extraction found {len(sections)} sections")
        return sections

    def _match_section_header(self, text: str) -> Optional[str]:
        """
        Match text against section header patterns.
        Returns section type if match found, otherwise None.
        """
        for section_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return section_type
        return None


class SectionDetector:
    """
    Unified section detection interface combining header detection and regex extraction.
    Provides both simple header detection and comprehensive section extraction.
    """

    def __init__(self):
        self.header_detector = HeaderDetector()
        self.regex_extractor = RegexSectionExtractor()

    def detect_headers(self, lines: List[str]) -> List[int]:
        """Detect header lines using simple heuristics."""
        return self.header_detector.detect_headers(lines)

    def extract_sections(self, markdown_dump: str) -> Dict[str, ExtractedSection]:
        """Extract sections using regex patterns."""
        return self.regex_extractor.extract(markdown_dump)

    def group_content_by_headers(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Group content by detected headers."""
        return self.header_detector.group_content_by_headers(lines)

    def extract_with_confidence(self, markdown_dump: str) -> Tuple[Dict[str, ExtractedSection], float]:
        """
        Extract sections with overall confidence scoring.
        Returns sections and average confidence score.
        """
        sections = self.extract_sections(markdown_dump)
        if not sections:
            return {}, 0.0
        
        avg_confidence = sum(section.confidence for section in sections.values()) / len(sections)
        return sections, avg_confidence
    