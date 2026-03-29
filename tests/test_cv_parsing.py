"""
CV Parsing Pipeline Tests

Comprehensive test suite for all parsing components.
"""

import tempfile
import os

from src.extraction import (
    TextCleaner,
    SectionDetector,
    SectionType,
    MarkdownGenerator,
    CVMarkdownConfig,
)


class TestTextCleaner:
    """Tests for text cleaning and validation."""

    def test_is_bad_text_empty(self):
        """Test detection of empty text."""
        is_bad, reason = TextCleaner.is_bad_text("")
        assert is_bad is True
        assert "Empty" in reason

    def test_is_bad_text_too_short(self):
        """Test detection of too-short text."""
        is_bad, reason = TextCleaner.is_bad_text("Hi")
        assert is_bad is True
        assert "short" in reason.lower()

    def test_is_bad_text_excessive_newlines(self):
        """Test detection of excessive newlines."""
        bad_text = "Line 1\n\n\n\n\nLine 2"
        is_bad, reason = TextCleaner.is_bad_text(bad_text)
        assert is_bad is True

    def test_is_bad_text_cid_artifacts(self):
        """Test detection of CID artifacts."""
        bad_text = "Some text (cid:1) more text (cid:2) and more (cid:3) (cid:4) (cid:5) (cid:6)"
        is_bad, reason = TextCleaner.is_bad_text(bad_text)
        assert is_bad is True
        assert "artifact" in reason.lower()

    def test_is_bad_text_control_characters(self):
        """Test detection of control characters."""
        bad_text = "Normal text\x01\x02 with control chars"
        is_bad, reason = TextCleaner.is_bad_text(bad_text)
        assert is_bad is True

    def test_is_bad_text_valid(self):
        """Test valid text passes checks."""
        good_text = "This is a valid CV with actual content. It contains multiple words and meaningful information."
        is_bad, reason = TextCleaner.is_bad_text(good_text)
        assert is_bad is False

    def test_remove_null_bytes(self):
        """Test NULL byte removal."""
        text = "Hello\x00World\x00Test"
        cleaned = TextCleaner.remove_null_bytes(text)
        assert "\x00" not in cleaned
        assert "HelloWorldTest" in cleaned

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        text = "Line 1\r\nLine 2\n\n\nLine 3"
        normalized = TextCleaner.normalize_whitespace(text)
        assert "\r\n" not in normalized
        assert "\n\n\n" not in normalized

    def test_remove_artifacts(self):
        """Test artifact removal."""
        text = "Text with (cid:1) and (cid:2) artifacts"
        cleaned = TextCleaner.remove_artifacts(text)
        assert "(cid:" not in cleaned

    def test_remove_accents(self):
        """Test accent removal."""
        text = "Café naïve résumé"
        no_accents = TextCleaner.remove_accents(text)
        assert "Cafe" in no_accents
        assert "naive" in no_accents
        assert "resume" in no_accents

    def test_normalize_unicode(self):
        """Test unicode normalization."""
        text = "Café"  # precomposed form
        normalized = TextCleaner.normalize_unicode(text)
        assert isinstance(normalized, str)

    def test_clean_text(self):
        """Test complete text cleaning."""
        raw = "Text with (cid:1)\x00extra  spaces\nand\n\nnewlines"
        cleaned = TextCleaner.clean_text(raw, lowercase=False)
        assert "(cid:" not in cleaned
        assert "\x00" not in cleaned
        assert "\n\n\n" not in cleaned

    def test_extract_lines(self):
        """Test line extraction."""
        text = "Line 1\n\nLine 2\n   \nLine 3"
        lines = TextCleaner.extract_lines(text)
        assert len(lines) == 3
        assert "Line 1" in lines
        assert "" not in lines

    def test_map_symbols_to_text(self):
        """Test symbol mapping."""
        text = "Contact: 📞 123-456 ✉️ test@example.com 📍 City"
        mapped = TextCleaner.map_symbols_to_text(text)
        assert "Phone:" in mapped
        assert "Email:" in mapped
        assert "Location:" in mapped

    def test_validate_and_clean(self):
        """Test complete validation and cleaning pipeline."""
        raw = "This is a valid CV text with proper content and structure"
        is_valid, reason, cleaned = TextCleaner.validate_and_clean(raw)
        assert is_valid is True
        assert cleaned == raw.lower()


class TestSectionDetector:
    """Tests for section detection."""

    def test_normalize_for_matching(self):
        """Test text normalization for matching."""
        text = "  Work Experience:  "
        normalized = SectionDetector.normalize_for_matching(text)
        assert normalized == "work experience"

    def test_is_section_header_heuristic_all_caps(self):
        """Test heuristic detection of ALL CAPS headers."""
        is_header, confidence = SectionDetector.is_section_header_heuristic(
            "WORK EXPERIENCE"
        )
        assert is_header is True
        assert confidence > 0.3

    def test_is_section_header_heuristic_with_colon(self):
        """Test heuristic detection of headers with colon."""
        is_header, confidence = SectionDetector.is_section_header_heuristic(
            "Work Experience:"
        )
        assert is_header is True

    def test_is_section_header_heuristic_short_line(self):
        """Test heuristic detection of short lines."""
        is_header, confidence = SectionDetector.is_section_header_heuristic(
            "Education"
        )
        assert is_header is True

    def test_is_section_header_heuristic_too_long(self):
        """Test rejection of too-long lines."""
        long_text = "This is a very long line " * 5
        is_header, confidence = SectionDetector.is_section_header_heuristic(long_text)
        assert is_header is False

    def test_detect_section_type_work_experience_en(self):
        """Test detection of work experience section (English)."""
        section_type, confidence = SectionDetector.detect_section_type(
            "WORK EXPERIENCE"
        )
        assert section_type == SectionType.WORK_EXPERIENCE
        assert confidence > 0.0

    def test_detect_section_type_work_experience_vi(self):
        """Test detection of work experience section (Vietnamese)."""
        section_type, confidence = SectionDetector.detect_section_type(
            "KINH NGHIỆM LÀM VIỆC"
        )
        assert section_type == SectionType.WORK_EXPERIENCE
        assert confidence > 0.0

    def test_detect_section_type_education(self):
        """Test detection of education section."""
        section_type, confidence = SectionDetector.detect_section_type("Education:")
        assert section_type == SectionType.EDUCATION

    def test_detect_section_type_skills(self):
        """Test detection of skills section."""
        section_type, confidence = SectionDetector.detect_section_type("SKILLS")
        assert section_type == SectionType.SKILLS

    def test_detect_sections(self):
        """Test section detection in lines."""
        lines = [
            "John Doe",
            "WORK EXPERIENCE",
            "Project X",
            "EDUCATION",
            "University",
        ]
        sections = SectionDetector.detect_sections(lines)
        assert len(sections) > 0
        assert any(s.type == SectionType.WORK_EXPERIENCE for s in sections)
        assert any(s.type == SectionType.EDUCATION for s in sections)

    def test_extract_section_content(self):
        """Test section content extraction."""
        lines = [
            "WORK EXPERIENCE",
            "Project 1",
            "Project 2",
            "EDUCATION",
            "University",
        ]
        content = SectionDetector.extract_section_content(lines, 0, 3)
        assert "Project 1" in content
        assert "Project 2" in content

    def test_group_sections_with_content(self):
        """Test grouping sections with their content."""
        lines = [
            "John Doe",
            "WORK EXPERIENCE",
            "- Worked at Company A",
            "EDUCATION",
            "- Bachelor from University",
        ]
        grouped = SectionDetector.group_sections_with_content(lines)
        assert SectionType.WORK_EXPERIENCE.value in grouped
        assert SectionType.EDUCATION.value in grouped


class TestMarkdownGenerator:
    """Tests for markdown generation."""

    def test_format_section_header(self):
        """Test section header formatting."""
        header = MarkdownGenerator.format_section_header("Work Experience")
        assert header == "## Work Experience"

    def test_format_bullet_list(self):
        """Test bullet list formatting."""
        items = ["Item 1", "Item 2", "Item 3"]
        formatted = MarkdownGenerator.format_bullet_list(items)
        assert "- Item 1" in formatted
        assert "- Item 2" in formatted
        assert "- Item 3" in formatted

    def test_format_key_value_pairs(self):
        """Test key-value pair formatting."""
        pairs = {"Name": "John", "Email": "john@example.com"}
        formatted = MarkdownGenerator.format_key_value_pairs(pairs)
        assert "Name: John" in formatted
        assert "Email: john@example.com" in formatted

    def test_format_work_experience_empty(self):
        """Test work experience formatting with empty list."""
        formatted = MarkdownGenerator.format_work_experience([])
        assert "*None provided*" in formatted

    def test_format_work_experience_with_data(self):
        """Test work experience formatting with data."""
        experiences = [
            {
                "company": "Tech Corp",
                "position": "Senior Engineer",
                "duration": "2020-2023",
                "description": ["Led team", "Shipped features"],
            }
        ]
        formatted = MarkdownGenerator.format_work_experience(experiences)
        assert "Tech Corp" in formatted
        assert "Senior Engineer" in formatted
        assert "2020-2023" in formatted

    def test_format_education_with_data(self):
        """Test education formatting with data."""
        educations = [
            {
                "school": "Tech University",
                "degree": "B.S. Computer Science",
                "field": "Computer Science",
                "gpa": "3.8",
                "graduation_date": "2020",
            }
        ]
        formatted = MarkdownGenerator.format_education(educations)
        assert "Tech University" in formatted
        assert "B.S. Computer Science" in formatted
        assert "3.8" in formatted

    def test_format_skills(self):
        """Test skills formatting."""
        skills = {
            "Technical": ["Python", "React", "PostgreSQL"],
            "Soft Skills": ["Leadership", "Communication"],
        }
        formatted = MarkdownGenerator.format_skills(skills)
        assert "Technical" in formatted
        assert "Python" in formatted
        assert "Leadership" in formatted

    def test_format_projects(self):
        """Test projects formatting."""
        projects = [
            {
                "name": "CV Parser",
                "role": "Lead Developer",
                "tech_stack": ["Python", "FastAPI"],
                "description": ["Robust PDF parsing", "Multilingual support"],
            }
        ]
        formatted = MarkdownGenerator.format_projects(projects)
        assert "CV Parser" in formatted
        assert "Lead Developer" in formatted

    def test_normalize_markdown(self):
        """Test markdown normalization."""
        markdown = "# Header\n\n\n\nSome text\n\n\nMore text"
        normalized = MarkdownGenerator.normalize_markdown(markdown)
        assert "\n\n\n" not in normalized

    def test_generate_markdown(self):
        """Test complete markdown generation."""
        personal_info = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890",
            "location": "New York",
        }

        sections = {
            "work_experience": [],
            "education": [],
            "skills": {},
            "projects": [],
            "certifications": {},
        }

        markdown = MarkdownGenerator.generate_markdown(personal_info, sections, "test.pdf")
        assert "# CV - John Doe" in markdown
        assert "john@example.com" in markdown
        assert "123-456-7890" in markdown
        assert "New York" in markdown

    def test_generate_markdown_with_config(self):
        """Test markdown generation with custom config."""
        personal_info = {"name": "Test"}
        sections = {
            "work_experience": [],
            "education": [],
            "skills": {},
            "projects": [],
            "certifications": {},
        }
        config = CVMarkdownConfig(include_timestamps=False)

        markdown = MarkdownGenerator.generate_markdown(
            personal_info, sections, config=config
        )
        # Should still contain CV title
        assert "# CV - Test" in markdown

    def test_save_markdown(self):
        """Test markdown file saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown = "# Test CV\nContent here"
            filepath = os.path.join(tmpdir, "test.md")

            MarkdownGenerator.save_markdown(markdown, filepath)

            assert os.path.exists(filepath)
            with open(filepath, "r") as f:
                content = f.read()
            assert content == markdown


class TestIntegration:
    """Integration tests for complete pipeline."""

    def test_text_cleaning_integration(self):
        """Test text cleaning in realistic scenario."""
        raw_cv_text = """John Doe
john@example.com | 123-456-7890

WORK EXPERIENCE
Senior Engineer at Tech Corp
2020 - 2023
- Led team of engineers
- Shipped features

EDUCATION
B.S. Computer Science
Tech University, 2020"""

        is_valid, reason, cleaned = TextCleaner.validate_and_clean(raw_cv_text)
        assert cleaned  # Should produce cleaned text
        # After cleaning, should not have artifacts
        assert "(cid:" not in cleaned
        assert "\n\n\n" not in cleaned

    def test_section_detection_integration(self):
        """Test section detection on realistic CV."""
        lines = [
            "John Doe",
            "Email: john@example.com",
            "WORK EXPERIENCE",
            "Senior Engineer at Tech Corp",
            "Led team of engineers",
            "EDUCATION",
            "B.S. Computer Science from Tech University",
            "SKILLS",
            "Python, ReactJS, PostgreSQL",
        ]

        grouped = SectionDetector.group_sections_with_content(lines)
        assert len(grouped) >= 2  # At least work experience and education
