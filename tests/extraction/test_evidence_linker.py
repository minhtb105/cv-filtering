"""
Test Evidence Linking Engine - 20+ tests for citation tracking and evidence quality
"""

import pytest
from src.extraction.evidence_linker import (
    EvidenceLinker, Evidence, EvidenceType, Citation, EvidenceValidator
)


class TestCitation:
    """Tests for Citation class - 3 tests"""
    
    def test_citation_creation(self):
        """Test creating a citation"""
        citation = Citation(
            text="Senior Developer",
            line_number=5,
            start_char=100,
            end_char=118,
            similarity_score=1.0
        )
        
        assert citation.text == "Senior Developer"
        assert citation.line_number == 5
        assert citation.similarity_score == 1.0
    
    def test_citation_get_context(self):
        """Test getting context around citation"""
        cv_text = """Line 1
Line 2
Senior Developer
Line 4
Line 5"""
        
        citation = Citation(
            text="Senior Developer",
            line_number=3,
            start_char=14,
            end_char=30
        )
        
        context = citation.get_context(cv_text, context_lines=1)
        assert "Senior Developer" in context
        assert "Line 2" in context
        assert "Line 4" in context
    
    def test_citation_partial_similarity(self):
        """Test citation with partial match"""
        citation = Citation(
            text="Sr Dev",
            line_number=1,
            start_char=0,
            end_char=6,
            similarity_score=0.85
        )
        
        assert citation.similarity_score == 0.85


class TestEvidence:
    """Tests for Evidence class - 4 tests"""
    
    def test_evidence_creation(self):
        """Test creating evidence"""
        evidence = Evidence(
            field_name="position",
            field_value="Senior Developer",
            evidence_type=EvidenceType.DIRECT_MATCH,
            confidence_score=0.95
        )
        
        assert evidence.field_name == "position"
        assert evidence.field_value == "Senior Developer"
        assert evidence.confidence_score == 0.95
    
    def test_evidence_has_strong_evidence_with_multiple_citations(self):
        """Test evidence with multiple citations"""
        citations = [
            Citation(text="Senior Developer", line_number=1, start_char=0, end_char=16),
            Citation(text="Senior Dev", line_number=5, start_char=100, end_char=111)
        ]
        
        evidence = Evidence(
            field_name="position",
            field_value="Senior Developer",
            evidence_type=EvidenceType.DIRECT_MATCH,
            citations=citations,
            confidence_score=0.95
        )
        
        assert evidence.has_strong_evidence() is True
    
    def test_evidence_no_citations(self):
        """Test evidence without citations"""
        evidence = Evidence(
            field_name="position",
            field_value="Unknown",
            evidence_type=EvidenceType.INFERRED,
            citations=[],
            confidence_score=0.5
        )
        
        assert evidence.has_strong_evidence() is False
    
    def test_evidence_audit_trail(self):
        """Test generating audit trail"""
        citations = [
            Citation(text="Senior Developer", line_number=1, start_char=0, end_char=16)
        ]
        
        evidence = Evidence(
            field_name="position",
            field_value="Senior Developer",
            evidence_type=EvidenceType.DIRECT_MATCH,
            citations=citations,
            extraction_method="rule_extractor",
            confidence_score=0.95
        )
        
        audit = evidence.get_audit_trail()
        
        assert audit['field'] == "position"
        assert audit['value'] == "Senior Developer"
        assert audit['evidence_type'] == "direct_match"
        assert audit['confidence'] == 0.95


class TestEvidenceLinker:
    """Tests for EvidenceLinker class - 10+ tests"""
    
    @pytest.fixture
    def linker(self):
        """Create evidence linker instance"""
        return EvidenceLinker()
    
    @pytest.fixture
    def sample_cv(self):
        """Sample CV text"""
        return """John Developer
Email: john@example.com
Phone: +1-555-0123

Senior Developer
Tech Company ABC
January 2020 - Present

- Developed web applications
- Led team of 5 developers
- Used Python, Django, React

Skills:
Python, JavaScript, Django, React,
PostgreSQL, AWS, Docker"""
    
    def test_linker_initialization(self, linker):
        """Test linker initializes correctly"""
        assert linker.evidence_map == {}
        assert linker.cv_text == ""
    
    def test_set_cv_text(self, linker, sample_cv):
        """Test setting CV text"""
        linker.set_cv_text(sample_cv)
        assert linker.cv_text == sample_cv
    
    def test_find_citations_direct_match(self, linker, sample_cv):
        """Test finding direct citations"""
        linker.set_cv_text(sample_cv)
        
        citations = linker._find_citations("Senior Developer")
        
        assert len(citations) > 0
        assert any("Senior Developer" in c.text for c in citations)
    
    def test_find_citations_partial_match(self, linker, sample_cv):
        """Test finding partial citations"""
        linker.set_cv_text(sample_cv)
        
        citations = linker._find_citations("Developer")
        
        assert len(citations) > 0
    
    def test_find_citations_email(self, linker, sample_cv):
        """Test finding email citations"""
        linker.set_cv_text(sample_cv)
        
        citations = linker._find_citations("john@example.com")
        
        assert len(citations) > 0
        assert citations[0].similarity_score == 1.0
    
    def test_find_evidence_for_field(self, linker, sample_cv):
        """Test finding evidence for a field"""
        linker.set_cv_text(sample_cv)
        
        evidence = linker.find_evidence_for_field(
            "position",
            "Senior Developer",
            EvidenceType.DIRECT_MATCH
        )
        
        assert evidence.field_name == "position"
        assert evidence.field_value == "Senior Developer"
        assert len(evidence.citations) > 0
        assert evidence.confidence_score > 0.8
    
    def test_find_contradictions(self, linker, sample_cv):
        """Test finding contradictions"""
        linker.set_cv_text(sample_cv)
        
        # This won't find contradictions in the sample, but should not crash
        contradictions = linker.find_contradictions("position", "Junior Developer")
        
        assert isinstance(contradictions, list)
    
    def test_find_supporting_facts(self, linker, sample_cv):
        """Test finding supporting facts"""
        linker.set_cv_text(sample_cv)
        
        supporting = linker.find_supporting_facts("position", "Senior Developer")
        
        assert isinstance(supporting, list)
    
    def test_get_all_evidence(self, linker, sample_cv):
        """Test retrieving all evidence"""
        linker.set_cv_text(sample_cv)
        
        linker.find_evidence_for_field("position", "Senior Developer")
        linker.find_evidence_for_field("email", "john@example.com")
        
        all_evidence = linker.get_all_evidence()
        
        assert len(all_evidence) == 2
        assert "position" in all_evidence
        assert "email" in all_evidence
    
    def test_get_evidence_report(self, linker, sample_cv):
        """Test generating evidence report"""
        linker.set_cv_text(sample_cv)
        
        linker.find_evidence_for_field("position", "Senior Developer", EvidenceType.DIRECT_MATCH)
        linker.find_evidence_for_field("email", "john@example.com", EvidenceType.DIRECT_MATCH)
        linker.find_evidence_for_field("company", "Tech Company ABC", EvidenceType.DIRECT_MATCH)
        
        report = linker.get_evidence_report()
        
        assert 'total_fields' in report
        assert 'average_confidence' in report
        assert 'fields' in report
        assert report['total_fields'] == 3
        assert report['average_confidence'] > 0
    
    def test_calculate_similarity(self):
        """Test string similarity calculation"""
        similarity = EvidenceLinker._calculate_similarity("Developer", "Developer")
        assert similarity == 1.0
        
        # More similar strings for partial match test
        similarity = EvidenceLinker._calculate_similarity("Senior Developer", "Senior Dev")
        assert 0.0 < similarity < 1.0
    
    def test_calculate_confidence_direct_match(self):
        """Test confidence calculation for direct matches"""
        citations = [Citation(text="Test", line_number=1, start_char=0, end_char=4)]
        
        confidence = EvidenceLinker._calculate_confidence(citations, EvidenceType.DIRECT_MATCH)
        
        assert confidence >= 0.9
    
    def test_calculate_confidence_multiple_citations(self):
        """Test confidence with multiple citations"""
        citations = [
            Citation(text="Test1", line_number=1, start_char=0, end_char=5),
            Citation(text="Test2", line_number=5, start_char=50, end_char=55),
            Citation(text="Test3", line_number=10, start_char=100, end_char=105)
        ]
        
        confidence = EvidenceLinker._calculate_confidence(citations, EvidenceType.PATTERN_MATCH)
        
        assert confidence > EvidenceLinker._calculate_confidence(
            [citations[0]], EvidenceType.PATTERN_MATCH
        )


class TestEvidenceValidator:
    """Tests for EvidenceValidator class - 5 tests"""
    
    def test_is_evidence_production_ready_strong(self):
        """Test validating strong evidence"""
        citations = [
            Citation(text="Test", line_number=1, start_char=0, end_char=4),
            Citation(text="Test", line_number=5, start_char=50, end_char=54)
        ]
        
        evidence = Evidence(
            field_name="position",
            field_value="Senior Developer",
            evidence_type=EvidenceType.DIRECT_MATCH,
            citations=citations,
            confidence_score=0.95
        )
        
        assert EvidenceValidator.is_evidence_production_ready(evidence) is True
    
    def test_is_evidence_production_ready_weak_confidence(self):
        """Test validating weak confidence evidence"""
        citations = [
            Citation(text="Test", line_number=1, start_char=0, end_char=4)
        ]
        
        evidence = Evidence(
            field_name="position",
            field_value="Developer",
            evidence_type=EvidenceType.INFERRED,
            citations=citations,
            confidence_score=0.5
        )
        
        assert EvidenceValidator.is_evidence_production_ready(evidence) is False
    
    def test_is_evidence_production_ready_no_citations(self):
        """Test validating evidence without citations"""
        evidence = Evidence(
            field_name="position",
            field_value="Developer",
            evidence_type=EvidenceType.INFERRED,
            citations=[],
            confidence_score=0.95
        )
        
        assert EvidenceValidator.is_evidence_production_ready(evidence) is False
    
    def test_validate_evidence_consistency_consistent(self):
        """Test validating consistent evidence"""
        evidence_list = [
            Evidence(
                field_name="position",
                field_value="Senior Developer",
                evidence_type=EvidenceType.DIRECT_MATCH,
                confidence_score=0.95
            ),
            Evidence(
                field_name="position",
                field_value="Senior Developer",
                evidence_type=EvidenceType.PATTERN_MATCH,
                confidence_score=0.85
            )
        ]
        
        result = EvidenceValidator.validate_evidence_consistency(evidence_list)
        
        assert result['consistent'] is True
        assert len(result['conflicts']) == 0
    
    def test_validate_evidence_consistency_conflicting(self):
        """Test validating conflicting evidence"""
        evidence_list = [
            Evidence(
                field_name="position",
                field_value="Senior Developer",
                evidence_type=EvidenceType.DIRECT_MATCH,
                confidence_score=0.95
            ),
            Evidence(
                field_name="position",
                field_value="Junior Developer",
                evidence_type=EvidenceType.PATTERN_MATCH,
                confidence_score=0.85
            )
        ]
        
        result = EvidenceValidator.validate_evidence_consistency(evidence_list)
        
        assert result['consistent'] is False
        assert len(result['conflicts']) == 2


class TestEvidenceIntegration:
    """Integration tests for evidence linking - 4 tests"""
    
    def test_full_evidence_extraction_flow(self):
        """Test complete evidence extraction flow"""
        cv_text = """John Developer
Email: john@dev.com
Position: Senior Software Engineer
Company: Tech Corp
Years: 5 years

Experience:
- Lead development team
- Django, Python, AWS"""
        
        linker = EvidenceLinker()
        linker.set_cv_text(cv_text)
        
        # Extract evidence for multiple fields
        email_evidence = linker.find_evidence_for_field("email", "john@dev.com", EvidenceType.DIRECT_MATCH)
        position_evidence = linker.find_evidence_for_field("position", "Senior Software Engineer", EvidenceType.DIRECT_MATCH)
        company_evidence = linker.find_evidence_for_field("company", "Tech Corp", EvidenceType.DIRECT_MATCH)
        
        # Verify all evidence collected
        assert email_evidence.confidence_score > 0.85
        assert position_evidence.confidence_score > 0.85
        assert company_evidence.confidence_score > 0.85
    
    def test_evidence_with_vietnamese_cv(self):
        """Test evidence linking with Vietnamese CV"""
        cv_text = """Nguyễn Văn A
Email: nguyen@example.vn
Vị Trí: Kỹ Sư Phần Mềm Cấp Cao
Công Ty: ABC Technology
Kinh Nghiệm: 5 năm"""
        
        linker = EvidenceLinker()
        linker.set_cv_text(cv_text)
        
        evidence = linker.find_evidence_for_field("email", "nguyen@example.vn", EvidenceType.DIRECT_MATCH)
        
        assert len(evidence.citations) > 0
        assert evidence.confidence_score > 0.8
    
    def test_evidence_report_generation(self):
        """Test generating comprehensive evidence report"""
        cv_text = """Senior Developer
Python, Django, PostgreSQL
Tech Inc
john@example.com"""
        
        linker = EvidenceLinker()
        linker.set_cv_text(cv_text)
        
        linker.find_evidence_for_field("position", "Senior Developer")
        linker.find_evidence_for_field("email", "john@example.com")
        
        report = linker.get_evidence_report()
        
        assert report['total_fields'] == 2
        assert report['average_confidence'] > 0.5
        assert len(report['fields']) == 2
    
    def test_evidence_validator_integration(self):
        """Test evidence validator with evidence linker"""
        cv_text = "Senior Developer at Tech Corp"
        
        linker = EvidenceLinker()
        linker.set_cv_text(cv_text)
        
        evidence = linker.find_evidence_for_field("position", "Senior Developer", EvidenceType.DIRECT_MATCH)
        
        # Validate the evidence
        is_ready = EvidenceValidator.is_evidence_production_ready(evidence)
        
        assert is_ready is True
