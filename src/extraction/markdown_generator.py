"""
Markdown Generator Module

Generates structured, machine-readable markdown from extracted CV data.
Each section starts with ## for consistent parsing.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CVMarkdownConfig:
    """Configuration for markdown generation."""
    include_timestamps: bool = True
    use_bullets: bool = True
    normalize_spacing: bool = True


class MarkdownGenerator:
    """Generates structured markdown from CV sections."""

    TEMPLATE = """# CV - {name}

**Generated**: {timestamp}
**Source**: {source}

## Personal Information
- Name: {name}
- Email: {email}
- Phone: {phone}
- Location: {location}

## Summary / Objective
{summary}

## Work Experience
{work_experience}

## Education
{education}

## Skills
{skills}

## Projects
{projects}

## Certifications / Languages / Awards / Interests
{certifications}
"""

    @staticmethod
    def format_section_header(section_name: str) -> str:
        """Format section name as markdown header."""
        return f"## {section_name}"

    @staticmethod
    def format_bullet_list(items: List[str], indent: int = 0) -> str:
        """Format list as bullets."""
        if not items:
            return ""

        prefix = "  " * indent
        return "\n".join(f"{prefix}- {item.strip()}" for item in items if item.strip())

    @staticmethod
    def format_key_value_pairs(pairs: Dict[str, str], indent: int = 0) -> str:
        """Format key-value pairs with machine-readable format."""
        if not pairs:
            return ""

        prefix = "  " * indent
        lines = []
        for key, value in pairs.items():
            if value:
                lines.append(f"{prefix}- {key}: {value.strip()}")
        return "\n".join(lines)

    @staticmethod
    def format_work_experience(experiences: List[Dict]) -> str:
        """Format work experience section."""
        if not experiences:
            return "*None provided*"

        sections = []
        for i, exp in enumerate(experiences, 1):
            company = exp.get("company", "Unknown Company")
            position = exp.get("position", "Unknown Position")
            duration = exp.get("duration", "")
            description = exp.get("description", "")

            section = f"\n### {i}. {position} at {company}"

            if duration:
                section += f"\n- Duration: {duration}"

            if description:
                # Handle description as list or string
                if isinstance(description, list):
                    section += "\n- Responsibilities:\n"
                    section += MarkdownGenerator.format_bullet_list(
                        description, indent=2
                    )
                else:
                    section += f"\n- Description: {description}"

            sections.append(section)

        return "\n".join(sections)

    @staticmethod
    def format_education(educations: List[Dict]) -> str:
        """Format education section."""
        if not educations:
            return "*None provided*"

        sections = []
        for i, edu in enumerate(educations, 1):
            school = edu.get("school", "Unknown School")
            degree = edu.get("degree", "")
            field = edu.get("field", "")
            gpa = edu.get("gpa", "")
            graduation_date = edu.get("graduation_date", "")

            section = f"\n### {i}. {school}"

            if degree or field:
                degree_str = degree
                if field and degree:
                    degree_str = f"{degree} in {field}"
                elif field:
                    degree_str = f"Major: {field}"
                section += f"\n- Degree: {degree_str}"

            if gpa:
                section += f"\n- GPA: {gpa}"

            if graduation_date:
                section += f"\n- Graduation: {graduation_date}"

            sections.append(section)

        return "\n".join(sections)

    @staticmethod
    def format_skills(skills: Dict[str, List[str]]) -> str:
        """Format skills section."""
        if not skills:
            return "*None provided*"

        sections = []

        for category, skill_list in skills.items():
            if skill_list:
                formatted_list = MarkdownGenerator.format_bullet_list(skill_list)
                sections.append(f"### {category}\n{formatted_list}")

        return "\n".join(sections) if sections else "*None provided*"

    @staticmethod
    def format_projects(projects: List[Dict]) -> str:
        """Format projects section."""
        if not projects:
            return "*None provided*"

        sections = []
        for i, project in enumerate(projects, 1):
            name = project.get("name", "Unnamed Project")
            role = project.get("role", "")
            tech_stack = project.get("tech_stack", [])
            description = project.get("description", "")

            section = f"\n### {i}. {name}"

            if role:
                section += f"\n- Role: {role}"

            if tech_stack:
                if isinstance(tech_stack, list):
                    section += f"\n- Tech Stack: {', '.join(tech_stack)}"
                else:
                    section += f"\n- Tech Stack: {tech_stack}"

            if description:
                if isinstance(description, list):
                    section += "\n- Description:\n"
                    section += MarkdownGenerator.format_bullet_list(
                        description, indent=2
                    )
                else:
                    section += f"\n- Description: {description}"

            sections.append(section)

        return "\n".join(sections)

    @staticmethod
    def format_certifications(certifications: Dict[str, List[str]]) -> str:
        """Format certifications/languages/awards/interests section."""
        if not certifications:
            return "*None provided*"

        sections = []

        for category, items in certifications.items():
            if items:
                formatted_list = MarkdownGenerator.format_bullet_list(items)
                if formatted_list:
                    sections.append(f"**{category}**\n{formatted_list}")

        return "\n".join(sections) if sections else "*None provided*"

    @staticmethod
    def generate_markdown(
        personal_info: Dict,
        sections: Dict[str, List],
        source_file: str = "Unknown",
        config: Optional[CVMarkdownConfig] = None,
    ) -> str:
        """
        Generate complete structured markdown CV.

        Args:
            personal_info: Dict with name, email, phone, location
            sections: Dict[section_type] → List/Dict of content
            source_file: Original PDF filename
            config: Generation configuration

        Returns:
            Structured markdown string
        """
        if config is None:
            config = CVMarkdownConfig()

        timestamp = (
            datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            if config.include_timestamps
            else ""
        )

        # Extract personal info with defaults
        name = personal_info.get("name", "Unknown")
        email = personal_info.get("email", "")
        phone = personal_info.get("phone", "")
        location = personal_info.get("location", "")
        summary = personal_info.get("summary", "")

        # Extract sections with defaults
        work_experience = sections.get("work_experience", [])
        education = sections.get("education", [])
        skills = sections.get("skills", {})
        projects = sections.get("projects", [])
        certifications = sections.get("certifications", {})

        # Format each section
        formatted_work = MarkdownGenerator.format_work_experience(work_experience)
        formatted_edu = MarkdownGenerator.format_education(education)
        formatted_skills = MarkdownGenerator.format_skills(skills)
        formatted_projects = MarkdownGenerator.format_projects(projects)
        formatted_certs = MarkdownGenerator.format_certifications(certifications)

        # Build markdown
        markdown = f"""# CV - {name}

**Generated**: {timestamp}
**Source**: {source_file}

## Personal Information
- Name: {name}
- Email: {email if email else "*Not provided*"}
- Phone: {phone if phone else "*Not provided*"}
- Location: {location if location else "*Not provided*"}

## Summary / Objective
{summary if summary else "*Not provided*"}

## Work Experience
{formatted_work}

## Education
{formatted_edu}

## Skills
{formatted_skills}

## Projects
{formatted_projects}

## Certifications / Languages / Awards / Interests
{formatted_certs}
"""

        return markdown

    @staticmethod
    def normalize_markdown(markdown: str) -> str:
        """
        Normalize markdown:
        - Ensure consistent spacing
        - Remove excessive blank lines
        - Fix indentation
        """
        lines = markdown.split("\n")
        normalized = []
        prev_blank = False

        for line in lines:
            if not line.strip():
                # Avoid consecutive blank lines
                if not prev_blank:
                    normalized.append("")
                    prev_blank = True
            else:
                normalized.append(line)
                prev_blank = False

        # Remove trailing blank lines
        while normalized and not normalized[-1].strip():
            normalized.pop()

        return "\n".join(normalized)

    @staticmethod
    def save_markdown(markdown: str, output_path: str) -> None:
        """Save markdown to file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
