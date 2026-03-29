"""
Task 1 Phase 2: Enhanced Rule-Based Extractors
High-confidence extraction with Vietnamese support and confidence scores
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
from enum import Enum
import logging

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractedField:
    """Extracted field with confidence and source tracking"""
    value: str
    confidence: float  # 0-1 scale
    source: str
    evidence: str


class NameExtractor:
    """Extract full name with confidence tracking"""
    
    @staticmethod
    def extract(text: str) -> Optional[ExtractedField]:
        """Extract name from CV text"""
        
        if not text or not text.strip():
            return None
        
        lines = text.split('\n')
        
        # Strategy 1: First non-empty line (often name)
        for line in lines[:5]:
            cleaned = line.strip()
            if cleaned and len(cleaned) > 2 and len(cleaned) < 100:
                # Check if looks like a name (capital letters)
                if sum(1 for c in cleaned if c.isupper()) >= len(cleaned) * 0.4:
                    return ExtractedField(
                        value=cleaned,
                        confidence=0.85,
                        source='first_line',
                        evidence=f"First meaningful line: {cleaned}"
                    )
        
        # Strategy 2: Pattern matching
        name_pattern = r'^([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)\s*(?:\(|,|$)'
        for line in lines[:10]:
            match = re.match(name_pattern, line.strip())
            if match:
                name = match.group(1).strip()
                return ExtractedField(
                    value=name,
                    confidence=0.95,
                    source='pattern_match',
                    evidence=f"Pattern matched: {name}"
                )
        
        return None


class EmailExtractor:
    """Extract email address with validation"""
    
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    @staticmethod
    def extract(text: str) -> Optional[ExtractedField]:
        """Extract email from text"""
        
        if not text:
            return None
        
        match = re.search(EmailExtractor.EMAIL_PATTERN, text)
        if match:
            email = match.group(0).lower()
            return ExtractedField(
                value=email,
                confidence=1.0,
                source='regex_pattern',
                evidence=f"Email pattern matched: {email}"
            )
        
        return None


class PhoneExtractor:
    """Extract phone number with regional support"""
    
    PHONE_PATTERNS = [
        r'\+84[0-9]{8,9}',  # Vietnam +84
        r'0[0-9]{8,9}',  # Vietnam 0-prefix
        r'\+1[0-9]{10}',  # US +1
        r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',  # US format
        r'\+\d{1,3}[0-9\s\-\(\)]{7,}',  # International
    ]
    
    @staticmethod
    def extract(text: str) -> Optional[ExtractedField]:
        """Extract phone number from text"""
        
        if not text:
            return None
        
        for pattern in PhoneExtractor.PHONE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                confidence = 0.95 if '+84' in phone or phone.startswith('0') else 0.85
                return ExtractedField(
                    value=phone,
                    confidence=confidence,
                    source='regex_pattern',
                    evidence=f"Phone pattern matched: {phone}"
                )
        
        return None


class SkillExtractor:
    """Extract technical and soft skills"""
    
    # Comprehensive skill dictionary
    SKILL_DICTIONARY = {
        'programming': [
            'python', 'java', 'javascript', 'typescript', 'csharp', 'c++', 'cpp', 'c#',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab',
            'perl', 'bash', 'shell', 'powershell', 'groovy', 'lua', 'dart', 'elixir',
            'clojure', 'haskell', 'erlang', 'lisp', 'scheme', 'prolog', 'cobol'
        ],
        'frameworks': [
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring',
            'nodejs', 'express', 'next.js', 'nuxt', 'laravel', 'rails', 'asp.net',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'xgboost', 'spark',
            'hadoop', 'kafka', 'rabbitmq', 'celery', 'airflow'
        ],
        'databases': [
            'mysql', 'postgresql', 'oracle', 'sql server', 'mongodb', 'cassandra',
            'redis', 'elasticsearch', 'dynamodb', 'firestore', 'mariadb', 'sqlite',
            'neo4j', 'hbase', 'couchdb', 'influxdb', 'timescaledb'
        ],
        'cloud': [
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'helm',
            'terraform', 'ansible', 'jenkins', 'gitlab', 'github', 'bitbucket',
            's3', 'ec2', 'lambda', 'ecs', 'aks', 'app service', 'cloud run'
        ],
        'devops': [
            'docker', 'kubernetes', 'jenkins', 'gitlab-ci', 'github actions', 'circleci',
            'terraform', 'ansible', 'prometheus', 'grafana', 'elk stack', 'datadog',
            'newrelic', 'splunk', 'cloudwatch', 'azure monitor'
        ],
        'soft_skills': [
            'communication', 'leadership', 'teamwork', 'project management', 'problem solving',
            'critical thinking', 'analytical', 'time management', 'public speaking',
            'negotiation', 'adaptability', 'creativity', 'attention to detail'
        ]
    }
    
    @staticmethod
    def extract(text: str) -> Optional[ExtractedField]:
        """Extract skills from text"""
        
        if not text:
            return None
        
        text_lower = text.lower()
        found_skills = []
        skill_categories = {}
        
        # Search for skills in dictionary
        for category, skills in SkillExtractor.SKILL_DICTIONARY.items():
            for skill in skills:
                if re.search(r'\b' + skill + r'\b', text_lower):
                    found_skills.append(skill)
                    if category not in skill_categories:
                        skill_categories[category] = []
                    skill_categories[category].append(skill)
        
        if found_skills:
            skill_string = ', '.join(found_skills[:15])  # Top 15 skills
            return ExtractedField(
                value=skill_string,
                confidence=0.9,
                source='skill_dictionary',
                evidence=f"Found {len(found_skills)} skills: {skill_string}"
            )
        
        return None


class JobTitleExtractor:
    """Extract job title and seniority level"""
    
    SENIORITY_LEVELS = {
        'entry': ['intern', 'junior', 'graduate', 'trainee', 'assistant'],
        'mid': ['senior', 'mid-level', 'specialist', 'engineer', 'developer'],
        'lead': ['lead', 'principal', 'staff', 'architect', 'manager', 'director', 'head'],
        'executive': ['cxo', 'ceo', 'cto', 'cfo', 'president', 'vice president']
    }
    
    JOB_TITLES = [
        'software engineer', 'senior developer', 'tech lead', 'architect',
        'product manager', 'data engineer', 'data scientist', 'ml engineer',
        'devops engineer', 'qa engineer', 'security engineer', 'cloud engineer',
        'full stack developer', 'frontend developer', 'backend developer',
        'database administrator', 'system administrator', 'network engineer'
    ]
    
    @staticmethod
    def extract(text: str) -> Optional[ExtractedField]:
        """Extract job title"""
        
        if not text:
            return None
        
        text_lower = text.lower()
        lines = text.split('\n')
        
        # Search for job titles
        for line in lines[:20]:  # Check first 20 lines
            line_lower = line.lower()
            
            for title in JobTitleExtractor.JOB_TITLES:
                if title in line_lower:
                    return ExtractedField(
                        value=title.title(),
                        confidence=0.85,
                        source='job_title_dictionary',
                        evidence=f"Found job title: {title}"
                    )
        
        return None


class LocationExtractor:
    """Extract location information"""
    
    COUNTRIES = [
        'vietnam', 'usa', 'uk', 'canada', 'australia', 'singapore', 'thailand',
        'germany', 'france', 'japan', 'india', 'china', 'south korea', 'taiwan',
        'philippines', 'malaysia', 'indonesia', 'hong kong'
    ]
    
    CITIES = [
        'hanoi', 'ho chi minh', 'saigon', 'da nang', 'hai phong', 'can tho',
        'new york', 'san francisco', 'los angeles', 'tokyo', 'london', 'paris',
        'sydney', 'toronto', 'singapore', 'bangkok', 'seoul'
    ]
    
    @staticmethod
    def extract(text: str) -> Optional[ExtractedField]:
        """Extract location"""
        
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Check for cities first
        for city in LocationExtractor.CITIES:
            if city in text_lower:
                return ExtractedField(
                    value=city.title(),
                    confidence=0.9,
                    source='location_dictionary',
                    evidence=f"Found city: {city}"
                )
        
        # Check for countries
        for country in LocationExtractor.COUNTRIES:
            if country in text_lower:
                return ExtractedField(
                    value=country.title(),
                    confidence=0.85,
                    source='location_dictionary',
                    evidence=f"Found country: {country}"
                )
        
        return None


class EnhancedRuleExtractor:
    """Coordinator for all rule-based extractors"""
    
    def __init__(self):
        self.name_extractor = NameExtractor()
        self.email_extractor = EmailExtractor()
        self.phone_extractor = PhoneExtractor()
        self.skill_extractor = SkillExtractor()
        self.job_title_extractor = JobTitleExtractor()
        self.location_extractor = LocationExtractor()
    
    def extract_contact_info(self, text: str) -> Dict[str, ExtractedField]:
        """Extract contact information"""
        
        results = {}
        
        results['name'] = self.name_extractor.extract(text)
        results['email'] = self.email_extractor.extract(text)
        results['phone'] = self.phone_extractor.extract(text)
        results['location'] = self.location_extractor.extract(text)
        
        return {k: v for k, v in results.items() if v is not None}
    
    def extract_professional_info(self, text: str) -> Dict[str, ExtractedField]:
        """Extract professional information"""
        
        results = {}
        
        results['job_title'] = self.job_title_extractor.extract(text)
        results['skills'] = self.skill_extractor.extract(text)
        
        return {k: v for k, v in results.items() if v is not None}
    
    def extract_all(self, text: str) -> Dict[str, ExtractedField]:
        """Extract all available information"""
        
        results = {}
        results.update(self.extract_contact_info(text))
        results.update(self.extract_professional_info(text))
        
        return results
