"""
Task 4 Phase 2: Evidence Linking Engine
Links extracted information back to specific CV excerpts for transparency and verification
Supports audit trails and confidence scoring based on evidence quality
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """Types of evidence"""
    DIRECT_MATCH = "direct_match"  # Exact text extraction
    PATTERN_MATCH = "pattern_match"  # Regex or rule-based extraction
    INFERRED = "inferred"  # Derived from other information
    CONTEXTUAL = "contextual"  # From context surrounding text
    LLM_EXTRACTED = "llm_extracted"  # Extracted by LLM


@dataclass
class Citation:
    """A citation/reference to source text in CV"""
    text: str  # The quoted text from CV
    line_number: int  # Line number in original CV (1-indexed)
    start_char: int  # Character offset in original CV
    end_char: int  # Character offset end
    similarity_score: float = 1.0  # How closely it matches (0-1)
    
    def get_context(self, cv_text: str, context_lines: int = 1) -> str:
        """Get surrounding context from CV"""
        lines = cv_text.split('\n')
        
        if 0 <= self.line_number - 1 < len(lines):
            start_line = max(0, self.line_number - 1 - context_lines)
            end_line = min(len(lines), self.line_number + context_lines)
            return '\n'.join(lines[start_line:end_line])
        
        return self.text


@dataclass
class Evidence:
    """Evidence for an extracted field"""
    field_name: str  # e.g., 'email', 'company', 'technology'
    field_value: str  # The extracted value
    evidence_type: EvidenceType  # How it was extracted
    citations: List[Citation] = field(default_factory=list)  # Where it came from
    confidence_score: float = 0.5  # 0-1 scale
    extraction_method: str = ""  # Which extractor found it
    supporting_facts: List[str] = field(default_factory=list)  # Related information
    contradictions: List[str] = field(default_factory=list)  # Conflicting information
    
    def has_strong_evidence(self) -> bool:
        """Check if evidence is strong enough for production use"""
        if not self.citations:
            return False
        
        # Strong if: multiple citations OR high confidence + direct match
        if len(self.citations) > 1:
            return True
        
        if self.evidence_type == EvidenceType.DIRECT_MATCH and self.confidence_score >= 0.9:
            return True
        
        return False
    
    def get_audit_trail(self) -> Dict:
        """Get detailed audit trail for this evidence"""
        return {
            'field': self.field_name,
            'value': self.field_value,
            'evidence_type': self.evidence_type.value,
            'extraction_method': self.extraction_method,
            'confidence': self.confidence_score,
            'citations_count': len(self.citations),
            'has_contradictions': len(self.contradictions) > 0,
            'supporting_facts': self.supporting_facts,
            'contradictions': self.contradictions
        }


class EvidenceLinker:
    """Links extracted information back to CV source material"""
    
    def __init__(self):
        self.evidence_map: Dict[str, List[Evidence]] = {}
        self.cv_text = ""
    
    def set_cv_text(self, cv_text: str):
        """Set the original CV text for evidence extraction"""
        self.cv_text = cv_text
    
    def find_evidence_for_field(
        self,
        field_name: str,
        field_value: str,
        evidence_type: EvidenceType = EvidenceType.PATTERN_MATCH
    ) -> Evidence:
        """Find and create evidence for an extracted field"""
        
        if not self.cv_text:
            logger.warning("CV text not set for evidence linking")
            return Evidence(
                field_name=field_name,
                field_value=field_value,
                evidence_type=evidence_type,
                confidence_score=0.0
            )
        
        citations = self._find_citations(field_value)
        
        evidence = Evidence(
            field_name=field_name,
            field_value=field_value,
            evidence_type=evidence_type,
            citations=citations,
            confidence_score=self._calculate_confidence(citations, evidence_type)
        )
        
        if field_name not in self.evidence_map:
            self.evidence_map[field_name] = []
        
        self.evidence_map[field_name].append(evidence)
        
        return evidence
    
    def _find_citations(self, search_text: str, max_citations: int = 5) -> List[Citation]:
        """Find citations for a field value in the CV text"""
        
        citations = []
        
        if not search_text or len(search_text) < 2:
            return citations
        
        lines = self.cv_text.split('\n')
        search_lower = search_text.lower()
        
        for line_idx, line in enumerate(lines):
            line_lower = line.lower()
            
            # Look for direct matches
            if search_lower in line_lower:
                start_pos = line_lower.find(search_lower)
                end_pos = start_pos + len(search_text)
                
                # Calculate character offset in full text
                char_offset = sum(len(l) + 1 for l in lines[:line_idx])
                
                citation = Citation(
                    text=line[start_pos:end_pos],
                    line_number=line_idx + 1,
                    start_char=char_offset + start_pos,
                    end_char=char_offset + end_pos,
                    similarity_score=1.0
                )
                citations.append(citation)
            
            # Look for partial matches (fuzzy)
            elif len(search_text) > 5:
                partial_match = self._find_partial_match(search_lower, line_lower, search_text, line)
                if partial_match:
                    char_offset = sum(len(l) + 1 for l in lines[:line_idx])
                    citation = Citation(
                        text=partial_match['text'],
                        line_number=line_idx + 1,
                        start_char=char_offset + partial_match['start'],
                        end_char=char_offset + partial_match['end'],
                        similarity_score=partial_match['score']
                    )
                    citations.append(citation)
            
            if len(citations) >= max_citations:
                break
        
        return citations
    
    def _find_partial_match(
        self,
        search_lower: str,
        line_lower: str,
        original: str,
        line: str
    ) -> Optional[Dict]:
        """Find partial fuzzy match in line"""
        
        # Look for key words from search text
        words = search_lower.split()
        
        for word in words:
            if len(word) > 3 and word in line_lower:
                start = line_lower.find(word)
                end = start + len(word)
                
                # Expand to word boundaries
                while start > 0 and line[start-1].isalnum():
                    start -= 1
                while end < len(line) and line[end].isalnum():
                    end += 1
                
                matched_text = line[start:end]
                similarity = self._calculate_similarity(matched_text.lower(), search_lower)
                
                if similarity > 0.7:
                    return {
                        'text': matched_text,
                        'start': start,
                        'end': end,
                        'score': similarity
                    }
        
        return None
    
    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """Calculate string similarity (0-1)"""
        
        if text1 == text2:
            return 1.0
        
        # Simple overlap-based similarity
        common = sum(1 for c1, c2 in zip(text1, text2) if c1 == c2)
        return common / max(len(text1), len(text2))
    
    @staticmethod
    def _calculate_confidence(citations: List[Citation], evidence_type: EvidenceType) -> float:
        """Calculate confidence score based on citations and evidence type"""
        
        base_scores = {
            EvidenceType.DIRECT_MATCH: 0.95,
            EvidenceType.PATTERN_MATCH: 0.80,
            EvidenceType.CONTEXTUAL: 0.70,
            EvidenceType.INFERRED: 0.60,
            EvidenceType.LLM_EXTRACTED: 0.75
        }
        
        base_score = base_scores.get(evidence_type, 0.5)
        
        if not citations:
            return base_score * 0.5  # Reduce if no citations found
        
        # Boost for multiple citations
        citation_boost = min(len(citations) * 0.05, 0.15)
        
        # Average similarity of citations
        avg_similarity = sum(c.similarity_score for c in citations) / len(citations)
        
        final_score = base_score + citation_boost
        final_score = min(final_score * avg_similarity, 1.0)
        
        return round(final_score, 2)
    
    def find_contradictions(
        self,
        field_name: str,
        field_value: str
    ) -> List[str]:
        """Find contradictory information in CV"""
        
        contradictions = []
        
        lines = self.cv_text.split('\n')
        
        # Look for lines containing the field_name but different values
        for line in lines:
            line_lower = line.lower()
            
            if field_name.lower() in line_lower:
                if field_value.lower() not in line_lower:
                    contradictions.append(line.strip())
        
        return contradictions[:3]  # Limit to 3 contradictions
    
    def find_supporting_facts(
        self,
        field_name: str,
        field_value: str
    ) -> List[str]:
        """Find information that supports the extracted field"""
        
        supporting = []
        
        lines = self.cv_text.split('\n')
        
        relevant_keywords = self._get_relevant_keywords(field_name)
        
        for line in lines:
            line_lower = line.lower()
            
            # Check if line mentions relevant keywords
            for keyword in relevant_keywords:
                if keyword in line_lower and len(line.strip()) > 10:
                    supporting.append(line.strip())
                    break
        
        return supporting[:5]  # Limit to 5 supporting facts
    
    @staticmethod
    def _get_relevant_keywords(field_name: str) -> List[str]:
        """Get relevant keywords for a field"""
        
        keywords_map = {
            'email': ['email', 'contact', 'reach', '@'],
            'phone': ['phone', 'call', 'contact', 'mobile', '0', '+'],
            'company': ['company', 'at', 'worked', 'employed', 'organization'],
            'position': ['position', 'role', 'title', 'as', 'developer', 'engineer'],
            'skills': ['skills', 'expertise', 'technologies', 'proficient', 'experience'],
            'education': ['education', 'degree', 'university', 'graduated', 'bachelor'],
            'location': ['location', 'city', 'country', 'based', 'address']
        }
        
        return keywords_map.get(field_name.lower(), [])
    
    def get_all_evidence(self) -> Dict[str, List[Evidence]]:
        """Get all collected evidence"""
        return self.evidence_map
    
    def get_evidence_report(self) -> Dict:
        """Generate comprehensive evidence report"""
        
        report = {
            'total_fields': len(self.evidence_map),
            'fields_with_strong_evidence': 0,
            'average_confidence': 0.0,
            'fields': {}
        }
        
        total_confidence = 0.0
        
        for field_name, evidence_list in self.evidence_map.items():
            if not evidence_list:
                continue
            
            # Use the strongest evidence for this field
            strongest = max(evidence_list, key=lambda e: e.confidence_score)
            
            report['fields'][field_name] = {
                'value': strongest.field_value,
                'confidence': strongest.confidence_score,
                'evidence_type': strongest.evidence_type.value,
                'citations': len(strongest.citations),
                'is_strong': strongest.has_strong_evidence(),
                'audit_trail': strongest.get_audit_trail()
            }
            
            if strongest.has_strong_evidence():
                report['fields_with_strong_evidence'] += 1
            
            total_confidence += strongest.confidence_score
        
        if self.evidence_map:
            report['average_confidence'] = round(total_confidence / len(self.evidence_map), 2)
        
        return report


class EvidenceValidator:
    """Validate evidence quality and completeness"""
    
    MIN_CONFIDENCE_FOR_PRODUCTION = 0.75
    
    @staticmethod
    def is_evidence_production_ready(evidence: Evidence) -> bool:
        """Check if evidence meets production standards"""
        
        # Must have strong evidence
        if not evidence.has_strong_evidence():
            return False
        
        # Must have minimum confidence
        if evidence.confidence_score < EvidenceValidator.MIN_CONFIDENCE_FOR_PRODUCTION:
            return False
        
        # Must have citations
        if not evidence.citations:
            return False
        
        return True
    
    @staticmethod
    def validate_evidence_consistency(evidence_list: List[Evidence]) -> Dict:
        """Validate consistency across multiple evidence items"""
        
        result = {
            'consistent': True,
            'conflicts': [],
            'strength_score': 1.0
        }
        
        if len(evidence_list) < 2:
            return result
        
        # Check for conflicting values
        unique_values = set(e.field_value for e in evidence_list)
        
        if len(unique_values) > 1:
            result['consistent'] = False
            result['conflicts'] = list(unique_values)
            result['strength_score'] = 0.5
        
        # Calculate overall strength
        avg_confidence = sum(e.confidence_score for e in evidence_list) / len(evidence_list)
        result['strength_score'] = avg_confidence
        
        return result
