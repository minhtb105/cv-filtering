"""
Interview Decision Engine

Bài toán cốt lõi: Candidate A đã được phỏng vấn trước. Có JD mới.
Có cần phỏng vấn lại không?

Thiết kế quyết định:

1. Nhánh FIRST-TIME (không có lịch sử):
   base_score → threshold lookup → decision

2. Nhánh RETURNING (có lịch sử phỏng vấn):
   base_score + delta_adjustments → adjusted_threshold → decision

   Delta signals:
   - CV delta: candidate thêm skills mới, kinh nghiệm mới → nới ngưỡng
   - JD delta: JD thay đổi nhiều → tăng ngưỡng (cần đánh giá lại)
   - Time delta: lâu rồi → tăng ngưỡng (skills có thể đã stale)

Tại sao dùng "adjusted threshold" thay vì "adjusted score":
   - Score là kết quả objective (CV vs JD matching)
   - Threshold là policy của recruiter (risk tolerance)
   - Candidate returning được "benefit of the doubt" → threshold thấp hơn
   - JD thay đổi lớn → cần đánh giá lại → threshold cao hơn
   - Cách này dễ explain hơn cho recruiter

Evidence:
   Mỗi decision kèm evidence cụ thể từ CV và JD để recruiter có thể verify.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class MatchScore:
    """
    Score output từ CompositeScorer (0-100).
    Tất cả sub-scores đều 0-100.
    """
    composite_score: float = 0.0
    skill_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    interview_score: float = 0.0
    
    # Missing skills để hiển thị trong evidence
    missing_required_skills: List[str] = field(default_factory=list)
    missing_preferred_skills: List[str] = field(default_factory=list)


@dataclass
class PreviousAssessment:
    """
    Kết quả phỏng vấn lần trước.
    """
    assessment_id: str
    assessed_at: datetime
    composite_score: float
    
    # Interview feedback (nếu có)
    technical_score: Optional[float] = None
    soft_skills_score: Optional[float] = None
    cultural_fit_score: Optional[float] = None
    interview_notes: str = ""
    
    # Snapshot CV skills lúc phỏng vấn (để compute delta)
    cv_skills_snapshot: List[str] = field(default_factory=list)
    
    # JD lúc phỏng vấn (để compute JD delta)
    jd_skills_snapshot: List[str] = field(default_factory=list)
    
    def days_since(self) -> int:
        """Số ngày kể từ lần phỏng vấn trước."""
        delta = datetime.utcnow() - self.assessed_at
        return delta.days


@dataclass
class DeltaAnalysis:
    """
    Phân tích thay đổi giữa lần phỏng vấn trước và hiện tại.
    
    Dùng để điều chỉnh ngưỡng quyết định, không phải score.
    Positive delta → nới ngưỡng (candidate improve)
    Negative delta → tăng ngưỡng (need stricter review)
    """
    # CV changes
    new_skills_count: int = 0           # Skills mới thêm vào CV
    new_experience_months: float = 0.0  # Kinh nghiệm tích lũy thêm
    cv_updated: bool = False            # CV có được update không
    
    # JD changes  
    jd_similarity: float = 1.0         # Jaccard similarity [0,1]: 1=identical, 0=hoàn toàn khác
    jd_required_skills_added: int = 0  # Skills mới trong JD mà candidate không có
    
    # Time
    days_since_last_interview: int = 0
    
    def threshold_adjustment(self) -> float:
        """
        Tính điều chỉnh ngưỡng dựa trên deltas.
        Returns: float [-15, +15] — negative = nới ngưỡng, positive = tăng ngưỡng
        
        Logic:
        - Candidate thêm skills mới (CV improve): nới ngưỡng (-5 max)
        - Candidate có thêm kinh nghiệm: nới ngưỡng (-3 max)
        - JD thay đổi nhiều: tăng ngưỡng (+10 max)
        - Thời gian lâu (> 12 tháng): tăng ngưỡng (+7 max)
        - Thời gian vừa phải (6-12 tháng): tăng nhẹ (+3)
        - Thời gian ngắn (< 6 tháng): không ảnh hưởng
        """
        adjustment = 0.0
        
        # CV improvements → nới ngưỡng
        if self.new_skills_count >= 3:
            adjustment -= 5.0   # Đáng kể
        elif self.new_skills_count >= 1:
            adjustment -= 2.0   # Nhỏ
        
        if self.new_experience_months >= 12:
            adjustment -= 3.0   # Thêm >= 1 năm kinh nghiệm
        elif self.new_experience_months >= 6:
            adjustment -= 1.5
        
        # JD changes → tăng ngưỡng
        jd_change = 1.0 - self.jd_similarity  # 0=no change, 1=completely different
        if jd_change >= 0.5:
            adjustment += 10.0  # JD thay đổi lớn
        elif jd_change >= 0.25:
            adjustment += 5.0   # JD thay đổi vừa
        elif jd_change >= 0.10:
            adjustment += 2.0   # JD thay đổi nhỏ
        
        # JD added new required skills → tăng ngưỡng
        adjustment += min(self.jd_required_skills_added * 1.5, 5.0)
        
        # Time decay → tăng ngưỡng
        if self.days_since_last_interview >= 365:
            adjustment += 7.0   # > 1 năm
        elif self.days_since_last_interview >= 180:
            adjustment += 3.0   # 6-12 tháng
        elif self.days_since_last_interview >= 90:
            adjustment += 1.0   # 3-6 tháng
        
        return max(-15.0, min(15.0, adjustment))  # Clamp [-15, 15]
    
    def summary(self) -> str:
        """Human-readable summary của delta analysis."""
        parts = []
        if self.new_skills_count > 0:
            parts.append(f"+{self.new_skills_count} new skills on CV")
        if self.new_experience_months >= 6:
            parts.append(f"+{self.new_experience_months:.0f} months experience")
        if self.jd_similarity < 0.9:
            pct = (1 - self.jd_similarity) * 100
            parts.append(f"JD changed {pct:.0f}%")
        if self.days_since_last_interview > 0:
            parts.append(f"{self.days_since_last_interview} days since last interview")
        return "; ".join(parts) if parts else "No significant changes"


@dataclass
class DecisionResult:
    """
    Output của InterviewDecisionEngine.
    
    Design principle: Mỗi decision phải có reasoning và evidence
    để recruiter có thể verify và override nếu cần.
    """
    decision: str  # REUSE / RESCORE / LIGHT_RESCREEN / DEEP_INTERVIEW / REJECT
    confidence: float  # [0, 1]
    
    reasoning: str  # Giải thích ngắn gọn (1-2 câu)
    evidence: List[str] = field(default_factory=list)  # Bullet points cụ thể
    
    # Scores
    composite_score: float = 0.0
    effective_threshold: float = 0.0  # Ngưỡng sau khi điều chỉnh
    
    # Context
    is_first_time: bool = True
    delta_analysis: Optional[DeltaAnalysis] = None
    
    # Recruiter guidance
    recommended_interview_duration: Optional[str] = None
    focus_areas: List[str] = field(default_factory=list)  # Những gì cần hỏi
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "confidence": round(self.confidence, 2),
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "composite_score": round(self.composite_score, 1),
            "effective_threshold": round(self.effective_threshold, 1),
            "is_first_time": self.is_first_time,
            "recommended_interview_duration": self.recommended_interview_duration,
            "focus_areas": self.focus_areas,
            "delta_summary": self.delta_analysis.summary() if self.delta_analysis else None,
        }


# ---------------------------------------------------------------------------
# Decision Engine
# ---------------------------------------------------------------------------

class InterviewDecisionEngine:
    """
    Quyết định có cần phỏng vấn lại không.
    
    Thresholds mặc định (có thể override qua config):
    
    Score range → Decision:
    [0, REJECT_THRESHOLD)             → REJECT
    [REJECT_THRESHOLD, RESCREEN_LOW)  → DEEP_INTERVIEW
    [RESCREEN_LOW, RESCREEN_HIGH)     → LIGHT_RESCREEN
    [RESCREEN_HIGH, REUSE_THRESHOLD)  → RESCORE (không cần gặp)
    [REUSE_THRESHOLD, 100]            → REUSE (dùng kết quả cũ)
    
    Nhưng thresholds này bị adjust bởi DeltaAnalysis.threshold_adjustment()
    """
    
    DEFAULT_THRESHOLDS = {
        "reject": 40.0,        # < 40: loại ngay
        "deep_interview": 60.0, # 40-60: cần phỏng vấn đầy đủ
        "light_rescreen": 75.0, # 60-75: phỏng vấn ngắn 30 phút
        "rescore": 85.0,        # 75-85: tự rescore không cần gặp
        # >= 85: REUSE kết quả cũ
    }
    
    # Chỉ áp dụng REUSE nếu có previous assessment
    # First-time candidate không có REUSE/RESCORE option
    
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
    
    def decide(
        self,
        match_score: MatchScore,
        previous_assessment: Optional[PreviousAssessment] = None,
        cv_current_skills: Optional[List[str]] = None,
        jd_current: Optional[Any] = None,  # JobRequirements
    ) -> DecisionResult:
        """
        Main decision function.
        
        Args:
            match_score: Kết quả scoring CV vs JD hiện tại
            previous_assessment: Kết quả phỏng vấn cũ (None = first time)
            cv_current_skills: List skills hiện tại của CV
            jd_current: JobRequirements hiện tại
            
        Returns:
            DecisionResult với decision, reasoning, evidence
        """
        score = match_score.composite_score
        is_first_time = previous_assessment is None
        
        if is_first_time:
            return self._decide_first_time(match_score)
        else:
            delta = self._compute_delta(
                previous_assessment,
                cv_current_skills or [],
                jd_current,
            )
            return self._decide_returning(match_score, previous_assessment, delta)
    
    def _decide_first_time(self, match_score: MatchScore) -> DecisionResult:
        """Decision cho candidate chưa từng phỏng vấn."""
        score = match_score.composite_score
        t = self.thresholds
        
        # First-time chỉ có: REJECT / DEEP_INTERVIEW / LIGHT_RESCREEN
        # Không có REUSE hoặc RESCORE (chưa có gì để reuse)
        
        if score < t["reject"]:
            return DecisionResult(
                decision="REJECT",
                confidence=self._calc_confidence(score, t["reject"], direction="below"),
                reasoning=f"Score {score:.0f}/100 thấp hơn ngưỡng tối thiểu {t['reject']:.0f}.",
                evidence=self._build_evidence(match_score),
                composite_score=score,
                effective_threshold=t["reject"],
                is_first_time=True,
            )
        
        elif score < t["light_rescreen"]:
            return DecisionResult(
                decision="DEEP_INTERVIEW",
                confidence=self._calc_confidence(score, t["light_rescreen"], direction="below"),
                reasoning=(
                    f"Score {score:.0f}/100 cần phỏng vấn đầy đủ để verify. "
                    f"Có {len(match_score.missing_required_skills)} required skills cần clarify."
                ),
                evidence=self._build_evidence(match_score),
                composite_score=score,
                effective_threshold=t["light_rescreen"],
                is_first_time=True,
                recommended_interview_duration="60-90 phút",
                focus_areas=self._build_focus_areas(match_score),
            )
        
        else:
            return DecisionResult(
                decision="LIGHT_RESCREEN",
                confidence=self._calc_confidence(score, t["light_rescreen"], direction="above"),
                reasoning=(
                    f"Score {score:.0f}/100 đủ để phỏng vấn ngắn (30 phút) "
                    f"confirm skills và culture fit."
                ),
                evidence=self._build_evidence(match_score),
                composite_score=score,
                effective_threshold=t["light_rescreen"],
                is_first_time=True,
                recommended_interview_duration="30 phút",
                focus_areas=self._build_focus_areas(match_score),
            )
    
    def _decide_returning(
        self,
        match_score: MatchScore,
        previous: PreviousAssessment,
        delta: DeltaAnalysis,
    ) -> DecisionResult:
        """Decision cho candidate đã từng phỏng vấn."""
        score = match_score.composite_score
        
        # Điều chỉnh thresholds dựa trên delta
        threshold_adj = delta.threshold_adjustment()
        adjusted_thresholds = {
            k: v + threshold_adj
            for k, v in self.thresholds.items()
        }
        t = adjusted_thresholds
        
        evidence = self._build_evidence(match_score)
        evidence.append(f"Delta analysis: {delta.summary()}")
        evidence.append(
            f"Threshold adjusted by {threshold_adj:+.1f} points "
            f"({'nới ngưỡng' if threshold_adj < 0 else 'tăng ngưỡng'})"
        )
        
        if score < t["reject"]:
            return DecisionResult(
                decision="REJECT",
                confidence=self._calc_confidence(score, t["reject"], direction="below"),
                reasoning=(
                    f"Score {score:.0f}/100 vẫn thấp hơn ngưỡng sau adjustment. "
                    f"Candidate không phù hợp với vị trí này."
                ),
                evidence=evidence,
                composite_score=score,
                effective_threshold=t["reject"],
                is_first_time=False,
                delta_analysis=delta,
            )
        
        elif score < t["deep_interview"]:
            return DecisionResult(
                decision="DEEP_INTERVIEW",
                confidence=self._calc_confidence(score, t["deep_interview"], direction="below"),
                reasoning=(
                    f"Score {score:.0f}/100. Cần phỏng vấn lại đầy đủ. "
                    f"Lần trước: {previous.composite_score:.0f}/100 ({previous.days_since()} ngày trước)."
                ),
                evidence=evidence,
                composite_score=score,
                effective_threshold=t["deep_interview"],
                is_first_time=False,
                delta_analysis=delta,
                recommended_interview_duration="60-90 phút",
                focus_areas=self._build_focus_areas(match_score),
            )
        
        elif score < t["light_rescreen"]:
            return DecisionResult(
                decision="LIGHT_RESCREEN",
                confidence=self._calc_confidence(score, t["light_rescreen"], direction="below"),
                reasoning=(
                    f"Score {score:.0f}/100. Cần verify một vài điểm mới trước khi tái sử dụng. "
                    f"Lần trước: {previous.composite_score:.0f}/100."
                ),
                evidence=evidence,
                composite_score=score,
                effective_threshold=t["light_rescreen"],
                is_first_time=False,
                delta_analysis=delta,
                recommended_interview_duration="30 phút",
                focus_areas=self._build_focus_areas(match_score),
            )
        
        elif score < t["rescore"]:
            return DecisionResult(
                decision="RESCORE",
                confidence=self._calc_confidence(score, t["rescore"], direction="below"),
                reasoning=(
                    f"Score {score:.0f}/100 đủ tốt. Có thể rescore tự động. "
                    f"Không cần gặp candidate. Delta không đáng kể."
                ),
                evidence=evidence,
                composite_score=score,
                effective_threshold=t["rescore"],
                is_first_time=False,
                delta_analysis=delta,
            )
        
        else:
            return DecisionResult(
                decision="REUSE",
                confidence=self._calc_confidence(score, t["rescore"], direction="above"),
                reasoning=(
                    f"Score {score:.0f}/100 cao và ổn định. "
                    f"Tái sử dụng kết quả lần trước ({previous.composite_score:.0f}/100). "
                    f"Không cần phỏng vấn lại."
                ),
                evidence=evidence,
                composite_score=score,
                effective_threshold=t["rescore"],
                is_first_time=False,
                delta_analysis=delta,
            )
    
    def _compute_delta(
        self,
        previous: PreviousAssessment,
        current_skills: List[str],
        jd_current: Optional[Any],
    ) -> DeltaAnalysis:
        """Tính delta giữa lần phỏng vấn trước và hiện tại."""
        
        # CV delta: new skills
        prev_skill_set = set(s.lower() for s in previous.cv_skills_snapshot)
        curr_skill_set = set(s.lower() for s in current_skills)
        new_skills = curr_skill_set - prev_skill_set
        
        # JD delta: Jaccard similarity
        jd_similarity = 1.0
        jd_required_added = 0
        if jd_current and previous.jd_skills_snapshot:
            prev_jd_skills = set(s.lower() for s in previous.jd_skills_snapshot)
            curr_jd_skills = set(s.lower() for s in getattr(jd_current, 'required_skills', []))
            
            # Jaccard
            if prev_jd_skills or curr_jd_skills:
                intersection = len(prev_jd_skills & curr_jd_skills)
                union = len(prev_jd_skills | curr_jd_skills)
                jd_similarity = intersection / union if union > 0 else 1.0
            
            # New required skills mà candidate chưa có
            new_required = curr_jd_skills - prev_jd_skills
            missing_in_cv = new_required - curr_skill_set
            jd_required_added = len(missing_in_cv)
        
        return DeltaAnalysis(
            new_skills_count=len(new_skills),
            new_experience_months=0.0,  # TODO: compute từ experience entries
            cv_updated=bool(new_skills),
            jd_similarity=jd_similarity,
            jd_required_skills_added=jd_required_added,
            days_since_last_interview=previous.days_since(),
        )
    
    def _build_evidence(self, score: MatchScore) -> List[str]:
        """Build evidence bullets từ score breakdown."""
        evidence = []
        
        evidence.append(f"Composite score: {score.composite_score:.1f}/100")
        evidence.append(
            f"Breakdown: Skills {score.skill_score:.1f} | "
            f"Experience {score.experience_score:.1f} | "
            f"Education {score.education_score:.1f}"
        )
        
        if score.missing_required_skills:
            top3 = score.missing_required_skills[:3]
            more = len(score.missing_required_skills) - 3
            skills_str = ", ".join(top3)
            if more > 0:
                skills_str += f" (+{more} more)"
            evidence.append(f"Missing required skills: {skills_str}")
        
        if score.missing_preferred_skills:
            top3 = score.missing_preferred_skills[:3]
            evidence.append(f"Missing preferred skills: {', '.join(top3)}")
        
        return evidence
    
    def _build_focus_areas(self, score: MatchScore) -> List[str]:
        """Gợi ý focus areas cho interviewer."""
        focus = []
        
        if score.missing_required_skills:
            focus.append(f"Verify skills: {', '.join(score.missing_required_skills[:3])}")
        
        if score.experience_score < 60:
            focus.append("Deep dive vào experience timeline và responsibilities")
        
        if score.skill_score < 60:
            focus.append("Technical screening bắt buộc")
        
        if not focus:
            focus.append("Culture fit và communication style")
            focus.append("Motivation và career goals")
        
        return focus
    
    @staticmethod
    def _calc_confidence(score: float, threshold: float, direction: str) -> float:
        """
        Tính confidence của decision dựa trên khoảng cách từ threshold.
        
        Càng xa threshold → confidence càng cao.
        Càng gần threshold → confidence thấp (borderline case).
        """
        distance = abs(score - threshold)
        
        # Normalize: distance 0-20 points → confidence 0.5-0.95
        confidence = 0.50 + min(distance / 20.0, 1.0) * 0.45
        
        return round(confidence, 2)


# ---------------------------------------------------------------------------
# Fix cho matching_engine.py — NameError bug
# ---------------------------------------------------------------------------

# Bug gốc trong src/scoring/matching_engine.py dòng 128:
#   if normalized == canonical.lower() or string in aliases:
#                                         ^^^^^^ undefined!
# 
# Fix: thay 'string' → 'normalized'
# 
# Đoạn code đúng:
# @staticmethod
# def get_canonical_name(skill: str) -> str:
#     normalized = SkillNormalization.normalize(skill)
#     for canonical, aliases in SkillNormalization.ALIASES.items():
#         if normalized == canonical.lower() or normalized in aliases:  # FIX: string → normalized
#             return canonical
#     return normalized
