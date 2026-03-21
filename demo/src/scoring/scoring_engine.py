"""
Scoring engine: Multi-factor candidate ranking
Combines rule-based, semantic, and LLM-based scoring
"""
from typing import Dict, List, Tuple
import re
import numpy as np
from dataclasses import dataclass
from functools import lru_cache
import hashlib


@dataclass
class ScoringWeights:
    """Weights for different scoring factors"""
    skill_match: float = 0.35
    experience_match: float = 0.25
    seniority: float = 0.15
    education: float = 0.10
    language_match: float = 0.10
    location_relevance: float = 0.05


class ScoringEngine:
    """Multi-factor scoring engine for candidate ranking"""
    
    def __init__(self, weights: ScoringWeights = None, cache_size: int = 1000):
        """
        Initialize scoring engine
        
        Args:
            weights: Custom scoring weights
            cache_size: Max scoring results to cache (LRU eviction)
        """
        self.weights = weights or ScoringWeights()
        self.cache_size = cache_size
        self._score_cache = {}  # Cache for scoring results
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Skill levels for better matching
        self.senior_keywords = {
            "lead", "senior", "principal", "architect", "director", 
            "manager", "head of", "chief", "staff engineer"
        }
        
        self.junior_keywords = {
            "junior", "associate", "intern", "entry", "trainee", "graduate"
        }
        
        self.common_skills = {
            # Languages
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
            "kotlin", "ruby", "php", "swift", "scala", "r", "matlab",
            # Web
            "react", "vue", "angular", "django", "flask", "fastapi", "spring",
            "nodejs", "express", "next.js", "html", "css", "webpack",
            # Data
            "sql", "mongodb", "postgresql", "mysql", "elasticsearch",
            "redis", "spark", "hadoop", "kafka", "airflow", "dbt",
            # ML
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
            "matplotlib", "nlp", "deep learning", "machine learning",
            # Cloud
            "aws", "azure", "gcp", "kubernetes", "docker", "terraform",
            # Tools
            "git", "api design", "rest", "graphql", "microservices"
        }
    
    def _get_cache_key(self, job_description: str, candidate_id: str) -> str:
        '''Generate cache key for scoring result'''
        # Hash job description and candidate ID
        combined = f'{job_description.strip()}:{candidate_id}'.encode('utf-8')
        return hashlib.md5(combined).hexdigest()
    
    def _add_to_cache(self, key: str, value: Dict):
        '''Add score to cache with LRU eviction'''
        # Remove oldest entry if cache full
        if len(self._score_cache) >= self.cache_size:
            # Simple FIFO eviction (in production, use OrderedDict for LRU)
            first_key = next(iter(self._score_cache))
            del self._score_cache[first_key]
        
        self._score_cache[key] = value
    
    def get_cache_stats(self) -> Dict[str, int]:
        '''Get cache performance statistics'''
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0
        
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate_percent': round(hit_rate, 2),
            'cached_scores': len(self._score_cache),
            'cache_capacity': self.cache_size
        }
    
    def score_candidate(self, job_description: str, 
                       candidate_profile, candidate_id: str = None) -> Dict[str, float]:
        '''
        Score a candidate for a job with caching
        
        Args:
            job_description: Job description text
            candidate_profile: StructuredProfile object
            candidate_id: Optional candidate ID for caching
            
        Returns:
            Dict with total_score and breakdown
        '''
        # Check cache if candidate_id provided
        if candidate_id:
            cache_key = self._get_cache_key(job_description, candidate_id)
            if cache_key in self._score_cache:
                self._cache_hits += 1
                return self._score_cache[cache_key]
            self._cache_misses += 1
        scores = {
            "skill_match": self._score_skills(job_description, candidate_profile),
            "experience_match": self._score_experience(job_description, candidate_profile),
            "seniority": self._score_seniority(job_description, candidate_profile),
            "education": self._score_education(candidate_profile),
            "language_match": self._score_languages(job_description, candidate_profile),
        }
        
        # Weighted sum
        total_score = (
            scores["skill_match"] * self.weights.skill_match +
            scores["experience_match"] * self.weights.experience_match +
            scores["seniority"] * self.weights.seniority +
            scores["education"] * self.weights.education +
            scores["language_match"] * self.weights.language_match
        )
        
        # Build result
        result = {
            'total_score': float(total_score),
            'skill_match': float(scores['skill_match']),
            'experience_match': float(scores['experience_match']),
            'seniority': float(scores['seniority']),
            'education': float(scores['education']),
            'language_match': float(scores['language_match']),
            'breakdown': {
                'weights': {
                    'skill_match': self.weights.skill_match,
                    'experience_match': self.weights.experience_match,
                    'seniority': self.weights.seniority,
                    'education': self.weights.education,
                    'language_match': self.weights.language_match,
                }
            }
        }
        
        # Cache result if candidate_id provided
        if candidate_id:
            self._add_to_cache(cache_key, result)
        
        return result
    
    def _score_skills(self, job_description: str, candidate_profile) -> float:
        """Score skill match (0-1)"""
        job_skills = self._extract_skills(job_description)
        candidate_skills = set(s.lower() for s in candidate_profile.skills)
        
        if not job_skills:
            return 0.5  # Neutral score if no skills found in job desc
        
        # Count matches
        matches = len(job_skills & candidate_skills)
        match_ratio = matches / len(job_skills)
        
        # Boost score if candidate has more skills
        complexity_bonus = min(len(candidate_skills) / 10, 0.15)
        
        return min(match_ratio + complexity_bonus, 1.0)
    
    def _score_experience(self, job_description: str, candidate_profile) -> float:
        """Score experience match (0-1)"""
        # Extract required years from job description
        required_years = self._extract_years(job_description)
        candidate_years = candidate_profile.years_experience
        
        if not required_years:
            # No specific requirement, score based on having any experience
            return min(candidate_years / 5.0, 1.0)
        
        # Score: how well candidate years match requirement
        if candidate_years >= required_years:
            # Over-qualified is okay, give bonus
            return min(1.0 + (candidate_years - required_years) / 10, 1.0)
        else:
            # Under-qualified - partial credit
            return candidate_years / required_years if required_years > 0 else 0.5
    
    def _score_seniority(self, job_description: str, candidate_profile) -> float:
        """Score seniority match (0-1)"""
        job_lower = job_description.lower()
        
        # Determine required seniority level
        is_senior_role = any(keyword in job_lower for keyword in ["senior", "lead", "principal", "principal"])
        is_junior_role = any(keyword in job_lower for keyword in ["junior", "entry", "graduate"])
        
        # Determine candidate seniority
        has_senior_title = any(
            keyword in exp.title.lower() 
            for exp in candidate_profile.experiences
            for keyword in self.senior_keywords
        ) if candidate_profile.experiences else False
        
        has_junior_title = any(
            keyword in exp.title.lower()
            for exp in candidate_profile.experiences
            for keyword in self.junior_keywords
        ) if candidate_profile.experiences else False
        
        # Scoring logic
        if is_senior_role:
            return 1.0 if has_senior_title else (0.6 if candidate_profile.years_experience >= 5 else 0.3)
        elif is_junior_role:
            return 1.0 if (has_junior_title or candidate_profile.years_experience < 3) else 0.7
        else:
            return 0.8  # Neutral seniority requirement
    
    def _score_education(self, candidate_profile) -> float:
        """Score education match (0-1)"""
        if not candidate_profile.education:
            return 0.5  # Neutral if no education specified
        
        degree_scores = {
            "phd": 1.0,
            "master": 0.9,
            "bachelors": 0.8,
            "diploma": 0.6,
        }
        
        max_score = 0.0
        for edu in candidate_profile.education:
            degree_lower = edu.degree.lower() if hasattr(edu, 'degree') else ''
            for degree_key, score in degree_scores.items():
                if degree_key in degree_lower:
                    max_score = max(max_score, score)
        
        return max_score if max_score > 0 else 0.5
    
    def _score_languages(self, job_description: str, candidate_profile) -> float:
        """Score language match (0-1)"""
        job_lower = job_description.lower()
        
        # Check for common job language requirements
        language_keywords = {
            "english": ["english", "fluent", "native", "c2"],
            "spanish": ["spanish", "espagnol"],
            "french": ["french", "francais"],
            "german": ["german", "deutsch"],
            "chinese": ["chinese", "mandarin", "cantonese"],
            "japanese": ["japanese"],
            "portuguese": ["portuguese"],
            "bilingual": ["bilingual", "multilingual", "bilingual"],
        }
        
        required_languages = []
        for lang, keywords in language_keywords.items():
            if any(kw in job_lower for kw in keywords):
                required_languages.append(lang)
        
        if not required_languages:
            return 0.8  # No language requirement
        
        # Check candidate languages
        candidate_langs = set(l.lower() for l in candidate_profile.languages)
        
        if "english" in required_languages:
            # English is almost always requiredfor tech jobs
            matched = 1.0 if candidate_langs else 0.5
        else:
            matches = len(set(required_languages) & candidate_langs)
            matched = matches / len(required_languages) if required_languages else 0.8
        
        return min(matched, 1.0)
    
    def _extract_skills(self, text: str) -> set:
        """Extract skills mentioned in text"""
        skills = set()
        text_lower = text.lower()
        
        for skill in self.common_skills:
            if skill in text_lower:
                skills.add(skill)
        
        return skills
    
    def _extract_years(self, text: str) -> float:
        """Extract required years of experience from text"""
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience',
            r'(?:require|need|expect).*?(\d+)\+?\s*(?:years?|yrs?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        
        return 0.0


# Test
if __name__ == "__main__":
    from models import StructuredProfile, ContactInfo, Experience
    
    # Create sample profile
    contact = ContactInfo(name="John Doe")
    exp = Experience(title="Senior Python Developer", company="TechCorp")
    profile = StructuredProfile(
        contact=contact,
        skills=["Python", "Django", "REST API", "PostgreSQL"],
        experiences=[exp],
        years_experience=5.0
    )
    
    # Test scoring
    engine = ScoringEngine()
    job_desc = """
    Senior Python Developer needed
    5+ years of experience with Python and Django
    Must have REST API design experience
    Strong SQL/PostgreSQL knowledge required
    """
    
    scores = engine.score_candidate(job_desc, profile)
    print(f"Total Score: {scores['total_score']:.2f}")
    print(f"Skill Match: {scores['skill_match']:.2f}")
    print(f"Experience Match: {scores['experience_match']:.2f}")
