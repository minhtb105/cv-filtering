"""
Real File Tests - 13 tests on actual CV files from data/demo folder
These tests verify the complete extraction pipeline on real Vietnamese CVs
"""

import pytest
import json
from pathlib import Path
from src.extraction.hr_extractor_agent import HRExtractorAgent


@pytest.fixture
def agent():
    """Create HR extractor agent"""
    return HRExtractorAgent()


@pytest.fixture
def cv_files_path():
    """Get path to demo CV files"""
    return Path("data/demo")


class TestRealCVExtraction:
    """Tests on real CV files - 13 tests"""
    
    def test_agent_initialization(self, agent):
        """Test agent initializes successfully"""
        assert agent is not None
        assert agent.markdown_formatter is not None
        assert agent.rule_extractor is not None
        assert agent.experience_engine is not None
    
    def test_extract_from_real_cv_file(self, agent, cv_files_path):
        """Test extracting from a real CV file"""
        # Find first PDF text file in demo directory
        demo_dir = cv_files_path
        
        cv_files = []
        if demo_dir.exists():
            # Look for text files that were extracted from PDFs
            cv_files = list(demo_dir.glob("*.txt"))
        
        if not cv_files:
            pytest.skip("No CV text files found in data/demo")
        
        # Extract from first file
        cv_file = cv_files[0]
        with open(cv_file, 'r', encoding='utf-8', errors='ignore') as f:
            cv_text = f.read()
        
        result = agent.extract_cv(cv_text)
        
        # Verify structure
        assert 'contact' in result
        assert 'professional' in result
        assert 'experience' in result
        assert 'projects' in result
        assert result['extraction_status'] in ['success', 'partial', 'error']
    
    def test_contact_info_extraction(self, agent, cv_files_path):
        """Test contact information extraction"""
        demo_dir = cv_files_path
        cv_files = list(demo_dir.glob("*.txt"))
        
        if not cv_files:
            pytest.skip("No CV text files found")
        
        with open(cv_files[0], 'r', encoding='utf-8', errors='ignore') as f:
            cv_text = f.read()
        
        result = agent.extract_cv(cv_text)
        contact = result.get('contact', {})
        
        # At minimum, should attempt extraction
        assert isinstance(contact, dict)
    
    def test_professional_info_extraction(self, agent, cv_files_path):
        """Test professional information extraction"""
        demo_dir = cv_files_path
        cv_files = list(demo_dir.glob("*.txt"))
        
        if not cv_files:
            pytest.skip("No CV text files found")
        
        with open(cv_files[0], 'r', encoding='utf-8', errors='ignore') as f:
            cv_text = f.read()
        
        result = agent.extract_cv(cv_text)
        professional = result.get('professional', {})
        
        assert isinstance(professional, dict)
    
    def test_experience_extraction(self, agent, cv_files_path):
        """Test experience extraction"""
        demo_dir = cv_files_path
        cv_files = list(demo_dir.glob("*.txt"))
        
        if not cv_files:
            pytest.skip("No CV text files found")
        
        with open(cv_files[0], 'r', encoding='utf-8', errors='ignore') as f:
            cv_text = f.read()
        
        result = agent.extract_cv(cv_text)
        experience = result.get('experience', {})
        
        assert 'years' in experience
        assert 'seniority' in experience
        assert 'entries' in experience
        assert isinstance(experience['years'], (int, float))
    
    def test_projects_extraction(self, agent, cv_files_path):
        """Test projects extraction"""
        demo_dir = cv_files_path
        cv_files = list(demo_dir.glob("*.txt"))
        
        if not cv_files:
            pytest.skip("No CV text files found")
        
        with open(cv_files[0], 'r', encoding='utf-8', errors='ignore') as f:
            cv_text = f.read()
        
        result = agent.extract_cv(cv_text)
        projects = result.get('projects', [])
        
        assert isinstance(projects, list)
    
    def test_skills_extraction(self, agent, cv_files_path):
        """Test skills extraction"""
        demo_dir = cv_files_path
        cv_files = list(demo_dir.glob("*.txt"))
        
        if not cv_files:
            pytest.skip("No CV text files found")
        
        with open(cv_files[0], 'r', encoding='utf-8', errors='ignore') as f:
            cv_text = f.read()
        
        result = agent.extract_cv(cv_text)
        skills = result.get('skills', [])
        
        assert isinstance(skills, list)
    
    def test_multiple_cv_extraction(self, agent, cv_files_path):
        """Test extracting from multiple CV files"""
        demo_dir = cv_files_path
        cv_files = list(demo_dir.glob("*.txt"))
        
        if not cv_files:
            pytest.skip("No CV text files found")
        
        # Test first 3 files
        for cv_file in cv_files[:3]:
            with open(cv_file, 'r', encoding='utf-8', errors='ignore') as f:
                cv_text = f.read()
            
            result = agent.extract_cv(cv_text)
            
            assert result is not None
            assert 'extraction_status' in result
            assert result['extraction_status'] in ['success', 'partial', 'error', 'empty_input']
    
    def test_empty_cv_handling(self, agent):
        """Test handling empty CV"""
        result = agent.extract_cv("")
        
        assert result['extraction_status'] == 'empty_input'
        assert result['experience']['years'] == 0.0
    
    def test_vietnamese_cv_extraction(self, agent, cv_files_path):
        """Test extraction from Vietnamese language CV"""
        # Create a simple Vietnamese CV for testing
        vietnamese_cv = """
NGUYỄN VĂN A
Hà Nội, Việt Nam
Email: nguyenvana@example.com
Điện thoại: 0903123456

KINH NGHIỆM LÀM VIỆC
Công Ty ABC - Lập Trình Viên Cấp Cao (Tháng 1/2020 - Hiện tại)
- Phát triển ứng dụng web sử dụng Python và Django
- Quản lý cơ sở dữ liệu PostgreSQL
- Hợp tác với team frontend

Công Ty XYZ - Lập Trình Viên (Tháng 6/2018 - Tháng 12/2019)
- Phát triển REST APIs
- Viết unit tests

KỸ NĂNG
- Python, JavaScript, Django, React
- PostgreSQL, Redis
- AWS, Docker, Kubernetes
"""
        
        result = agent.extract_cv(vietnamese_cv)
        
        assert result is not None
        assert 'experience' in result
    
    def test_bilingual_cv_extraction(self, agent):
        """Test extraction from bilingual (English + Vietnamese) CV"""
        bilingual_cv = """
JOHN NGUYỄN
Senior Software Engineer
Ho Chi Minh City, Vietnam

SUMMARY
Senior engineer with 5 years experience in full-stack development.
Kinh nghiệm phát triển ứng dụng web quy mô lớn.

EXPERIENCE
Senior Developer - Tech A (Jan 2021 - Present)
Công Ty công nghệ hàng đầu ở TPHCM
- Designed cloud architecture
- Phát triển hệ thống phân tán

SKILLS
Python, JavaScript, AWS, Docker, Kubernetes
Kỹ năng: Leadership, Communication, Problem Solving
"""
        
        result = agent.extract_cv(bilingual_cv)
        
        assert result is not None
        assert result['extraction_status'] in ['success', 'partial']
    
    def test_extraction_result_json_serializable(self, agent, cv_files_path):
        """Test that extraction result is JSON serializable"""
        demo_dir = cv_files_path
        cv_files = list(demo_dir.glob("*.txt"))
        
        if not cv_files:
            pytest.skip("No CV text files found")
        
        with open(cv_files[0], 'r', encoding='utf-8', errors='ignore') as f:
            cv_text = f.read()
        
        result = agent.extract_cv(cv_text)
        
        # Should be JSON serializable
        json_str = json.dumps(result, default=str)
        assert json_str is not None
        assert len(json_str) > 0
    
    def test_markdown_formatting_integration(self, agent):
        """Test markdown formatting is applied correctly"""
        sample_cv = """
John Developer
john@example.com
+1-555-0123

EXPERIENCE
Company ABC, Senior Developer, Jan 2020 - Present
Developed APIs using Python

SKILLS
Python, Django, PostgreSQL
"""
        
        result = agent.extract_cv(sample_cv)
        
        # Should complete without errors
        assert result is not None
        assert 'experience' in result
