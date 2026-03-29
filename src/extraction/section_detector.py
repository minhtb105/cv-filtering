"""
Section Detection Module

Hybrid approach: Regex + Fuzzy Matching + Heuristics
Supports English and Vietnamese multilingual CVs.
"""

import re
from enum import Enum
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

try:
    from rapidfuzz import fuzz
except ImportError:
    # Fallback if rapidfuzz not available
    fuzz = None


class SectionType(Enum):
    """CV section types."""
    PERSONAL_INFO = "personal_info"
    SUMMARY = "summary"
    WORK_EXPERIENCE = "work_experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    LANGUAGES = "languages"
    AWARDS = "awards"
    INTERESTS = "interests"
    UNKNOWN = "unknown"


@dataclass
class Section:
    """Detected section with metadata."""
    line_number: int
    type: SectionType
    raw_text: str
    confidence: float  # 0.0 to 1.0


class SectionDetector:
    """Detects CV sections using hybrid matching strategy."""

    # Multilingual keywords for section detection
    SECTION_KEYWORDS = {
        SectionType.WORK_EXPERIENCE: {
            "en": [
                "work experience",
                "experience",
                "employment",
                "professional experience",
                "career",
                "work history",
                "positions held",
                "job history",
            ],
            "vi": [
                "kinh nghiệm làm việc",
                "kinh nghiệm",
                "quá trình công tác",
                "công việc",
                "lịch sử công việc",
                "vị trí công việc",
            ],
        },
        SectionType.EDUCATION: {
            "en": [
                "education",
                "academic background",
                "academic",
                "qualification",
                "degree",
                "school",
                "university",
                "college",
                "training",
            ],
            "vi": [
                "học vấn",
                "trình độ học vấn",
                "nền tảng học vấn",
                "đào tạo",
                "bằng cấp",
                "trường",
                "đại học",
                "học tập",
            ],
        },
        SectionType.SKILLS: {
            "en": [
                "skills",
                "technical skills",
                "competencies",
                "expertise",
                "proficiencies",
                "capabilities",
                "technical expertise",
                "core competencies",
            ],
            "vi": [
                "kỹ năng",
                "kỹ năng chuyên môn",
                "kỹ năng kỹ thuật",
                "năng lực",
                "chuyên môn",
                "khả năng",
            ],
        },
        SectionType.PROJECTS: {
            "en": [
                "projects",
                "personal projects",
                "project experience",
                "portfolio",
                "notable projects",
            ],
            "vi": [
                "dự án",
                "các dự án",
                "dự án cá nhân",
                "dự án kinh nghiệm",
                "danh sách dự án",
            ],
        },
        SectionType.SUMMARY: {
            "en": [
                "summary",
                "professional summary",
                "objective",
                "profile",
                "about",
                "introduction",
                "career summary",
                "professional profile",
            ],
            "vi": [
                "tóm tắt",
                "tóm tắt chuyên môn",
                "mục tiêu",
                "mục tiêu nghề nghiệp",
                "giới thiệu",
                "hồ sơ",
            ],
        },
        SectionType.CERTIFICATIONS: {
            "en": [
                "certifications",
                "certificates",
                "licenses",
                "professional certifications",
                "credentials",
            ],
            "vi": [
                "chứng chỉ",
                "chứng chỉ chuyên môn",
                "giấy chứng nhận",
                "bằng cấp",
                "tài chính",
            ],
        },
        SectionType.LANGUAGES: {
            "en": [
                "languages",
                "language skills",
                "language proficiency",
            ],
            "vi": [
                "ngôn ngữ",
                "kỹ năng ngôn ngữ",
                "trình độ ngôn ngữ",
            ],
        },
        SectionType.AWARDS: {
            "en": [
                "awards",
                "achievements",
                "honors",
                "recognition",
                "prizes",
            ],
            "vi": [
                "giải thưởng",
                "thành tích",
                "danh hiệu",
                "công nhận",
            ],
        },
        SectionType.INTERESTS: {
            "en": [
                "interests",
                "hobbies",
                "personal interests",
                "hobbies and interests",
            ],
            "vi": [
                "sở thích",
                "sở thích cá nhân",
                "hoạt động",
            ],
        },
    }

    @staticmethod
    def normalize_for_matching(text: str) -> str:
        """Normalize text for section matching."""
        from .text_cleaner import TextCleaner

        # Remove accents for better matching
        text = TextCleaner.remove_accents(text)
        # Lowercase
        text = text.lower()
        # Remove extra whitespace and punctuation
        text = re.sub(r'[:\-_\s]+', ' ', text).strip()
        return text

    @staticmethod
    def is_section_header_heuristic(line: str) -> Tuple[bool, float]:
        """
        Heuristic checks for section header candidates.

        Returns:
            (is_header: bool, confidence: float)
        """
        line_stripped = line.strip()

        # Empty or too long
        if not line_stripped or len(line_stripped) > 100:
            return False, 0.0

        # Word count heuristic (sections are typically short)
        word_count = len(line_stripped.split())
        if word_count > 6:
            return False, 0.0

        confidence = 0.0

        # ALL CAPS → strong signal
        if line_stripped.isupper() and len(line_stripped) > 3:
            confidence += 0.4

        # Ends with colon
        if line_stripped.endswith(':'):
            confidence += 0.2

        # Standalone line (surrounded by content)
        if len(line_stripped) < 50 and word_count <= 4:
            confidence += 0.2

        # Check for common section starters
        lower_line = line_stripped.lower()
        if any(
            starter in lower_line
            for starter in ['experience', 'education', 'skills', 'projects', 'summary']
        ):
            confidence += 0.2

        return confidence > 0.0, confidence

    @staticmethod
    def fuzzy_match_keywords(
        line: str, keywords: List[str], threshold: int = 80
    ) -> Tuple[float, str]:
        """
        Fuzzy match line against keyword list.

        Returns:
            (max_score: float, best_match: str)
        """
        if not fuzz:
            # Fallback: exact substring matching
            normalized_line = SectionDetector.normalize_for_matching(line)
            for kw in keywords:
                normalized_kw = SectionDetector.normalize_for_matching(kw)
                if normalized_kw in normalized_line:
                    return 100.0, kw
            return 0.0, ""

        normalized_line = SectionDetector.normalize_for_matching(line)

        best_score = 0.0
        best_match = ""

        for keyword in keywords:
            # Try partial ratio for better matching
            score = fuzz.token_set_ratio(normalized_line, keyword)
            if score > best_score:
                best_score = score
                best_match = keyword

        return float(best_score), best_match

    @staticmethod
    def detect_section_type(line: str) -> Tuple[Optional[SectionType], float]:
        """
        Detect section type using hybrid strategy.

        Returns:
            (section_type: SectionType or None, confidence: float)
        """
        # Step 1: Heuristic check
        is_header, heuristic_confidence = SectionDetector.is_section_header_heuristic(
            line
        )
        if not is_header:
            return None, 0.0

        best_type = None
        best_score = 0.0
        best_confidence = 0.0

        # Step 2: Fuzzy match against all section types
        for section_type, keywords_dict in SectionDetector.SECTION_KEYWORDS.items():
            all_keywords = keywords_dict.get("en", []) + keywords_dict.get("vi", [])

            fuzzy_score, _ = SectionDetector.fuzzy_match_keywords(line, all_keywords)

            if fuzzy_score >= 80:  # Threshold for fuzzy match
                # Combine heuristic + fuzzy scores
                combined_score = (heuristic_confidence * 0.3) + (fuzzy_score / 100.0 * 0.7)

                if combined_score > best_score:
                    best_score = combined_score
                    best_type = section_type
                    best_confidence = combined_score

        return best_type, best_confidence

    @staticmethod
    def detect_sections(lines: List[str]) -> List[Section]:
        """
        Detect all sections in a CV line list.

        Args:
            lines: List of text lines from CV

        Returns:
            List of detected sections with metadata
        """
        sections = []

        for line_num, line in enumerate(lines):
            section_type, confidence = SectionDetector.detect_section_type(line)

            if section_type is not None:
                section = Section(
                    line_number=line_num,
                    type=section_type,
                    raw_text=line.strip(),
                    confidence=confidence,
                )
                sections.append(section)

        return sections

    @staticmethod
    def extract_section_content(
        lines: List[str], section_start: int, section_end: Optional[int] = None
    ) -> List[str]:
        """
        Extract content between section boundaries.

        Args:
            lines: All CV lines
            section_start: Starting line (inclusive, after header)
            section_end: Ending line (exclusive) or None for all remaining

        Returns:
            Section content lines
        """
        if section_end is None:
            section_end = len(lines)

        return lines[section_start + 1 : section_end]

    @staticmethod
    def group_sections_with_content(
        lines: List[str],
    ) -> Dict[str, Dict]:
        """
        Group detected sections with their content.

        Returns:
            Dict[section_name] = {
                'header_line': int,
                'type': SectionType,
                'confidence': float,
                'content': List[str],
            }
        """
        sections = SectionDetector.detect_sections(lines)

        if not sections:
            return {}

        grouped = {}

        for i, section in enumerate(sections):
            # Determine content boundaries
            content_start = section.line_number
            content_end = (
                sections[i + 1].line_number
                if i + 1 < len(sections)
                else len(lines)
            )

            # Skip the header line itself
            section_content = lines[content_start + 1 : content_end]

            # Remove empty lines at start/end
            while section_content and not section_content[0].strip():
                section_content.pop(0)
            while section_content and not section_content[-1].strip():
                section_content.pop()

            grouped[section.type.value] = {
                "header_line": section.line_number,
                "type": section.type,
                "confidence": section.confidence,
                "raw_header": section.raw_text,
                "content": section_content,
            }

        return grouped
