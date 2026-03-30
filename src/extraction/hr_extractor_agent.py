"""
HR Extractor Agent - Main CV Processing Engine
Integrates multiple extraction layers:
1. Markdown formatting for structure
2. Rule-based extraction for high-confidence fields
3. Experience engine for date parsing and career analysis
4. LLM project detection for complex information

All methods return normalized, validated data with confidence scores
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

from src.config import settings
from src.extraction.markdown_formatter import MarkdownCVFormatter
from src.extraction.enhanced_rules import EnhancedRuleExtractor, ExtractedField
from src.extraction.experience_engine import (
    DateParser, ExperienceExtractor, ExperienceEngine, ExperienceEntry, DateRange
)
from src.extraction.project_detection_llm import ProjectDetectionLLM, ProjectLLMValidator, LLMProject
from src.extraction.evidence_linker import EvidenceLinker, EvidenceType, EvidenceValidator

logger = logging.getLogger(__name__)


class HRExtractorAgent:
    """Main CV extraction agent with multi-layer intelligent pipeline"""
    
    def __init__(self):
        self.markdown_formatter = MarkdownCVFormatter()
        self.rule_extractor = EnhancedRuleExtractor()
        self.date_parser = DateParser()
        self.experience_extractor = ExperienceExtractor()
        self.experience_engine = ExperienceEngine()
        self.project_detector = ProjectDetectionLLM()
        self.project_validator = ProjectLLMValidator()
        self.evidence_linker = EvidenceLinker()  # Task 4: Evidence linking
    
    def extract_cv(self, cv_text: str) -> Dict:
        """Main extraction pipeline - process CV and return structured data"""
        
        if not cv_text or not cv_text.strip():
            logger.warning("Empty CV text provided")
            return self._empty_extraction()
        
        try:
            # Step 0: Initialize evidence linking (Task 4)
            self.evidence_linker.set_cv_text(cv_text)
            
            # Step 1: Convert to markdown for structure
            markdown_cv = self.markdown_formatter.format_cv_to_markdown(cv_text)
            
            # Step 2: Extract basic contact info using rules
            contact_info = self._extract_contact_info(cv_text)
            
            # Step 3: Extract professional info using rules
            professional_info = self._extract_professional_info(cv_text)
            
            # Step 4: Extract experience with date parsing
            years_experience = self._extract_years_experience(markdown_cv)
            seniority = self._infer_seniority(markdown_cv, years_experience)
            
            # Step 5: Extract projects using LLM with experience context
            experience_entries = self._extract_experience_entries(markdown_cv)
            projects = self._extract_projects_and_skills_llm_enhanced(markdown_cv, experience_entries)
            
            # Step 6: Collect evidence for extracted fields (Task 4)
            evidence_report = self._collect_evidence_for_extraction(contact_info, professional_info)
            
            # Compile final result
            result = {
                'contact': contact_info,
                'professional': professional_info,
                'experience': {
                    'years': years_experience,
                    'seniority': seniority,
                    'entries': experience_entries
                },
                'projects': projects.get('projects', []),
                'skills': projects.get('skills', []),
                'extraction_status': 'success',
                'evidence': evidence_report,
                'timestamp': datetime.now(datetime.timezone.utc).isoformat()
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error in extract_cv: {e}")
            return self._error_extraction(str(e))
    
    def _collect_evidence_for_extraction(
        self,
        contact_info: Dict,
        professional_info: Dict
    ) -> Dict:
        """Collect evidence for all extracted fields (Task 4)"""
        
        try:
            # Link evidence for contact info
            for field_name, field_data in contact_info.items():
                if field_data and field_data.get('value'):
                    evidence = self.evidence_linker.find_evidence_for_field(
                        field_name,
                        field_data['value'],
                        EvidenceType.DIRECT_MATCH
                    )
                    evidence.extraction_method = field_data.get('source', 'unknown')
            
            # Link evidence for professional info
            for field_name, field_data in professional_info.items():
                if field_data and field_data.get('value'):
                    evidence = self.evidence_linker.find_evidence_for_field(
                        field_name,
                        field_data['value'],
                        EvidenceType.PATTERN_MATCH
                    )
                    evidence.extraction_method = field_data.get('source', 'unknown')
            
            # Generate evidence report
            return self.evidence_linker.get_evidence_report()
        
        except Exception as e:
            logger.error(f"Error collecting evidence: {e}")
            return {'error': str(e)}
    
    def _extract_contact_info(self, text: str) -> Dict[str, Optional[ExtractedField]]:
        """Extract contact information using rule-based extraction"""
        
        try:
            contact = self.rule_extractor.extract_contact_info(text)
            
            # Convert ExtractedField objects to dicts for JSON serialization
            return {
                key: {
                    'value': field.value,
                    'confidence': field.confidence,
                    'source': field.source
                } if field else None
                for key, field in contact.items()
            }
        
        except Exception as e:
            logger.error(f"Error extracting contact info: {e}")
            return {}
    
    def _extract_professional_info(self, text: str) -> Dict[str, Optional[ExtractedField]]:
        """Extract professional information"""
        
        try:
            professional = self.rule_extractor.extract_professional_info(text)
            
            return {
                key: {
                    'value': field.value,
                    'confidence': field.confidence,
                    'source': field.source
                } if field else None
                for key, field in professional.items()
            }
        
        except Exception as e:
            logger.error(f"Error extracting professional info: {e}")
            return {}
    
    def _extract_years_experience(self, markdown_cv: str) -> float:
        """Extract and calculate total years of experience"""
        
        try:
            # Extract experience entries from markdown
            experience_section = self.experience_extractor.extract_experience_section(markdown_cv)
            experience_text = '\n'.join(experience_section)
            
            if not experience_text.strip():
                logger.debug("No experience section found")
                return 0.0
            
            # Parse entries
            entries = self.experience_extractor.extract_entries(experience_text)
            
            if not entries:
                logger.debug("No experience entries parsed")
                return 0.0
            
            # Calculate total years
            total_years = self.experience_engine.calculate_total_years(entries)
            
            return round(total_years, 1)
        
        except Exception as e:
            logger.error(f"Error calculating years experience: {e}")
            return 0.0
    
    def _infer_seniority(self, markdown_cv: str, years_experience: float) -> str:
        """Infer seniority level based on experience and titles"""
        
        try:
            # Get experience entries for analysis
            experience_section = self.experience_extractor.extract_experience_section(markdown_cv)
            experience_text = '\n'.join(experience_section)
            
            entries = self.experience_extractor.extract_entries(experience_text)
            
            if not entries:
                return 'unknown'
            
            # Analyze progression
            progression = self.experience_engine.analyze_progression(entries)
            
            # Determine seniority based on years and progression
            if years_experience < 2:
                return 'junior'
            elif years_experience < 5:
                if progression.get('progression') == 'healthy':
                    return 'mid'
                else:
                    return 'junior'
            elif years_experience < 10:
                if progression.get('progression') == 'healthy':
                    return 'senior'
                else:
                    return 'mid'
            else:
                if progression.get('progression') == 'healthy':
                    return 'principal'
                else:
                    return 'senior'
        
        except Exception as e:
            logger.error(f"Error inferring seniority: {e}")
            return 'unknown'
    
    def _extract_experience_entries(self, markdown_cv: str) -> List[Dict]:
        """Extract experience entries with date parsing"""
        
        try:
            experience_section = self.experience_extractor.extract_experience_section(markdown_cv)
            experience_text = '\n'.join(experience_section)
            
            entries = self.experience_extractor.extract_entries(experience_text)
            
            # Convert to dict format
            result = []
            for entry in entries:
                result.append({
                    'company': entry.company,
                    'position': entry.position,
                    'duration_months': entry.get_duration_months(),
                    'duration_years': round(entry.get_duration_years(), 1),
                    'description': entry.description
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error extracting experience entries: {e}")
            return []
    
    def _extract_projects_and_skills_llm_enhanced(
        self,
        markdown_cv: str,
        experience_entries: List[Dict]
    ) -> Dict:
        """Extract projects using LLM with experience context"""
        
        try:
            # Convert dict entries back to ExperienceEntry objects for context
            experience_objs = []
            for entry_dict in experience_entries:
                exp_entry = ExperienceEntry(
                    company=entry_dict.get('company', ''),
                    position=entry_dict.get('position', ''),
                    date_range=DateRange(start_date=None, end_date=None),
                    description=entry_dict.get('description', '')
                )
                experience_objs.append(exp_entry)
            
            # Extract projects using LLM
            projects = self.project_detector.extract_projects_from_markdown(
                markdown_cv,
                experience_entries=experience_objs
            )
            
            # Extract skills using rule-based method as fallback
            skill_field = self.rule_extractor.skill_extractor.extract(markdown_cv)
            skills = []
            if skill_field:
                skills = [s.strip() for s in skill_field.value.split(',')]
            
            # Compile results
            return {
                'projects': [
                    {
                        'name': p.name,
                        'company': p.company,
                        'description': p.description,
                        'technologies': p.technologies,
                        'metrics': p.metrics,
                        'role': p.role,
                        'complexity_level': p.complexity_level,
                        'confidence': p.confidence
                    }
                    for p in projects
                ],
                'skills': skills,
                'skills_confidence': skill_field.confidence if skill_field else 0.0
            }
        
        except Exception as e:
            logger.error(f"Error extracting projects and skills: {e}")
            # Return fallback with just skills
            skill_field = self.rule_extractor.skill_extractor.extract(markdown_cv)
            return {
                'projects': [],
                'skills': [s.strip() for s in skill_field.value.split(',')] if skill_field else [],
                'extraction_error': str(e)
            }
    
    def _empty_extraction(self) -> Dict:
        """Return empty structured response"""
        
        return {
            'contact': {},
            'professional': {},
            'experience': {
                'years': 0.0,
                'seniority': 'unknown',
                'entries': []
            },
            'projects': [],
            'skills': [],
            'extraction_status': 'empty_input',
            'evidence': {'total_fields': 0, 'average_confidence': 0.0, 'fields': {}},
            'timestamp': datetime.now(datetime.timezone.utc).isoformat()
        }
    
    def _error_extraction(self, error_msg: str) -> Dict:
        """Return error structured response"""
        
        return {
            'contact': {},
            'professional': {},
            'experience': {
                'years': 0.0,
                'seniority': 'unknown',
                'entries': []
            },
            'projects': [],
            'skills': [],
            'extraction_status': 'error',
            'error_message': error_msg,
            'evidence': {'total_fields': 0, 'average_confidence': 0.0, 'fields': {}},
            'timestamp': datetime.now(datetime.timezone.utc).isoformat()
        }
