"""
Markdown Normalizer - Section detection and text cleaning
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExtractionMetadata:
    """Metadata about the extraction"""
    language_detected: str = "unknown"
    sections_found: List[str] = field(default_factory=list)
    confidence: float = 0.0
    cleaned_bytes: int = 0


class HybridSectionExtractor:
    """Extract and normalize sections from CV text"""

    SECTION_KEYWORDS = {
        "en": {
            "summary": ["summary", "profile", "about", "objective"],
            "experience": ["experience", "work history", "employment", "professional experience"],
            "education": ["education", "academic", "qualification", "degree"],
            "skills": ["skills", "technical skills", "competencies", "technologies"],
            "projects": ["projects", "project", "portfolio"],
            "certifications": ["certifications", "certificates", "licenses"],
            "languages": ["languages", "language proficiency"],
            "contact": ["contact", "info", "personal information"],
        },
        "vi": {
            "summary": ["tóm tắt", "hồ sơ", "giới thiệu", "mục tiêu"],
            "experience": ["kinh nghiệm", "lịch sử công việc", "việc làm", "nghề nghiệp"],
            "education": ["học vấn", "học tập", "trình độ", "bằng cấp"],
            "skills": ["kỹ năng", "kỹ thuật", "năng lực", "công nghệ"],
            "projects": ["dự án", "d án", "portfolio"],
            "certifications": ["chứng chỉ", "chứng nhận", "bằng cấp"],
            "languages": ["ngoại ngữ", "ngôn ngữ"],
            "contact": ["liên hệ", "thông tin", "cá nhân"],
        }
    }

    TECH_KEYWORDS = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
        "React", "Angular", "Vue", "NodeJS", "Node.js", "Django", "Flask",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "Git",
        "REST", "API", "GraphQL", "Microservices", "SQL", "NoSQL",
        "Machine Learning", "AI", "Deep Learning", "NLP", "Computer Vision",
        "Linux", "Windows", "Agile", "Scrum", "CI/CD",
    ]

    KNOWN_TOKENS = {
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "NodeJS", "Node.js", "ReactJS", "VueJS", "AngularJS",
        "AWS", "Azure", "GCP", "K8s",
        "RESTful", "GraphQL", "CI/CD", "DevOps",
        "MachineLearning", "DeepLearning", "NLP",
        "JUnit", "Selenium", "Cypress",
    }

    def __init__(self):
        self.language = "en"

    def normalize(self, text: str, source_lang: str = "auto") -> Tuple[str, ExtractionMetadata]:
        """Normalize extracted text to markdown"""
        text = self._clean_text(text)
        language = self._detect_language(text) if source_lang == "auto" else source_lang
        self.language = language

        sections = self._detect_sections(text, language)
        markdown = self._build_markdown(text, sections, language)

        metadata = ExtractionMetadata(
            language_detected=language,
            sections_found=list(sections.keys()),
            confidence=self._calculate_confidence(sections),
        )

        return markdown, metadata

    def _clean_text(self, text: str) -> str:
        """Clean text with glyph errors"""
        text = text.replace("\x00", "")
        text = text.replace("\ufffd", "")
        text = re.sub(r"[\x01-\x08\x0b-\x0c\x0e-\x1f]", "", text)

        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        lines = text.split("\n")
        cleaned = [line.strip() for line in lines if line.strip()]
        text = "\n".join(cleaned)

        return text

    def _restore_spaces(self, text: str) -> str:
        """Restore spaces in camelCase but preserve known tokens"""
        for token in sorted(self.KNOWN_TOKENS, key=len, reverse=True):
            if token in text:
                text = text.replace(token, token.replace(" ", ""))

        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        text = re.sub(r"([a-zA-Z])([A-Z][a-z])", r"\1 \2", text)

        for token in self.KNOWN_TOKENS:
            pattern = re.compile(re.escape(token.replace(" ", "")), re.IGNORECASE)
            text = pattern.sub(token, text)

        return text

    def _detect_language(self, text: str) -> str:
        """Detect if text is Vietnamese or English"""
        vietnamese_chars = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"

        vi_count = sum(1 for c in text.lower() if c in vietnamese_chars)
        vi_ratio = vi_count / max(len(text), 1)

        return "vi" if vi_ratio > 0.02 else "en"

    def _detect_sections(self, text: str, language: str) -> Dict[str, Tuple[int, int]]:
        """Detect sections in text"""
        keywords = self.SECTION_KEYWORDS.get(language, self.SECTION_KEYWORDS["en"])
        lines = text.split("\n")
        sections = {}

        current_section = "header"
        sections[current_section] = (0, 0)

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()

            for section_name, section_keywords in keywords.items():
                if any(kw in line_lower for kw in section_keywords):
                    if line_lower.startswith(section_name) or len(line) < 50:
                        sections[section_name] = (i, i)
                        current_section = section_name
                        break

        for section_name in sections:
            start, _ = sections[section_name]
            sections[section_name] = (start, len(lines) - 1)

        return sections

    def _build_markdown(self, text: str, sections: Dict[str, Tuple[int, int]], language: str) -> str:
        """Build markdown with section headers"""
        lines = text.split("\n")
        markdown_lines = []

        markdown_lines.append(f"# {language.upper()} - CV Extraction")
        markdown_lines.append("")
        markdown_lines.append(f"**Extracted:** {datetime.utcnow().isoformat()}")
        markdown_lines.append("")

        section_order = ["summary", "experience", "projects", "skills", "education", "certifications", "languages", "contact"]
        detected_sections = {k: v for k, v in sections.items() if k in section_order}

        for section in section_order:
            if section in detected_sections:
                markdown_lines.append(f"## {section.upper()}")
                markdown_lines.append("")

                start_idx, end_idx = detected_sections[section]
                section_lines = lines[start_idx+1:end_idx] if start_idx != end_idx else lines[start_idx+1:start_idx+5]

                for line in section_lines[:10]:
                    if line.strip() and not any(kw in line.lower() for kw in self.SECTION_KEYWORDS[language].get(section, [])):
                        markdown_lines.append(line)

                markdown_lines.append("")

        if "header" in sections:
            start_idx, _ = sections["header"]
            header_lines = [l for l in lines[:min(start_idx, 5)] if l.strip()]
            if header_lines:
                markdown_lines.insert(3, "## HEADER")
                markdown_lines.insert(4, "")
                for line in header_lines[:3]:
                    markdown_lines.insert(5, line)
                    markdown_lines.insert(6, "")

        return "\n".join(markdown_lines)

    def _calculate_confidence(self, sections: Dict[str, Tuple[int, int]]) -> float:
        """Calculate confidence based on sections found"""
        min_sections = 3
        found = len(sections)
        return min(found / min_sections, 1.0)


__all__ = ["HybridSectionExtractor", "ExtractionMetadata"]
