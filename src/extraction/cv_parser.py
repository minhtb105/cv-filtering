"""
CV Parser Pipeline

Main orchestrator for robust CV parsing with:
- Text validation & cleaning
- Section detection (multilingual, fuzzy)
- Structured markdown generation
- Optional LLM extraction
"""

import logging
import os
from typing import Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import json

from src.extraction.pdf_extractor import PDFExtractor
from src.extraction.text_cleaner import TextCleaner
from src.extraction.section_detector import SectionDetector, SectionType
from src.extraction.markdown_generator import MarkdownGenerator, CVMarkdownConfig
from src.extraction.llm_extractor import LLMExtractor, LLMExtractionConfig

logger = logging.getLogger(__name__)


@dataclass
class CVParsingConfig:
    """Configuration for CV parsing pipeline."""
    extract_with_ocr: bool = False
    use_llm_extraction: bool = False
    remove_accents_for_matching: bool = True
    llm_config: Optional[LLMExtractionConfig] = None
    markdown_config: Optional[CVMarkdownConfig] = None
    output_markdown_dir: Optional[str] = None
    output_json_dir: Optional[str] = None


class CVParser:
    """Robust CV parsing pipeline with multilingual support."""

    def __init__(self, config: Optional[CVParsingConfig] = None):
        self.config = config or CVParsingConfig()
        self.text_cleaner = TextCleaner()
        self.section_detector = SectionDetector()

        if self.config.use_llm_extraction:
            llm_config = self.config.llm_config or LLMExtractionConfig()
            self.llm_extractor = LLMExtractor(llm_config)
        else:
            self.llm_extractor = None

        # Create output directories if specified
        if self.config.output_markdown_dir:
            Path(self.config.output_markdown_dir).mkdir(parents=True, exist_ok=True)
        if self.config.output_json_dir:
            Path(self.config.output_json_dir).mkdir(parents=True, exist_ok=True)

    def parse_cv(self, pdf_path: str) -> Dict[str, Any]:
        """
        Complete CV parsing pipeline.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with:
            {
                'success': bool,
                'filename': str,
                'extraction_method': str,
                'text_quality': (is_valid, reason),
                'cleaned_text': str,
                'sections': Dict[section_type] → content,
                'markdown': str,
                'json_extracted': Optional[Dict],
                'errors': List[str],
                'metadata': Dict
            }
        """
        result = {
            "success": False,
            "filename": os.path.basename(pdf_path),
            "extraction_method": None,
            "text_quality": None,
            "cleaned_text": "",
            "sections": {},
            "markdown": "",
            "json_extracted": None,
            "errors": [],
            "metadata": {
                "pdf_path": pdf_path,
                "file_size": os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0,
            },
        }

        try:
            # Step 1: Extract text from PDF
            logger.info(f"Parsing CV: {pdf_path}")

            if not os.path.exists(pdf_path):
                result["errors"].append(f"File not found: {pdf_path}")
                return result

            success, raw_text, method = PDFExtractor.extract_text_with_fallback(
                pdf_path
            )
            result["extraction_method"] = method

            if not success:
                result["errors"].append("Failed to extract text from PDF")
                return result

            result["metadata"]["raw_text_length"] = len(raw_text)

            # Step 2: Validate & clean text
            is_valid, reason, cleaned_text = self.text_cleaner.validate_and_clean(
                raw_text
            )
            result["text_quality"] = (is_valid, reason)
            result["cleaned_text"] = cleaned_text

            if not is_valid:
                logger.warning(f"Text quality issue: {reason}")
                if method == "failed":  # If primary extraction failed
                    result["errors"].append(f"Text quality issue: {reason}")
                    return result

            # Step 3: Detect sections
            lines = self.text_cleaner.extract_lines(cleaned_text)
            result["metadata"]["line_count"] = len(lines)

            sections_grouped = self.section_detector.group_sections_with_content(
                lines
            )
            result["sections"] = {
                section_name: section_info["content"]
                for section_name, section_info in sections_grouped.items()
            }

            logger.info(f"Detected {len(sections_grouped)} sections")

            # Step 4: Extract personal info (heuristic)
            personal_info = self._extract_personal_info(lines[:50])  # Check first 50 lines
            result["metadata"]["personal_info"] = personal_info

            # Step 5: Generate markdown
            personal_info_full = {
                "name": personal_info.get("name", "Unknown"),
                "email": personal_info.get("email", ""),
                "phone": personal_info.get("phone", ""),
                "location": personal_info.get("location", ""),
                "summary": self._extract_summary_from_sections(sections_grouped),
            }

            sections_for_markdown = self._structure_sections_for_markdown(
                sections_grouped
            )

            markdown_config = (
                self.config.markdown_config or CVMarkdownConfig()
            )
            markdown = MarkdownGenerator.generate_markdown(
                personal_info_full,
                sections_for_markdown,
                source_file=os.path.basename(pdf_path),
                config=markdown_config,
            )
            markdown = MarkdownGenerator.normalize_markdown(markdown)
            result["markdown"] = markdown

            # Save markdown if output dir specified
            if self.config.output_markdown_dir:
                markdown_path = os.path.join(
                    self.config.output_markdown_dir,
                    f"{Path(pdf_path).stem}.md"
                )
                MarkdownGenerator.save_markdown(markdown, markdown_path)
                result["metadata"]["markdown_saved"] = markdown_path
                logger.info(f"Markdown saved to: {markdown_path}")

            # Step 6: Optional LLM extraction
            if self.config.use_llm_extraction and self.llm_extractor:
                logger.info("Running LLM extraction...")
                json_data = self.llm_extractor.extract(markdown)
                if json_data:
                    result["json_extracted"] = json_data

                    # Save JSON if output dir specified
                    if self.config.output_json_dir:
                        json_path = os.path.join(
                            self.config.output_json_dir,
                            f"{Path(pdf_path).stem}.json"
                        )
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)
                        result["metadata"]["json_saved"] = json_path
                        logger.info(f"JSON saved to: {json_path}")

            result["success"] = True
            logger.info(f"Successfully parsed CV: {pdf_path}")

        except Exception as e:
            logger.error(f"Unexpected error during parsing: {e}", exc_info=True)
            result["errors"].append(f"Unexpected error: {str(e)}")

        return result

    def _extract_personal_info(self, lines: list) -> Dict[str, str]:
        """
        Extract personal info (name, email, phone, location) from first lines.

        Simple heuristic: look for patterns in first 50 lines.
        """
        import re

        personal_info = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
        }

        text = "\n".join(lines)

        # Email pattern
        email_match = re.search(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text
        )
        if email_match:
            personal_info["email"] = email_match.group()

        # Phone pattern (basic)
        phone_match = re.search(
            r'(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}',
            text,
        )
        if phone_match:
            personal_info["phone"] = phone_match.group().strip()

        # Name: typically first few non-empty lines
        for line in lines:
            if line.strip() and len(line.strip()) < 50:
                # Likely a name if short and early
                if personal_info["email"] in line or personal_info["phone"] in line:
                    continue  # Skip if it contains contact info
                if not personal_info["name"]:
                    personal_info["name"] = line.strip()
                    break

        return personal_info

    def _extract_summary_from_sections(self, sections_grouped: Dict) -> str:
        """Extract summary/objective from detected sections."""
        summary_section = sections_grouped.get(SectionType.SUMMARY.value, {})
        if summary_section and summary_section.get("content"):
            content = summary_section["content"]
            return " ".join(content[:3]) if content else ""
        return ""

    def _structure_sections_for_markdown(self, sections_grouped: Dict) -> Dict:
        """Structure grouped sections for markdown generation."""
        structured = {
            "work_experience": [],
            "education": [],
            "skills": {},
            "projects": [],
            "certifications": {},
        }

        # Work experience: parse lines into structured format
        if SectionType.WORK_EXPERIENCE.value in sections_grouped:
            exp_lines = sections_grouped[SectionType.WORK_EXPERIENCE.value]["content"]
            # Simple parsing: each entry might be multi-line
            # Group by company lines (heuristic: all caps or title case)
            exp_blocks = self._parse_experience_blocks(exp_lines)
            structured["work_experience"] = exp_blocks

        # Education
        if SectionType.EDUCATION.value in sections_grouped:
            edu_lines = sections_grouped[SectionType.EDUCATION.value]["content"]
            edu_blocks = self._parse_education_blocks(edu_lines)
            structured["education"] = edu_blocks

        # Skills
        if SectionType.SKILLS.value in sections_grouped:
            skill_lines = sections_grouped[SectionType.SKILLS.value]["content"]
            skill_dict = self._parse_skills(skill_lines)
            structured["skills"] = skill_dict

        # Projects
        if SectionType.PROJECTS.value in sections_grouped:
            proj_lines = sections_grouped[SectionType.PROJECTS.value]["content"]
            proj_blocks = self._parse_project_blocks(proj_lines)
            structured["projects"] = proj_blocks

        # Certifications, Languages, Awards, Interests
        cert_dict = {}
        for section_type in [
            SectionType.CERTIFICATIONS,
            SectionType.LANGUAGES,
            SectionType.AWARDS,
            SectionType.INTERESTS,
        ]:
            if section_type.value in sections_grouped:
                lines = sections_grouped[section_type.value]["content"]
                cert_dict[section_type.value] = [l.strip() for l in lines if l.strip()]

        structured["certifications"] = cert_dict

        return structured

    def _parse_experience_blocks(self, lines: list) -> list:
        """Parse work experience blocks from lines."""
        blocks = []
        current_block = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Simple heuristic: if line looks like company/position (common patterns)
            if any(
                keyword in line.lower()
                for keyword in ["company:", "position:", "role:", "at ", "-"]
            ):
                if current_block:
                    blocks.append(current_block)
                current_block = {"company": "", "position": "", "duration": "", "description": []}

                if "company:" in line.lower():
                    current_block["company"] = line.split(":", 1)[1].strip()
                elif "position:" in line.lower():
                    current_block["position"] = line.split(":", 1)[1].strip()
                elif "role:" in line.lower():
                    current_block["position"] = line.split(":", 1)[1].strip()
                elif " - " in line:
                    parts = line.split(" - ")
                    current_block["company"] = parts[0].strip()
                    current_block["position"] = parts[1].strip() if len(parts) > 1 else ""

            else:
                # It's description
                if current_block or line:
                    if not current_block:
                        current_block = {"company": "Unknown", "position": line, "duration": "", "description": []}
                    current_block["description"].append(line)

        if current_block:
            blocks.append(current_block)

        return blocks

    def _parse_education_blocks(self, lines: list) -> list:
        """Parse education blocks from lines."""
        blocks = []
        current_block = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if any(
                keyword in line.lower()
                for keyword in ["university:", "school:", "degree:", "major:", "gpa:"]
            ):
                if current_block:
                    blocks.append(current_block)
                current_block = {"school": "", "degree": "", "field": "", "gpa": "", "graduation_date": ""}

                if any(kw in line.lower() for kw in ["university:", "school:"]):
                    current_block["school"] = line.split(":", 1)[1].strip()
                elif "degree:" in line.lower():
                    current_block["degree"] = line.split(":", 1)[1].strip()
                elif "major:" in line.lower():
                    current_block["field"] = line.split(":", 1)[1].strip()
                elif "gpa:" in line.lower():
                    current_block["gpa"] = line.split(":", 1)[1].strip()

            else:
                if not current_block:
                    current_block = {"school": line, "degree": "", "field": "", "gpa": "", "graduation_date": ""}

        if current_block:
            blocks.append(current_block)

        return blocks

    def _parse_skills(self, lines: list) -> Dict[str, list]:
        """Parse skills into categories."""
        skills_dict = {"technical": [], "soft_skills": []}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Simple heuristic: if line mentions "technical", add to technical
            if "technical" in line.lower() or "programming" in line.lower():
                skills_dict["technical"].append(line)
            else:
                skills_dict["soft_skills"].append(line)

        # If no distinction made, put all in technical
        if not skills_dict["soft_skills"] and skills_dict["technical"]:
            skills_dict["soft_skills"] = skills_dict["technical"]
            skills_dict["technical"] = []

        return skills_dict

    def _parse_project_blocks(self, lines: list) -> list:
        """Parse project blocks from lines."""
        blocks = []
        current_block = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if any(
                keyword in line.lower()
                for keyword in ["project:", "name:", "role:", "tech:", "tech stack:"]
            ):
                if current_block:
                    blocks.append(current_block)
                current_block = {"name": "", "role": "", "tech_stack": [], "description": []}

                if "project:" in line.lower() or "name:" in line.lower():
                    current_block["name"] = line.split(":", 1)[1].strip()
                elif "role:" in line.lower():
                    current_block["role"] = line.split(":", 1)[1].strip()
                elif "tech:" in line.lower():
                    tech_str = line.split(":", 1)[1].strip()
                    current_block["tech_stack"] = [t.strip() for t in tech_str.split(",")]

            else:
                if not current_block:
                    current_block = {"name": line, "role": "", "tech_stack": [], "description": []}
                else:
                    current_block["description"].append(line)

        if current_block:
            blocks.append(current_block)

        return blocks

    def parse_batch(self, pdf_directory: str) -> list:
        """
        Parse multiple CVs from a directory.

        Args:
            pdf_directory: Directory containing PDF files

        Returns:
            List of parsing results
        """
        results = []

        pdf_dir = Path(pdf_directory)
        if not pdf_dir.exists():
            logger.error(f"Directory not found: {pdf_directory}")
            return results

        pdf_files = list(pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files to process")

        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"Processing {i}/{len(pdf_files)}: {pdf_path.name}")

            result = self.parse_cv(str(pdf_path))
            results.append(result)

            if not result["success"]:
                logger.warning(f"Failed to parse: {pdf_path.name}")

        # Summary
        successful = sum(1 for r in results if r["success"])
        logger.info(
            f"Batch processing complete: {successful}/{len(pdf_files)} successful"
        )

        return results
