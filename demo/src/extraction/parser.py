"""
CV extraction module: Parse raw text into structured data
Uses spaCy NER + rule-based extraction
"""
import re
from typing import List, Optional
import spacy


class CVExtractor:
    """Extract structured information from CV text"""
    
    # Common skill keywords (expandable)
    SKILL_KEYWORDS = {
        # Programming
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "kotlin",
        "ruby", "php", "swift", "scala", "r", "matlab", "perl", "groovy",
        # Web
        "html", "css", "react", "vue", "angular", "django", "flask", "fastapi",
        "spring", "nodejs", "express", "next.js", "webpack", "babel",
        # Data
        "sql", "mongodb", "postgresql", "mysql", "elasticsearch", "redis",
        "spark", "hadoop", "kafka", "airflow", "dbt",
        # ML
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib",
        "nlp", "computer vision", "deep learning", "machine learning",
        # Cloud
        "aws", "azure", "gcp", "kubernetes", "docker", "terraform",
        # Tools
        "git", "api design", "rest", "graphql", "microservices", "agile",
        "scrum", "jira", "linux", "windows", "macos"
    }
    
    # Experience keywords for years extraction
    EXPERIENCE_PATTERNS = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
        r"(?:experience|exp).*?(\d+)\+?\s*(?:years?|yrs?)",
    ]
    
    def __init__(self):
        """Initialize spaCy model (optional for MVP)"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.has_nlp = True
        except OSError:
            print("⚠️  spaCy model not found. Running in lightweight mode (no NER).")
            print("   To use full NER, run: python -m spacy download en_core_web_sm")
            self.nlp = None
            self.has_nlp = False
    
    def extract_all(self, raw_text: str) -> dict:
        """Extract all structured data from CV text"""
        return {
            "contact": self.extract_contact_info(raw_text),
            "summary": self.extract_summary(raw_text),
            "skills": self.extract_skills(raw_text),
            "experiences": self.extract_experiences(raw_text),
            "education": self.extract_education(raw_text),
            "languages": self.extract_languages(raw_text),
            "years_experience": self.extract_years_experience(raw_text),
        }
    
    def extract_contact_info(self, text: str) -> dict:
        """Extract name, email, phone using regex + NER"""
        result = {
            "name": None,
            "email": None,
            "phone": None,
            "location": None,
            "linkedin": None
        }
        
        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            result["email"] = email_match.group(0)
        
        # Phone (basic patterns)
        phone_match = re.search(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if phone_match:
            result["phone"] = phone_match.group(0)
        
        # LinkedIn
        linkedin_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', text, re.IGNORECASE)
        if linkedin_match:
            result["linkedin"] = linkedin_match.group(0)
        
        # Name (first occurrence of PERSON entity from spaCy, if available)
        if self.has_nlp:
            doc = self.nlp(text[:1000])  # Use first 1000 chars for efficiency
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    result["name"] = ent.text
                    break
            
            # Location (look for GPE entities)
            for ent in doc.ents:
                if ent.label_ == "GPE":
                    result["location"] = ent.text
                    break
        else:
            # Fallback: extract first capitalized phrase
            cap_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+[A-Z][a-z]+)?\b', text[:200])
            if cap_words:
                result["name"] = cap_words[0]
        
        return result
    
    def extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary/objective"""
        # Look for common section headers
        patterns = [
            r"(?:professional\s+)?summary[:\s]+([^\n]{20,200})",
            r"objective[:\s]+([^\n]{20,200})",
            r"profile[:\s]+([^\n]{20,200})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills using keyword matching"""
        text_lower = text.lower()
        found_skills = set()
        
        # Keyword-based extraction
        for keyword in self.SKILL_KEYWORDS:
            if keyword in text_lower:
                found_skills.add(keyword.title())
        
        # Look for skills section and extract
        skills_match = re.search(
            r"(?:skills|technical skills|competencies)[:\s]+([^\n]{30,300})",
            text,
            re.IGNORECASE
        )
        if skills_match:
            skills_text = skills_match.group(1)
            # Split by common delimiters
            for skill in re.split(r'[,;•\n]', skills_text):
                skill = skill.strip()
                if len(skill) > 1 and len(skill) < 50:
                    found_skills.add(skill)
        
        return sorted(list(found_skills))[:30]  # Limit to 30 unique skills
    
    def extract_experiences(self, text: str) -> List[dict]:
        """Extract work experiences"""
        experiences = []
        
        # Simplified: Look for job title patterns
        job_patterns = [
            r"(?:^|\n)\s*([A-Z][A-Za-z\s]+(?:Engineer|Manager|Doctor|Developer|Analyst|Specialist|Officer|Coordinator|Architect|Lead|Director|Head|Chief))\s+(?:at|@|for|in)\s+([A-Z][A-Za-z\s&]+)",
        ]
        
        for pattern in job_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                title, company = match.groups()
                experiences.append({
                    "title": title.strip()[:50],
                    "company": company.strip()[:50],
                    "duration": None,
                    "start_date": None,
                    "end_date": None,
                    "description": None
                })
        
        return experiences[:10]  # Limit to 10 experiences
    
    def extract_education(self, text: str) -> List[dict]:
        """Extract education information"""
        education = []
        
        # Degree patterns
        degree_patterns = [
            (r"(?:bachelor|b\.s\.|b\.a\.|bsc|ba)", "Bachelor"),
            (r"(?:master|m\.s\.|m\.a\.|msc|ma)", "Master"),
            (r"(?:phd|doctorate)", "PhD"),
            (r"(?:high school|secondary|diploma)", "Diploma"),
        ]
        
        for pattern, degree_type in degree_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                education.append({
                    "degree": degree_type,
                    "field": "Unspecified",
                    "institution": "Unspecified",
                    "graduation_date": None
                })
        
        return education[:5]  # Limit to 5 education entries
    
    def extract_languages(self, text: str) -> List[str]:
        """Extract spoken languages"""
        languages = []
        language_keywords = {
            "english", "spanish", "french", "german", "chinese", "japanese",
            "korean", "portuguese", "italian", "russian", "hindi", "arabic",
            "vietnamese", "thai", "turkish", "polish", "dutch", "swedish"
        }
        
        text_lower = text.lower()
        for lang in language_keywords:
            if lang in text_lower:
                languages.append(lang.title())
        
        return languages
    
    def extract_years_experience(self, text: str) -> float:
        """Extract years of experience"""
        for pattern in self.EXPERIENCE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        
        return 0.0
    
    def clean_text(self, text: str) -> str:
        """Normalize and clean extracted text"""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep some punctuation
        text = re.sub(r'[^\w\s.,!?()@-]', '', text)
        return text.strip()


# Test
if __name__ == "__main__":
    extractor = CVExtractor()
    sample_text = """
    John Doe
    john.doe@email.com | (555) 123-4567 | linkedin.com/in/johndoe
    
    Professional Summary
    Experienced software engineer with 5 years of experience in Python, JavaScript, and cloud technologies.
    
    Technical Skills
    - Languages: Python, JavaScript, Java, C++
    - Frameworks: Django, React, Spring
    - Databases: PostgreSQL, MongoDB, Redis
    - Tools: Git, Docker, Kubernetes, AWS
    
    Work Experience
    Senior Software Engineer at TechCorp (2020-2023)
    - Led development of microservices architecture
    - Managed team of 5 engineers
    
    Education
    Bachelor of Science in Computer Science
    State University (2018)
    
    Languages: English, Spanish
    """
    
    result = extractor.extract_all(sample_text)
    import json
    print(json.dumps(result, indent=2))
