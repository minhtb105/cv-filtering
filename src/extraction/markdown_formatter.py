"""
Markdown-Enhanced CV Formatter (Phase 1)
Converts raw CV text to structured markdown sections for LLM context
Improves extraction accuracy through organizational structure
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class MarkdownCVFormatter:
    """Convert raw CV text to structured markdown sections"""
    
    SECTION_KEYWORDS = {
        'en': {
            'contact': ['contact', 'information', 'personal info', 'phone', 'email'],
            'experience': ['experience', 'work experience', 'employment', 'professional history', 'positions'],
            'projects': ['projects', 'portfolio', 'case studies', 'achievements'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise'],
            'education': ['education', 'qualifications', 'degrees', 'certifications'],
            'languages': ['languages', 'language proficiencies'],
            'certifications': ['certifications', 'certificates', 'licenses'],
            'summary': ['summary', 'objective', 'professional summary'],
            'awards': ['awards', 'recognition', 'honors'],
            'references': ['references', 'referees']
        },
        'vi': {
            'contact': ['thông tin liên hệ', 'liên hệ', 'điện thoại', 'email'],
            'experience': ['kinh nghiệm', 'kinh nghiệm làm việc', 'công việc', 'vị trí', 'positions'],
            'projects': ['dự án', 'dự án tiêu biểu', 'portfolio'],
            'skills': ['kỹ năng', 'kỹ năng kỹ thuật', 'chuyên môn'],
            'education': ['học vấn', 'bằng cấp', 'giáo dục', 'đại học'],
            'languages': ['ngôn ngữ', 'trình độ ngôn ngữ'],
            'certifications': ['chứng chỉ', 'certificates'],
            'summary': ['tóm tắt', 'mục tiêu', 'giới thiệu'],
            'awards': ['giải thưởng', 'vinh danh'],
            'references': ['người tham khảo', 'tham khảo']
        }
    }
    
    @classmethod
    def format_cv_to_markdown(
        cls,
        cv_text: str,
        contact_info: Optional[Dict] = None,
        include_contact: bool = True
    ) -> str:
        """Convert CV text to structured markdown format"""
        
        if not cv_text or not cv_text.strip():
            return ""
        
        # Extract sections
        sections = cls.extract_sections(cv_text)
        
        # Build markdown output
        markdown_lines = []
        
        # Add contact section if available
        if include_contact and contact_info:
            markdown_lines.append("## Contact Information")
            if contact_info.get('name'):
                markdown_lines.append(f"**{contact_info['name']}**")
            if contact_info.get('email'):
                markdown_lines.append(f"- Email: {contact_info['email']}")
            if contact_info.get('phone'):
                markdown_lines.append(f"- Phone: {contact_info['phone']}")
            markdown_lines.append("")
        
        # Add formatted sections
        for section_name, section_content in sections.items():
            if section_content and section_content.strip():
                markdown_lines.append(f"## {section_name.title()}")
                markdown_lines.append(section_content)
                markdown_lines.append("")
        
        return "\n".join(markdown_lines)
    
    @classmethod
    def extract_sections(cls, text: str) -> Dict[str, str]:
        """Extract and organize CV sections by keywords"""
        
        text_lower = text.lower()
        lines = text.split('\n')
        
        # Find section boundaries
        section_boundaries = cls._find_section_boundaries(text_lower, lines)
        
        sections = {}
        
        for section_name, (start_idx, end_idx) in section_boundaries.items():
            section_content = '\n'.join(lines[start_idx:end_idx])
            
            # Format based on section type
            if section_name == 'Experience':
                formatted = cls._format_experience(section_content)
            elif section_name == 'Skills':
                formatted = cls._format_skills(section_content)
            elif section_name == 'Education':
                formatted = cls._format_education(section_content)
            elif section_name == 'Projects':
                formatted = cls._format_projects(section_content)
            else:
                formatted = section_content.strip()
            
            sections[section_name] = formatted
        
        return sections
    
    @classmethod
    def _find_section_boundaries(cls, text_lower: str, lines: List[str]) -> Dict[str, Tuple[int, int]]:
        """Find start and end indices for each section"""
        
        boundaries = {}
        all_keywords = {}
        
        # Collect all keywords
        for lang in ['en', 'vi']:
            for section, keywords in cls.SECTION_KEYWORDS[lang].items():
                if section not in all_keywords:
                    all_keywords[section] = []
                all_keywords[section].extend(keywords)
        
        # Find sections
        section_starts = {}
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            for section, keywords in all_keywords.items():
                if any(kw in line_lower for kw in keywords):
                    if section not in section_starts:
                        section_starts[section] = i
                    break
        
        # Determine boundaries
        sorted_starts = sorted(section_starts.items(), key=lambda x: x[1])
        
        for idx, (section, start) in enumerate(sorted_starts):
            end = sorted_starts[idx + 1][1] if idx < len(sorted_starts) - 1 else len(lines)
            boundaries[section] = (start + 1, end)  # Skip header line
        
        return boundaries
    
    @classmethod
    def _format_experience(cls, text: str) -> str:
        """Format experience section with bullet points"""
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        formatted = []
        
        for line in lines:
            if line and not line.startswith('#'):
                # Add bullet point if not already present
                if not line.startswith('- ') and not line.startswith('• '):
                    formatted.append(f"- {line}")
                else:
                    formatted.append(line)
        
        return '\n'.join(formatted)
    
    @classmethod
    def _format_skills(cls, text: str) -> str:
        """Format skills section"""
        
        return cls._parse_skill_list(text)
    
    @classmethod
    def _format_education(cls, text: str) -> str:
        """Format education section"""
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        formatted = []
        
        for line in lines:
            if line:
                formatted.append(f"- {line}")
        
        return '\n'.join(formatted)
    
    @classmethod
    def _format_projects(cls, text: str) -> str:
        """Format projects section"""
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        formatted = []
        
        for line in lines:
            if line and not line.startswith('- '):
                formatted.append(f"- {line}")
            else:
                formatted.append(line)
        
        return '\n'.join(formatted)
    
    @classmethod
    def _parse_list_entries(cls, text: str) -> List[str]:
        """Parse list-style entries from text"""
        
        entries = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                entries.append(line)
        
        return entries
    
    @classmethod
    def _parse_skill_list(cls, text: str) -> str:
        """Parse and format skill list"""
        
        # Split by common delimiters
        skills = re.split(r'[,;]|\band\b|\bor\b|[-•]', text, flags=re.IGNORECASE)
        skills = [s.strip() for s in skills if s.strip()]
        
        # Format as bullet list
        return '\n'.join([f"- {skill}" for skill in skills[:20]])  # Limit to 20 skills
