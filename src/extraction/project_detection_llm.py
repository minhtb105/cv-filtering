"""
Task 3 Phase 2: LLM Project Detection with JSON-Only Output
Reliable project extraction using Ollama with strict JSON parsing
Confidence scoring and validation integrated
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
import logging
import requests

from src.config import settings
from src.extraction.experience_engine import ExperienceEntry

logger = logging.getLogger(__name__)


@dataclass
class ProjectDuration:
    """Project duration info"""
    start_month: Optional[int] = None
    start_year: Optional[int] = None
    end_month: Optional[int] = None
    end_year: Optional[int] = None
    duration_months: float = 0.0


@dataclass
class LLMProject:
    """LLM-extracted project data"""
    name: str
    company: str
    description: str
    technologies: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    role: str = ""
    duration: ProjectDuration = field(default_factory=ProjectDuration)
    complexity_level: str = "medium"  # low, medium, high
    ownership: str = "contributor"  # contributor, owner, technical_lead
    confidence: float = 0.75
    extraction_method: str = "llm"
    evidence_snippets: List[str] = field(default_factory=list)


class ProjectDetectionLLM:
    """LLM-powered project detection with reliability focus"""
    
    def __init__(
        self,
        model: str = "qwen2.5-coder:3b",
        ollama_url: str = "http://localhost:11434/api/generate",
        max_retries: int = 3,
        temperature: float = 0.1,
        timeout: int = 30
    ):
        self.model = model
        self.ollama_url = ollama_url
        self.max_retries = max_retries
        self.temperature = temperature
        self.timeout = timeout
        self.validator = ProjectLLMValidator()
    
    def extract_projects_from_markdown(
        self,
        markdown_cv: str,
        experience_entries: Optional[List[ExperienceEntry]] = None
    ) -> List[LLMProject]:
        """Extract projects from markdown CV with experience context"""
        
        try:
            # Extract projects section
            projects_section = self._extract_projects_section(markdown_cv)
            
            if not projects_section:
                logger.debug("No projects section found in CV")
                return []
            
            # Prepare context from experience entries
            experience_context = self._prepare_experience_context(experience_entries or [])
            
            # Build extraction prompt
            prompt = self._build_extraction_prompt(projects_section, experience_context)
            
            # Call LLM with retries
            json_response = self._call_llm_with_retries(prompt)
            
            if not json_response:
                logger.warning("Failed to get valid JSON response from LLM")
                return []
            
            # Parse and validate projects
            projects = self._parse_json_response(json_response)
            
            # Validate and score
            validated_projects = []
            for project in projects:
                validated = self.validator.validate_and_score(project)
                if validated:
                    validated_projects.append(validated)
            
            return validated_projects
        
        except Exception as e:
            logger.error(f"Error in extract_projects_from_markdown: {e}")
            return []
    
    def _extract_projects_section(self, markdown_cv: str) -> str:
        """Extract projects section from markdown CV"""
        
        SECTION_KEYWORDS = {
            'en': ['## projects', '## portfolio', '## case studies', '## key projects'],
            'vi': ['## dự án', '## dự án tiêu biểu', '## portfolio']
        }
        
        lines = markdown_cv.split('\n')
        in_projects = False
        projects_lines = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check for projects section
            for keywords in SECTION_KEYWORDS.values():
                if any(kw in line_lower for kw in keywords):
                    in_projects = True
                    continue
            
            # Check for next section (end of projects)
            if in_projects and line.startswith('##') and not any(
                kw in line_lower for kw in sum(SECTION_KEYWORDS.values(), [])
            ):
                break
            
            if in_projects:
                projects_lines.append(line)
        
        return '\n'.join(projects_lines)
    
    def _prepare_experience_context(self, experience_entries: List[ExperienceEntry]) -> str:
        """Prepare experience context for prompt"""
        
        if not experience_entries:
            return ""
        
        context_lines = ["Recent work experience for context:"]
        for entry in experience_entries[-3:]:  # Last 3 positions
            context_lines.append(f"- {entry.company}: {entry.position}")
        
        return '\n'.join(context_lines)
    
    def _build_extraction_prompt(self, projects_text: str, experience_context: str) -> str:
        """Build structured LLM prompt for JSON extraction"""
        
        prompt = f"""Extract all projects from the following CV section. 
Return ONLY valid JSON in the following format (no markdown, no explanation):

{{"projects": [
  {{
    "name": "Project Name",
    "company": "Company Name",
    "description": "Brief description of what was built",
    "technologies": ["tech1", "tech2"],
    "metrics": ["metric1", "metric2"],
    "role": "Your role",
    "complexity_level": "low|medium|high",
    "ownership": "contributor|owner|technical_lead",
    "duration_months": 6
  }}
]}}

{experience_context}

Projects to extract:
{projects_text}

Return ONLY the JSON object, no other text."""
        
        return prompt
    
    def _call_llm_with_retries(self, prompt: str) -> Optional[str]:
        """Call LLM with retry logic"""
        
        for attempt in range(self.max_retries):
            try:
                response = self._call_llm(prompt)
                
                if response and self._is_valid_json(response):
                    return response
                
                logger.debug(f"Attempt {attempt + 1}: Invalid JSON response, retrying...")
            
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1}: Error - {e}")
        
        return None
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call Ollama API"""
        
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            
            logger.error(f"Ollama API error: {response.status_code}")
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def _is_valid_json(self, text: str) -> bool:
        """Check if text contains valid JSON"""
        
        try:
            # Try to extract JSON from text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json.loads(json_match.group())
                return True
            return False
        except (json.JSONDecodeError, AttributeError):
            return False
    
    def _parse_json_response(self, response: str) -> List[Dict]:
        """Parse JSON response from LLM"""
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in response")
                return []
            
            json_str = json_match.group()
            data = json.loads(json_str)
            
            projects = data.get("projects", [])
            if isinstance(projects, list):
                return projects
            
            return []
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []


class ProjectLLMValidator:
    """Validate and score LLM-extracted projects"""
    
    REQUIRED_FIELDS = ['name', 'description', 'technologies']
    COMPLEXITY_LEVELS = ['low', 'medium', 'high']
    OWNERSHIP_LEVELS = ['contributor', 'owner', 'technical_lead']
    
    def validate_and_score(self, project_data: Dict) -> Optional[LLMProject]:
        """Validate project data and calculate confidence score"""
        
        # Check required fields
        if not self._has_required_fields(project_data):
            logger.debug(f"Project missing required fields: {project_data}")
            return None
        
        # Create project object
        try:
            duration = ProjectDuration(
                duration_months=float(project_data.get('duration_months', 0))
            )
            
            project = LLMProject(
                name=project_data.get('name', '').strip(),
                company=project_data.get('company', 'Unknown').strip(),
                description=project_data.get('description', '').strip(),
                technologies=self._normalize_list(project_data.get('technologies', [])),
                metrics=self._normalize_list(project_data.get('metrics', [])),
                role=project_data.get('role', '').strip(),
                duration=duration,
                complexity_level=self._validate_complexity(project_data.get('complexity_level', 'medium')),
                ownership=self._validate_ownership(project_data.get('ownership', 'contributor')),
                confidence=self._calculate_confidence(project_data)
            )
            
            return project
        
        except Exception as e:
            logger.error(f"Error validating project: {e}")
            return None
    
    def _has_required_fields(self, project_data: Dict) -> bool:
        """Check if project has all required fields"""
        
        for field in self.REQUIRED_FIELDS:
            if field not in project_data or not str(project_data[field]).strip():
                return False
        
        return True
    
    def _normalize_list(self, value) -> List[str]:
        """Normalize list fields"""
        
        if isinstance(value, list):
            return [str(v).strip() for v in value if v]
        elif isinstance(value, str):
            return [v.strip() for v in value.split(',') if v.strip()]
        
        return []
    
    def _validate_complexity(self, value: str) -> str:
        """Validate and normalize complexity level"""
        
        value_lower = str(value).lower().strip()
        return value_lower if value_lower in self.COMPLEXITY_LEVELS else 'medium'
    
    def _validate_ownership(self, value: str) -> str:
        """Validate and normalize ownership level"""
        
        value_lower = str(value).lower().strip()
        return value_lower if value_lower in self.OWNERSHIP_LEVELS else 'contributor'
    
    def _calculate_confidence(self, project_data: Dict) -> float:
        """Calculate confidence score (0-1)"""
        
        score = 0.75  # Base score
        
        # Add points for completeness
        if project_data.get('company'):
            score += 0.05
        if project_data.get('role'):
            score += 0.05
        if project_data.get('metrics') and len(self._normalize_list(project_data.get('metrics'))) > 0:
            score += 0.1
        if project_data.get('duration_months'):
            score += 0.05
        
        return min(score, 1.0)
