"""
Enumerations for CV Intelligence Platform

Comprehensive set of enums for type safety and validation across the platform.
"""

from enum import Enum
from typing import Literal


class CEFRLEVEL(str, Enum):
    """Common European Framework of Reference Language Levels"""
    A1 = "A1"  # Beginner
    A2 = "A2"  # Elementary
    B1 = "B1"  # Intermediate
    B2 = "B2"  # Upper-intermediate
    C1 = "C1"  # Advanced
    C2 = "C2"  # Mastery
    NATIVE = "NATIVE"  # Native speaker
    FLUENT = "FLUENT"  # Fluent (maps to C1-C2)


class SeniorityLevel(str, Enum):
    """Candidate/Role seniority levels"""
    JUNIOR = "junior"  # 0-2 years
    MID = "mid"  # 2-5 years
    SENIOR = "senior"  # 5-10 years
    LEAD = "lead"  # 10-15 years
    PRINCIPAL = "principal"  # 15+ years


class ExtractionMethod(str, Enum):
    """PDF extraction method"""
    PYMUPDF = "pymupdf"
    PDFPLUMBER = "pdfplumber"
    OCR = "ocr"
    MANUAL = "manual"


class RiskFlagType(str, Enum):
    """Types of risk flags"""
    WEAK_EVIDENCE = "weak_evidence"
    NO_METRICS = "no_metrics"
    TIMELINE_GAP = "timeline_gap"
    INCONSISTENCY = "inconsistency"
    OVERSTATEMENT = "overstatement"
    MISSING_REQUIRED_SKILL = "missing_required_skill"
    MISSING_EXPERIENCE = "missing_experience"
    OUTDATED_SKILL = "outdated_skill"


class RiskLevel(str, Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DecisionType(str, Enum):
    """Decision outcomes"""
    REUSE = "REUSE"
    RESCORE = "RESCORE"
    LIGHT_RESCREEN = "LIGHT_RESCREEN"
    DEEP_INTERVIEW = "DEEP_INTERVIEW"
    REJECT = "REJECT"


class InterviewRound(str, Enum):
    """Interview round types"""
    SCREENING = "screening"
    ROUND1 = "round1"
    ROUND2 = "round2"
    FINAL = "final"


class InterviewDecision(str, Enum):
    """Interview outcomes"""
    PASS = "PASS"
    FAIL = "FAIL"


# Literal types for additional type safety
SourceLanguage = Literal["en", "vi"]
TranslationStatus = Literal["pending", "completed", "failed"]
SourceType = Literal["pdf", "docx", "text"]
OwnershipLevel = Literal["owned", "led", "contributed", "supported"]