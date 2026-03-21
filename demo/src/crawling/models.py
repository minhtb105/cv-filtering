"""
Data models for Job Description Crawler

Defines structured data classes for consistent job description extraction
across different job board sources.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class JobDescription:
    """
    Standardized job description data model
    
    Provides consistent structure for job data extracted from various sources.
    Includes both required and nice-to-have skills for intelligent CV matching.
    """
    
    # Core identification fields
    title: str
    company: str
    location: str
    category: str  # Maps to one of the 24 CV categories
    
    # Job details
    job_type: str  # Full-time, Part-time, Contract, Internship, etc.
    experience_level: str  # Entry, Mid, Senior, Lead, etc.
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "VND"
    
    # Content fields
    description: str
    requirements: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    
    # Skills classification
    skills_required: List[str] = field(default_factory=list)  # Must-have skills
    skills_nice_to_have: List[str] = field(default_factory=list)  # Good-to-have skills
    
    # Metadata
    source: str  # Job board source (VietnamWorks, CareerBuilder, etc.)
    url: str
    posted_date: Optional[datetime] = None
    crawled_at: datetime = field(default_factory=datetime.now)
    
    # Source-specific raw data for debugging/extension
    source_specific: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export and API responses"""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "category": self.category,
            "job_type": self.job_type,
            "experience_level": self.experience_level,
            "salary": {
                "min": self.salary_min,
                "max": self.salary_max,
                "currency": self.currency
            },
            "description": self.description,
            "requirements": self.requirements,
            "benefits": self.benefits,
            "skills": {
                "required": self.skills_required,
                "nice_to_have": self.skills_nice_to_have
            },
            "source": self.source,
            "url": self.url,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "crawled_at": self.crawled_at.isoformat(),
            "source_specific": self.source_specific
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def get_all_skills(self) -> List[str]:
        """Get combined list of required and nice-to-have skills"""
        return self.skills_required + self.skills_nice_to_have
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobDescription':
        """Create JobDescription from dictionary"""
        # Handle datetime conversion
        posted_date = None
        if data.get('posted_date'):
            posted_date = datetime.fromisoformat(data['posted_date'])
        
        crawled_at = datetime.now()
        if data.get('crawled_at'):
            crawled_at = datetime.fromisoformat(data['crawled_at'])
        
        return cls(
            title=data['title'],
            company=data['company'],
            location=data['location'],
            category=data['category'],
            job_type=data['job_type'],
            experience_level=data['experience_level'],
            salary_min=data.get('salary', {}).get('min'),
            salary_max=data.get('salary', {}).get('max'),
            currency=data.get('salary', {}).get('currency', 'VND'),
            description=data['description'],
            requirements=data.get('requirements', []),
            benefits=data.get('benefits', []),
            skills_required=data.get('skills', {}).get('required', []),
            skills_nice_to_have=data.get('skills', {}).get('nice_to_have', []),
            source=data['source'],
            url=data['url'],
            posted_date=posted_date,
            crawled_at=crawled_at,
            source_specific=data.get('source_specific', {})
        )


# Category mapping for the 24 CV categories
CATEGORY_MAPPING = {
    "ACCOUNTANT": [
        "Kế toán", "Accountant", "Accounting", "Finance", "Tài chính", 
        "Kiểm toán", "Audit", "Financial", "Bookkeeping"
    ],
    "ADVOCATE": [
        "Luật sư", "Legal", "Lawyer", "Advocate", "Tư vấn pháp luật", 
        "Pháp lý", "Legal Counsel", "Legal Advisor"
    ],
    "AGRICULTURE": [
        "Nông nghiệp", "Agriculture", "Farm", "Nông trại", "Plant", 
        "Crop", "Agronomy", "Agribusiness"
    ],
    "APPAREL": [
        "Thời trang", "Apparel", "Fashion", "May mặc", "Garment", 
        "Textile", "Dệt may", "Clothing"
    ],
    "ARTS": [
        "Nghệ thuật", "Arts", "Art", "Creative", "Design", 
        "Graphic", "Illustration", "Painting"
    ],
    "AUTOMOBILE": [
        "Ô tô", "Automobile", "Car", "Vehicle", "Auto", 
        "Mechanic", "Automotive", "Xe hơi"
    ],
    "AVIATION": [
        "Hàng không", "Aviation", "Airlines", "Pilot", "Flight", 
        "Airport", "Aircraft", "Cơ khí hàng không"
    ],
    "BANKING": [
        "Ngân hàng", "Banking", "Bank", "Finance", "Tài chính", 
        "Credit", "Loan", "Giao dịch viên"
    ],
    "BPO": [
        "BPO", "Outsourcing", "Call Center", "Customer Service", 
        "Chăm sóc khách hàng", "Telesales", "Support"
    ],
    "BUSINESS-DEVELOPMENT": [
        "Phát triển kinh doanh", "Business Development", "BD", 
        "Kinh doanh", "Business", "Sales", "Partnership"
    ],
    "CHEF": [
        "Đầu bếp", "Chef", "Cook", "Cooking", "Ẩm thực", 
        "Cuisine", "Restaurant", "Kitchen"
    ],
    "CONSTRUCTION": [
        "Xây dựng", "Construction", "Building", "Architecture", 
        "Engineering", "Site Manager", "Project Manager"
    ],
    "CONSULTANT": [
        "Tư vấn", "Consultant", "Consulting", "Advisor", 
        "Strategy", "Management", "Business Consultant"
    ],
    "DESIGNER": [
        "Thiết kế", "Designer", "Design", "Graphic Design", 
        "UI/UX", "Creative", "Art Director"
    ],
    "DIGITAL-MEDIA": [
        "Truyền thông số", "Digital Media", "Social Media", 
        "Content", "Marketing", "Online", "Digital Marketing"
    ],
    "ENGINEERING": [
        "Kỹ sư", "Engineer", "Engineering", "Technical", 
        "Mechanical", "Electrical", "Civil", "Software Engineer"
    ],
    "FINANCE": [
        "Tài chính", "Finance", "Financial", "Investment", 
        "Budget", "Accounting", "Analyst", "Financial Planning"
    ],
    "FITNESS": [
        "Thể dục", "Fitness", "Gym", "Trainer", "Personal Trainer", 
        "Health", "Wellness", "Exercise"
    ],
    "HEALTHCARE": [
        "Y tế", "Healthcare", "Medical", "Hospital", "Clinic", 
        "Nurse", "Doctor", "Health"
    ],
    "HR": [
        "Nhân sự", "HR", "Human Resources", "Recruitment", 
        "Tuyển dụng", "Personnel", "Talent Acquisition"
    ],
    "INFORMATION-TECHNOLOGY": [
        "Công nghệ thông tin", "IT", "Information Technology", 
        "Software", "Developer", "Programmer", "Lập trình", "DevOps"
    ],
    "PUBLIC-RELATIONS": [
        "Quan hệ công chúng", "PR", "Public Relations", 
        "Communications", "Media", "Corporate Communications"
    ],
    "SALES": [
        "Bán hàng", "Sales", "Kinh doanh", "Business Development", 
        "Account Manager", "Sales Executive", "Business"
    ],
    "TEACHER": [
        "Giáo viên", "Teacher", "Educator", "Instructor", 
        "Lecturer", "Trainer", "Education", "Teaching"
    ]
}


def get_category_keywords(category: str) -> List[str]:
    """Get search keywords for a given category"""
    return CATEGORY_MAPPING.get(category, [])


def normalize_category(job_title: str, description: str = "") -> str:
    """Auto-detect category from job title and description"""
    text = f"{job_title} {description}".lower()
    
    for category, keywords in CATEGORY_MAPPING.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return category
    
    return "OTHER"  # Default category for unmatched jobs


class JobSearchQuery:
    """Represents a search query for job crawling"""
    
    def __init__(self, category: str, location: str = "Vietnam", limit: int = 50):
        self.category = category
        self.location = location
        self.limit = limit
        self.keywords = get_category_keywords(category)
    
    def get_search_terms(self) -> List[str]:
        """Get search terms for this category"""
        return self.keywords[:3]  # Use top 3 keywords to avoid too many variations
    
    def __str__(self) -> str:
        return f"JobSearchQuery(category={self.category}, location={self.location}, limit={self.limit})"