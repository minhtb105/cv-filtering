"""
Project Validation Module

Comprehensive validation for project data with confidence scoring and quality checks.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass

from src.models.domain.project import LLMProject, ProjectDuration


@dataclass
class ProjectValidationResult:
    """Result of project validation"""
    is_valid: bool
    confidence: float
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    field_scores: Dict[str, float]


class ProjectValidator:
    """Comprehensive project validator with confidence scoring"""
    
    REQUIRED_FIELDS = ['name', 'description', 'technologies']
    COMPLEXITY_LEVELS = ['low', 'medium', 'high']
    OWNERSHIP_LEVELS = ['contributor', 'owner', 'technical_lead']
    PROJECT_TYPES = ['web', 'mobile', 'desktop', 'api', 'database', 'infrastructure', 'unknown']
    
    @classmethod
    def validate_project(cls, project: LLMProject) -> ProjectValidationResult:
        """Validate complete project with scoring"""
        errors = []
        warnings = []
        suggestions = []
        field_scores = {}
        confidence = 0.75  # Base confidence
        
        # Validate required fields
        for field in cls.REQUIRED_FIELDS:
            value = getattr(project, field)
            if not value or (isinstance(value, list) and len(value) == 0):
                errors.append(f"Required field '{field}' is missing or empty")
                field_scores[field] = 0.0
            else:
                field_scores[field] = 1.0
                confidence += 0.1
        
        # Validate name
        name_score = cls._validate_name(project.name)
        field_scores['name'] = name_score
        if name_score < 0.5:
            errors.append("Project name is too short or invalid")
        elif name_score < 0.8:
            warnings.append("Project name could be more descriptive")
        
        # Validate company
        company_score = cls._validate_company(project.company)
        field_scores['company'] = company_score
        if company_score < 0.3:
            errors.append("Company name is invalid")
        elif company_score < 0.7:
            warnings.append("Company name could be more specific")
        
        # Validate description
        desc_score = cls._validate_description(project.description)
        field_scores['description'] = desc_score
        if desc_score < 0.3:
            errors.append("Project description is too short or empty")
        elif desc_score < 0.7:
            suggestions.append("Consider adding more technical details to the description")
        
        # Validate technologies
        tech_score = cls._validate_technologies(project.technologies)
        field_scores['technologies'] = tech_score
        if tech_score < 0.3:
            errors.append("No technologies specified or too many invalid technologies")
        elif tech_score < 0.7:
            suggestions.append("Consider adding more specific technologies")
        
        # Validate role
        role_score = cls._validate_role(project.role)
        field_scores['role'] = role_score
        if role_score < 0.3:
            warnings.append("Role description is missing or too generic")
        elif role_score < 0.7:
            suggestions.append("Consider being more specific about your role")
        
        # Validate duration
        duration_score = cls._validate_duration(project.duration)
        field_scores['duration'] = duration_score
        if duration_score < 0.3:
            warnings.append("Project duration is missing or invalid")
        elif duration_score < 0.7:
            suggestions.append("Consider adding more specific dates")
        
        # Validate complexity level
        complexity_score = cls._validate_complexity(project.complexity_level)
        field_scores['complexity_level'] = complexity_score
        if complexity_score < 0.5:
            errors.append(f"Invalid complexity level: {project.complexity_level}")
        
        # Validate ownership
        ownership_score = cls._validate_ownership(project.ownership)
        field_scores['ownership'] = ownership_score
        if ownership_score < 0.5:
            errors.append(f"Invalid ownership level: {project.ownership}")
        
        # Validate metrics
        metrics_score = cls._validate_metrics(project.metrics)
        field_scores['metrics'] = metrics_score
        if metrics_score < 0.3:
            warnings.append("No metrics provided - consider adding quantifiable outcomes")
        elif metrics_score < 0.7:
            suggestions.append("Consider adding more specific metrics with numbers")
        
        # Validate project type
        type_score = cls._validate_project_type(project.project_type)
        field_scores['project_type'] = type_score
        if type_score < 0.5:
            warnings.append("Project type is unknown - consider specifying web/mobile/etc.")
        
        # Calculate overall confidence
        total_score = sum(field_scores.values())
        max_possible = len(field_scores)
        confidence = min(1.0, max(0.0, total_score / max_possible))
        
        # Add bonuses for good practices
        if project.confidence > 0.8:
            confidence = min(1.0, confidence + 0.1)
        
        if len(project.technologies) >= 3:
            confidence = min(1.0, confidence + 0.05)
        
        if project.metrics and len(project.metrics) >= 2:
            confidence = min(1.0, confidence + 0.05)
        
        # Check for inconsistencies
        inconsistencies = cls._check_inconsistencies(project)
        if inconsistencies:
            warnings.extend(inconsistencies)
            confidence = max(0.0, confidence - 0.1)
        
        return ProjectValidationResult(
            is_valid=len(errors) == 0,
            confidence=confidence,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            field_scores=field_scores
        )
    
    @staticmethod
    def _validate_name(name: str) -> float:
        """Validate project name"""
        if not name or not isinstance(name, str):
            return 0.0
        
        name = name.strip()
        if len(name) < 2:
            return 0.0
        if len(name) > 100:
            return 0.3
        
        # Check for meaningful content
        meaningful_words = [w for w in name.split() if len(w) > 2]
        if len(meaningful_words) < 1:
            return 0.4
        
        # Check for special characters (some are ok, too many are not)
        special_chars = sum(1 for c in name if not c.isalnum() and c not in ' -_&()')
        if special_chars > len(name) * 0.3:
            return 0.5
        
        return 0.8 if len(meaningful_words) >= 2 else 0.6
    
    @staticmethod
    def _validate_company(company: str) -> float:
        """Validate company name"""
        if not company or not isinstance(company, str):
            return 0.0
        
        company = company.strip()
        if len(company) < 2:
            return 0.0
        if len(company) > 100:
            return 0.3
        
        # Check for company-like patterns
        if any(word in company.lower() for word in ['company', 'corporation', 'inc', 'llc', 'ltd']):
            return 0.8
        
        # Check for meaningful content
        meaningful_words = [w for w in company.split() if len(w) > 2]
        if len(meaningful_words) < 1:
            return 0.4
        
        return 0.7 if len(meaningful_words) >= 2 else 0.5
    
    @staticmethod
    def _validate_description(description: str) -> float:
        """Validate project description"""
        if not description or not isinstance(description, str):
            return 0.0
        
        description = description.strip()
        if len(description) < 10:
            return 0.0
        if len(description) > 2000:
            return 0.5
        
        # Check for technical content
        technical_keywords = ['develop', 'build', 'create', 'implement', 'design', 'architecture', 'system', 'solution']
        tech_count = sum(1 for word in description.lower().split() if word in technical_keywords)
        
        # Check for action verbs
        action_verbs = ['developed', 'built', 'created', 'implemented', 'designed', 'architected', 'engineered']
        action_count = sum(1 for word in description.lower().split() if word in action_verbs)
        
        score = 0.3 + (len(description) / 1000) * 0.3 + (tech_count * 0.1) + (action_count * 0.1)
        return min(1.0, score)
    
    @staticmethod
    def _validate_technologies(technologies: List[str]) -> float:
        """Validate technology list"""
        if not technologies or not isinstance(technologies, list):
            return 0.0
        
        if len(technologies) == 0:
            return 0.0
        
        # Common technology patterns
        tech_patterns = [
            r'python', r'java', r'javascript', r'typescript', r'c#', r'c\+\+', r'go', r'rust',
            r'react', r'vue', r'angular', r'django', r'flask', r'spring', r'node\.js',
            r'docker', r'kubernetes', r'aws', r'azure', r'gcp', r'postgresql', r'mongodb',
            r'git', r'github', r'gitlab', r'jenkins', r'devops', r'ci/cd'
        ]
        
        valid_count = 0
        for tech in technologies:
            tech_lower = tech.lower().strip()
            if any(re.search(pattern, tech_lower) for pattern in tech_patterns):
                valid_count += 1
        
        score = valid_count / len(technologies) if technologies else 0.0
        return score * 0.8 + 0.2  # Base score of 0.2 for having technologies
    
    @staticmethod
    def _validate_role(role: str) -> float:
        """Validate role description"""
        if not role or not isinstance(role, str):
            return 0.3  # Partial score for missing role
        
        role = role.strip().lower()
        if len(role) < 3:
            return 0.2
        
        # Role keywords
        role_keywords = ['developer', 'engineer', 'architect', 'lead', 'manager', 'analyst', 'designer']
        has_role_keyword = any(keyword in role for keyword in role_keywords)
        
        # Action keywords
        action_keywords = ['responsible', 'led', 'managed', 'developed', 'designed', 'implemented']
        has_action_keyword = any(keyword in role for keyword in action_keywords)
        
        score = 0.3
        if has_role_keyword:
            score += 0.3
        if has_action_keyword:
            score += 0.2
        if len(role) > 20:
            score += 0.2
        
        return min(1.0, score)
    
    @staticmethod
    def _validate_duration(duration: ProjectDuration) -> float:
        """Validate project duration"""
        if not duration or (not duration.start_year and not duration.start_month):
            return 0.3  # Partial score for missing duration
        
        if duration.start_year and duration.start_year < 1990:
            return 0.2  # Too old
        
        if duration.start_year and duration.start_year > 2030:
            return 0.2  # Too far in future
        
        if duration.duration_months < 0:
            return 0.0
        
        if duration.duration_months == 0:
            return 0.4  # Missing duration
        
        if duration.duration_months > 120:  # More than 10 years
            return 0.6  # Suspiciously long
        
        # Good duration range
        if 3 <= duration.duration_months <= 60:  # 3 months to 5 years
            return 0.9
        
        return 0.7
    
    @staticmethod
    def _validate_complexity(complexity: str) -> float:
        """Validate complexity level"""
        if not complexity or complexity not in ProjectValidator.COMPLEXITY_LEVELS:
            return 0.0
        return 1.0
    
    @staticmethod
    def _validate_ownership(ownership: str) -> float:
        """Validate ownership level"""
        if not ownership or ownership not in ProjectValidator.OWNERSHIP_LEVELS:
            return 0.0
        return 1.0
    
    @staticmethod
    def _validate_metrics(metrics: List[str]) -> float:
        """Validate metrics list"""
        if not metrics or not isinstance(metrics, list):
            return 0.2  # Partial score for missing metrics
        
        if len(metrics) == 0:
            return 0.2
        
        # Check for quantitative metrics
        quantitative_patterns = [
            r'\d+%', r'\d+\+', r'\d+x', r'\d+\.?\d*\s*(ms|seconds?|minutes?|hours?)',
            r'\d+\.?\d*\s*(users?|customers?|clients?)', r'\d+\.?\d*\s*(lines? of code|loc)'
        ]
        
        quantitative_count = 0
        for metric in metrics:
            metric_lower = metric.lower().strip()
            if any(re.search(pattern, metric_lower) for pattern in quantitative_patterns):
                quantitative_count += 1
        
        score = quantitative_count / len(metrics) if metrics else 0.0
        return score * 0.7 + 0.3  # Base score of 0.3 for having metrics
    
    @staticmethod
    def _validate_project_type(project_type: str) -> float:
        """Validate project type"""
        if not project_type or project_type not in ProjectValidator.PROJECT_TYPES:
            return 0.3  # Partial score for unknown type
        return 1.0 if project_type != 'unknown' else 0.5
    
    @staticmethod
    def _check_inconsistencies(project: LLMProject) -> List[str]:
        """Check for logical inconsistencies in project data"""
        inconsistencies = []
        
        # Check if duration is very short but complexity is high
        if project.duration.duration_months < 3 and project.complexity_level == 'high':
            inconsistencies.append("High complexity with very short duration may be inconsistent")
        
        # Check if no technologies but high complexity
        if len(project.technologies) == 0 and project.complexity_level == 'high':
            inconsistencies.append("High complexity project should specify technologies used")
        
        # Check if ownership is 'owner' but no metrics provided
        if project.ownership == 'owner' and len(project.metrics) == 0:
            inconsistencies.append("Project owner should provide measurable outcomes")
        
        # Check if role is very generic for a complex project
        generic_roles = ['developer', 'programmer', 'coder']
        if (project.complexity_level in ['high', 'medium'] and 
            project.role.lower() in generic_roles and 
            len(project.role) < 20):
            inconsistencies.append("Complex project should have more specific role description")
        
        return inconsistencies
    
    @classmethod
    def validate_project_dict(cls, project_dict: Dict[str, Any]) -> ProjectValidationResult:
        """Validate project from dictionary data"""
        try:
            # Create project object from dict
            duration_data = project_dict.get('duration', {})
            duration = ProjectDuration(
                start_month=duration_data.get('start_month'),
                start_year=duration_data.get('start_year'),
                end_month=duration_data.get('end_month'),
                end_year=duration_data.get('end_year'),
                duration_months=duration_data.get('duration_months', 0.0)
            )
            
            project = LLMProject(
                name=project_dict.get('name', ''),
                company=project_dict.get('company', ''),
                description=project_dict.get('description', ''),
                technologies=project_dict.get('technologies', []),
                metrics=project_dict.get('metrics', []),
                role=project_dict.get('role', ''),
                duration=duration,
                complexity_level=project_dict.get('complexity_level', 'medium'),
                ownership=project_dict.get('ownership', 'contributor'),
                confidence=project_dict.get('confidence', 0.75),
                extraction_method=project_dict.get('extraction_method', 'llm'),
                evidence_snippets=project_dict.get('evidence_snippets', []),
                normalized_technologies=project_dict.get('normalized_technologies', []),
                impact_score=project_dict.get('impact_score', 0.0),
                business_value=project_dict.get('business_value', ''),
                team_size=project_dict.get('team_size'),
                project_type=project_dict.get('project_type', 'unknown'),
                start_date_str=project_dict.get('start_date_str'),
                end_date_str=project_dict.get('end_date_str')
            )
            
            return cls.validate_project(project)
        except Exception as e:
            return ProjectValidationResult(
                is_valid=False,
                confidence=0.0,
                errors=[f"Failed to validate project dictionary: {str(e)}"],
                warnings=[],
                suggestions=[],
                field_scores={}
            )