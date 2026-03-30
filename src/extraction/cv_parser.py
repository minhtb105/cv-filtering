"""
CV Parser - Main Public API

Simplified CV parsing interface using Clean Architecture pipeline:
- STEP 1-4: Geometric extraction (PDFExtractor)
- STEP 5: LLM-based structured extraction (HRExtractorAgent)
- STEP 6: Enrichment (PostProcessor)

This parser provides a high-level interface that wraps CVProcessingPipeline,
handling file I/O, result serialization, and format conversion.

Design principle: Trust LLM output, enrich through computation only.
No keyword lists, no fuzzy matching, no regex-based section detection.
"""

import logging
import os
import json
from typing import Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from src.extraction.cv_pipeline import CVProcessingPipeline, PipelineConfig, ProcessingResult

logger = logging.getLogger(__name__)


@dataclass
class CVParsingConfig:
    """Configuration for CV parsing."""
    use_llm_extraction: bool = True
    llm_model: str = "qwen2.5-coder:3b"
    llm_base_url: str = "http://localhost:11434"
    llm_timeout: int = 30
    output_markdown_dir: Optional[str] = None
    output_json_dir: Optional[str] = None
    debug: bool = False


class CVParser:
    """Public CV parsing interface."""

    def __init__(self, config: Optional[CVParsingConfig] = None):
        """
        Initialize the CV parser.
        
        Args:
            config: CVParsingConfig instance
        """
        self.config = config or CVParsingConfig()
        
        # Initialize the processing pipeline
        pipeline_cfg = PipelineConfig(
            use_llm=self.config.use_llm_extraction,
            llm_model=self.config.llm_model,
            llm_base_url=self.config.llm_base_url,
            llm_timeout=self.config.llm_timeout,
            output_markdown_dir=self.config.output_markdown_dir,
            output_json_dir=self.config.output_json_dir,
            debug=self.config.debug,
        )
        self.pipeline = CVProcessingPipeline(config=pipeline_cfg)

    def parse_cv(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse a CV PDF file end-to-end.

        Flow:
        1. STEP 1-4: Extract geometric structure via PDFExtractor
        2. STEP 5: Extract structured data via HRExtractorAgent (LLM-based)
        3. STEP 6: Enrich with computed values via PostProcessor

        Args:
            pdf_path (str): Path to PDF file

        Returns:
            Dict with parsing results:
            {
                'success': bool,
                'filename': str,
                'extraction_method': str,
                'cleaned_text': str,
                'extracted_profile': Dict or None,
                'total_years_experience': float,
                'seniority_level': str or None,
                'markdown': str (intermediate markdown dump),
                'errors': List[str],
                'metadata': Dict
            }
        """
        result_dict = {
            "success": False,
            "filename": os.path.basename(pdf_path),
            "extraction_method": "geometric_pipeline",
            "cleaned_text": "",
            "extracted_profile": None,
            "total_years_experience": 0.0,
            "seniority_level": None,
            "markdown": "",
            "errors": [],
            "metadata": {
                "pdf_path": pdf_path,
                "file_size": os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0,
                "pipeline": "Clean Architecture (PDFExtractor → HRExtractorAgent → PostProcessor)",
            },
        }

        try:
            logger.info(f"[CVParser] Starting: {pdf_path}")

            # File validation
            if not os.path.exists(pdf_path):
                error_msg = f"File not found: {pdf_path}"
                result_dict["errors"].append(error_msg)
                logger.error(f"[CVParser] {error_msg}")
                return result_dict

            # Run the pipeline
            logger.info(f"[CVParser] Running pipeline...")
            pipeline_result: ProcessingResult = self.pipeline.process_pdf(pdf_path)

            # Copy results from pipeline
            result_dict["success"] = pipeline_result.success
            result_dict["cleaned_text"] = pipeline_result.ordered_text
            result_dict["extracted_profile"] = pipeline_result.extracted_profile
            result_dict["total_years_experience"] = pipeline_result.total_years_experience
            result_dict["seniority_level"] = pipeline_result.seniority_level
            result_dict["markdown"] = pipeline_result.intermediate_markdown
            result_dict["metadata"]["total_pages"] = pipeline_result.total_pages
            result_dict["metadata"]["extraction_status"] = pipeline_result.metadata.get("extraction_status", "unknown")
            
            if pipeline_result.error:
                result_dict["errors"].append(pipeline_result.error)
                logger.error(f"[CVParser] Pipeline error: {pipeline_result.error}")
                return result_dict

            logger.info(
                f"[CVParser] Success: "
                f"{pipeline_result.total_pages} pages, "
                f"{pipeline_result.total_years_experience} years exp, "
                f"{pipeline_result.seniority_level} seniority"
            )

        except Exception as e:
            logger.error(f"[CVParser] Unexpected error: {e}", exc_info=True)
            result_dict["errors"].append(f"Parsing error: {str(e)}")

        return result_dict

    def parse_batch(
        self,
        pdf_dir: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Parse multiple CV PDFs in a directory.

        Args:
            pdf_dir (str): Directory containing PDF files
            output_dir (str): Optional output directory for results

        Returns:
            Dict[filename] → parse_cv result
        """
        results = {}
        pdf_files = list(Path(pdf_dir).glob("*.pdf"))

        logger.info(f"[CVParser] Batch: Starting {len(pdf_files)} files")

        for pdf_file in pdf_files:
            logger.info(f"[CVParser] Batch: {pdf_file.name}")
            result = self.parse_cv(str(pdf_file))
            results[pdf_file.name] = result

            # Save individual results if output_dir specified
            if output_dir and result["success"]:
                output_path = os.path.join(output_dir, f"{pdf_file.stem}_result.json")
                os.makedirs(output_dir, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info(f"[CVParser] Batch: Complete {len(results)} files")
        return results

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

    def _extract_personal_info_from_sections(self, sections_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Extract personal info from extracted sections (from geometric pipeline).
        
        This method processes the sections output from the new pipeline
        to extract name, email, phone, location.
        """
        import re

        personal_info = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
        }

        # Combine all content to search within
        all_content = " ".join(sections_dict.values())

        # Email pattern
        email_match = re.search(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            all_content
        )
        if email_match:
            personal_info["email"] = email_match.group()

        # Phone pattern (basic)
        phone_match = re.search(
            r'(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}',
            all_content,
        )
        if phone_match:
            personal_info["phone"] = phone_match.group().strip()

        # Name: check personal_info section first, then first section
        if "personal_info" in sections_dict:
            pi_content = sections_dict["personal_info"]
            first_line = pi_content.split("\n")[0].strip() if pi_content else ""
            if first_line and len(first_line) < 100 and not email_match:
                personal_info["name"] = first_line

        # Location: check personal_info section
        if "personal_info" in sections_dict and not personal_info["location"]:
            pi_content = sections_dict["personal_info"]
            location_match = re.search(r'(?:location|city|address)[:\s]+([^\n]+)', pi_content, re.IGNORECASE)
            if location_match:
                personal_info["location"] = location_match.group(1).strip()

        return personal_info

    def _structure_sections_for_markdown_from_dict(self, sections_dict: Dict[str, str]) -> Dict:
        """
        Structure sections dictionary for markdown generation.
        
        Converts flat section dictionary from pipeline into structured format
        expected by MarkdownGenerator.
        """
        structured = {
            "work_experience": [],
            "education": [],
            "skills": {},
            "projects": [],
            "certifications": {},
        }

        # Work experience
        if "experience" in sections_dict:
            exp_lines = sections_dict["experience"].split("\n")
            exp_blocks = self._parse_experience_blocks(exp_lines)
            structured["work_experience"] = exp_blocks

        # Education
        if "education" in sections_dict:
            edu_lines = sections_dict["education"].split("\n")
            edu_blocks = self._parse_education_blocks(edu_lines)
            structured["education"] = edu_blocks

        # Skills
        if "skills" in sections_dict:
            skill_lines = sections_dict["skills"].split("\n")
            skill_dict = self._parse_skills(skill_lines)
            structured["skills"] = skill_dict

        # Projects
        if "projects" in sections_dict:
            proj_lines = sections_dict["projects"].split("\n")
            proj_blocks = self._parse_project_blocks(proj_lines)
            structured["projects"] = proj_blocks

        # Certifications, Languages, Awards, Interests as lists
        cert_dict = {}
        for section_type in ["certifications", "languages", "awards", "interests"]:
            if section_type in sections_dict:
                lines = sections_dict[section_type].split("\n")
                cert_dict[section_type] = [l.strip() for l in lines if l.strip()]

        structured["certifications"] = cert_dict

        return structured
