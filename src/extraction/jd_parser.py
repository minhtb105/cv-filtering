"""
JD Parser — Job Description Parsing

Mirror của CV pipeline nhưng đơn giản hơn nhiều.
JD thường ngắn hơn, cấu trúc rõ ràng hơn CV.

Flow:
  raw JD text / PDF → LLM extraction → JobRequirements schema → scoring

Lý do tách JD parser riêng:
  - JD schema khác CV schema (required/preferred skills, experience range)
  - JD thường là text thuần, không cần geometric extraction
  - JD cần extract skill importance (required vs preferred)
  - JD ít thay đổi hơn CV → cache dài hơn
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class JobRequirements:
    """
    Structured output từ JD parsing.
    
    Thiết kế: tách required vs preferred skills vì chúng có weight khác nhau
    trong matching engine. Missing required skill → penalize mạnh.
    Missing preferred skill → penalize nhẹ.
    """
    jd_id: Optional[str] = None
    title: str = ""
    company: str = ""
    
    # Skills (phần quan trọng nhất)
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    
    # Experience requirements
    min_experience_years: float = 0.0
    max_experience_years: Optional[float] = None  # None = không giới hạn
    required_seniority: str = "mid"  # junior/mid/senior/lead
    
    # Education
    required_degree: str = ""  # bachelor/master/phd
    
    # Other requirements
    required_languages: List[str] = field(default_factory=list)
    location: str = ""
    remote_eligible: bool = False
    
    # Context
    description_summary: str = ""
    responsibilities: List[str] = field(default_factory=list)
    
    # Metadata
    extraction_confidence: float = 0.7
    extraction_method: str = "llm"
    
    def to_scoring_dict(self) -> Dict[str, Any]:
        """Convert sang format dùng cho CompositeScorer."""
        return {
            "title": self.title,
            "skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "min_experience_years": self.min_experience_years,
            "required_seniority": self.required_seniority,
            "required_degree": self.required_degree,
            "required_languages": self.required_languages,
        }
    
    def skill_set(self) -> set:
        """Toàn bộ skills (required + preferred)."""
        return set(s.lower() for s in self.required_skills + self.preferred_skills)
    
    def jaccard_similarity(self, other: "JobRequirements") -> float:
        """
        Tính Jaccard similarity giữa 2 JD.
        Dùng để detect JD có thay đổi nhiều không.
        
        Returns: float [0, 1] — 1.0 = identical, 0.0 = hoàn toàn khác
        """
        set_a = self.skill_set()
        set_b = other.skill_set()
        
        if not set_a and not set_b:
            return 1.0
        if not set_a or not set_b:
            return 0.0
        
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union


class JDParser:
    """
    Job Description parser.
    
    Strategy:
    1. LLM extraction (primary) — Qwen2.5 qua Ollama
    2. Regex fallback — catch common patterns nếu LLM fail
    
    Không cần geometric extraction vì JD thường là text thuần
    (HTML, Word, plain text) không phải scanned PDF.
    """
    
    EXTRACTION_PROMPT = """Extract structured information from this Job Description.
Return ONLY valid JSON, no explanations.

{{
    "title": "Job title",
    "company": "Company name",
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill3", "skill4"],
    "min_experience_years": 3,
    "max_experience_years": 7,
    "required_seniority": "mid|senior|junior|lead",
    "required_degree": "bachelor|master|phd|none",
    "required_languages": ["English", "Vietnamese"],
    "location": "City, Country",
    "remote_eligible": true,
    "description_summary": "2-3 sentence summary",
    "responsibilities": ["responsibility 1", "responsibility 2"]
}}

RULES:
- required_skills: skills explicitly marked as "required", "must have", "mandatory"
- preferred_skills: "nice to have", "preferred", "bonus"  
- If unclear, put in required_skills
- Normalize skill names to English (e.g., "lập trình Python" → "Python")
- min_experience_years: extract từ "X years of experience" patterns
- required_seniority: infer từ title và requirements nếu không explicit
- Return null cho fields không có trong JD

JOB DESCRIPTION:
{jd_text}"""

    # Regex patterns cho fallback extraction
    _SKILL_SECTION_PATTERNS = [
        r'(?:required|must.have|mandatory)[:\s]+([^\n]+(?:\n[-•*][^\n]+)*)',
        r'(?:requirements?|qualifications?)[:\s]*\n((?:[-•*][^\n]+\n?)+)',
        r'(?:skills?)[:\s]+([^\n]+(?:\n[-•*][^\n]+)*)',
    ]
    
    _EXP_PATTERNS = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
        r'minimum\s*(\d+)\s*(?:years?|yrs?)',
        r'at least\s*(\d+)\s*(?:years?|yrs?)',
        r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)',
    ]
    
    _DEGREE_MAP = {
        'phd': 'phd', 'doctorate': 'phd',
        'master': 'master', "master's": 'master', 'm.s': 'master', 'mba': 'master',
        'bachelor': 'bachelor', "bachelor's": 'bachelor', 'b.s': 'bachelor', 'b.e': 'bachelor',
        'associate': 'associate',
    }
    
    COMMON_TECH_SKILLS = {
        # Languages
        'python', 'java', 'javascript', 'typescript', 'go', 'golang', 'rust', 'c++',
        'c#', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r',
        # Frameworks
        'react', 'vue', 'angular', 'django', 'flask', 'fastapi', 'spring', 'node.js',
        'express', 'nestjs', 'laravel', 'rails',
        # Databases
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
        # DevOps
        'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins', 'ci/cd',
        'aws', 'gcp', 'azure', 'linux',
        # Data
        'sql', 'spark', 'kafka', 'airflow', 'pandas', 'numpy', 'tensorflow', 'pytorch',
        # Tools
        'git', 'github', 'gitlab', 'jira', 'figma',
        # Methodologies
        'agile', 'scrum', 'kanban', 'tdd', 'bdd', 'microservices', 'rest', 'graphql',
    }

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5-coder:3b-instruct-q4_K_M",
        timeout: int = 30,
    ):
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.ollama_model = ollama_model
        self.timeout = timeout
        self._ollama_available: Optional[bool] = None
    
    def _check_ollama(self) -> bool:
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            import requests
            r = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            self._ollama_available = r.status_code == 200
        except Exception:
            self._ollama_available = False
        return self._ollama_available
    
    def parse(self, jd_text: str, jd_id: Optional[str] = None) -> JobRequirements:
        """
        Parse JD text → JobRequirements.
        
        Args:
            jd_text: Raw JD text (HTML, plain text, or extracted PDF text)
            jd_id: Optional ID để track
            
        Returns:
            JobRequirements với tất cả fields đã extract
        """
        # Clean HTML tags nếu có
        clean_text = self._clean_html(jd_text)
        
        # Thử LLM trước
        if self._check_ollama():
            result = self._extract_with_llm(clean_text)
            if result:
                result.jd_id = jd_id
                result.extraction_method = "llm"
                return result
        
        # Fallback: regex
        logger.warning("LLM unavailable or failed, using regex fallback for JD parsing")
        result = self._extract_with_regex(clean_text)
        result.jd_id = jd_id
        result.extraction_method = "regex"
        return result
    
    def _extract_with_llm(self, jd_text: str) -> Optional[JobRequirements]:
        """Extract JD info via LLM."""
        try:
            import requests
            prompt = self.EXTRACTION_PROMPT.format(jd_text=jd_text[:4000])
            
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1,
                "format": "json",
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            
            if response.status_code != 200:
                return None
            
            raw = response.json().get("response", "")
            
            # Parse JSON
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                # Try to find JSON block
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if not match:
                    return None
                data = json.loads(match.group())
            
            return self._dict_to_requirements(data)
            
        except Exception as e:
            logger.error(f"LLM JD extraction failed: {e}")
            return None
    
    def _dict_to_requirements(self, data: Dict[str, Any]) -> JobRequirements:
        """Convert raw LLM dict output → JobRequirements."""
        # Normalize skills: lowercase, deduplicate
        required = list({s.lower().strip() for s in (data.get("required_skills") or []) if s})
        preferred = list({s.lower().strip() for s in (data.get("preferred_skills") or []) if s})
        
        # Remove skills from preferred nếu đã có trong required
        preferred = [s for s in preferred if s not in set(required)]
        
        # Extract experience
        min_exp = 0.0
        max_exp = None
        exp_raw = data.get("min_experience_years")
        if exp_raw is not None:
            try:
                min_exp = float(exp_raw)
            except (ValueError, TypeError):
                pass
        
        exp_max_raw = data.get("max_experience_years")
        if exp_max_raw is not None:
            try:
                max_exp = float(exp_max_raw)
            except (ValueError, TypeError):
                pass
        
        # Normalize seniority
        seniority = str(data.get("required_seniority") or "mid").lower()
        if seniority not in ("junior", "mid", "senior", "lead", "principal"):
            seniority = self._infer_seniority(min_exp, data.get("title", ""))
        
        # Normalize degree
        degree_raw = str(data.get("required_degree") or "").lower()
        degree = self._normalize_degree(degree_raw)
        
        return JobRequirements(
            title=data.get("title") or "",
            company=data.get("company") or "",
            required_skills=required,
            preferred_skills=preferred,
            min_experience_years=min_exp,
            max_experience_years=max_exp,
            required_seniority=seniority,
            required_degree=degree,
            required_languages=[l for l in (data.get("required_languages") or []) if l],
            location=data.get("location") or "",
            remote_eligible=bool(data.get("remote_eligible", False)),
            description_summary=data.get("description_summary") or "",
            responsibilities=[r for r in (data.get("responsibilities") or []) if r],
            extraction_confidence=0.85,
        )
    
    def _extract_with_regex(self, jd_text: str) -> JobRequirements:
        """
        Regex-based fallback extraction.
        Không chính xác bằng LLM nhưng đủ dùng cho basic matching.
        """
        text_lower = jd_text.lower()
        
        # Extract skills bằng cách tìm các tech keywords trong text
        found_skills = []
        for skill in self.COMMON_TECH_SKILLS:
            # Word boundary check
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        # Extract experience
        min_exp = 0.0
        for pattern in self._EXP_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    min_exp = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    pass
        
        # Extract title (thường ở đầu)
        title = ""
        first_line = jd_text.strip().split('\n')[0].strip()
        if len(first_line) < 100:  # Likely a title
            title = first_line
        
        # Extract degree
        degree = ""  # default
        for keyword, normalized in self._DEGREE_MAP.items():
            if keyword in text_lower:
                degree = normalized
                break
        
        # Extract seniority
        seniority = self._infer_seniority(min_exp, title)
        
        # Remote check
        remote = any(kw in text_lower for kw in ["remote", "work from home", "wfh", "anywhere"])
        
        return JobRequirements(
            title=title,
            required_skills=found_skills,
            preferred_skills=[],
            min_experience_years=min_exp,
            required_seniority=seniority,
            required_degree=degree,
            remote_eligible=remote,
            extraction_confidence=0.5,
        )
    
    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove HTML tags."""
        clean = re.sub(r'<[^>]+>', ' ', text)
        clean = re.sub(r'&[a-zA-Z]+;', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    @staticmethod
    def _normalize_degree(degree_raw: str) -> str:
        if not degree_raw:
            return ""
        for key, val in JDParser._DEGREE_MAP.items():
            if key in degree_raw:
                return val
            
        return ""
    
    @staticmethod
    def _infer_seniority(min_exp: float, title: str) -> str:
        """Infer seniority từ exp years và title."""
        title_lower = title.lower()
        
        # Title-based
        if any(kw in title_lower for kw in ["lead", "head", "principal", "director", "manager"]):
            return "lead"
        if any(kw in title_lower for kw in ["senior", "sr.", "sr "]):
            return "senior"
        if any(kw in title_lower for kw in ["junior", "jr.", "jr ", "intern", "fresher"]):
            return "junior"
        
        # Experience-based fallback
        if min_exp >= 8:
            return "lead"
        elif min_exp >= 5:
            return "senior"
        elif min_exp >= 2:
            return "mid"
        else:
            return "junior"
    


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def parse_jd(
    jd_text: str,
    jd_id: Optional[str] = None,
    use_llm: bool = True,
) -> JobRequirements:
    """Quick parse JD từ text."""
    parser = JDParser()
    if not use_llm:
        parser._ollama_available = False
    return parser.parse(jd_text, jd_id=jd_id)
