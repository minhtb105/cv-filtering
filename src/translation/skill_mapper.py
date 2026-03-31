"""
Skill Mapper - Vietnamese to English skill translation
"""

from typing import Dict


class SkillMapper:
    """Map Vietnamese skill names to English"""

    VI_TO_EN = {
        "lập trình": "programming",
        "phát triển web": "web development",
        "phát triển phần mềm": "software development",
        "cơ sở dữ liệu": "database",
        "quản lý dự án": "project management",
        "phân tích dữ liệu": "data analysis",
        "học máy": "machine learning",
        "trí tuệ nhân tạo": "artificial intelligence",
        "điện toán đám mây": "cloud computing",
        "devops": "devops",
        "bảo mật": "security",
        "kiểm thử": "testing",
        "agile": "agile",
        "scrum": "scrum",
        "ứng dụng di động": "mobile application",
        "api": "api",
        "rest api": "rest api",
        "frontend": "frontend",
        "backend": "backend",
        "fullstack": "fullstack",
        "java": "java",
        "python": "python",
        "javascript": "javascript",
        "typescript": "typescript",
        "c++": "c++",
        "c#": "c#",
        "golang": "golang",
        "rust": "rust",
        "sql": "sql",
        "nosql": "nosql",
        "mongodb": "mongodb",
        "postgresql": "postgresql",
        "mysql": "mysql",
        "redis": "redis",
        "docker": "docker",
        "kubernetes": "kubernetes",
        "aws": "aws",
        "azure": "azure",
        "gcp": "gcp",
    }

    def __init__(self):
        self.en_to_vi: Dict[str, str] = {v: k for k, v in self.VI_TO_EN.items()}

    def to_english(self, skill: str) -> str:
        """Convert Vietnamese skill name to English"""
        skill_lower = skill.lower().strip()
        return self.VI_TO_EN.get(skill_lower, skill)

    def to_vietnamese(self, skill: str) -> str:
        """Convert English skill name to Vietnamese"""
        if not skill or not isinstance(skill, str):
           return skill if skill is not None else ""
        
        skill_lower = skill.lower().strip()
        
        return self.en_to_vi.get(skill_lower, skill)

    def is_vietnamese(self, skill: str) -> bool:
        """Check if text contains Vietnamese characters"""
        if not skill or not isinstance(skill, str):
            return skill if skill is not None else ""
        
        vietnamese_chars = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
        return any(c in skill.lower() for c in vietnamese_chars)


__all__ = ["SkillMapper"]
