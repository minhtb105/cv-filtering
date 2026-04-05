# CV Intelligence Platform

> Nền tảng AI giúp nhà tuyển dụng quyết định **có cần phỏng vấn lại ứng viên hay không** — tự động parse CV, so sánh với JD, và đưa ra khuyến nghị có giải thích.

---

## Mục tiêu

Bài toán cốt lõi: *Ứng viên A đã được phỏng vấn 6 tháng trước cho vị trí X. Hôm nay công ty mở thêm vị trí Y tương tự. Có cần phỏng vấn lại không?*

Hệ thống trả lời bằng một trong 5 quyết định có lý giải:

| Quyết định | Ý nghĩa | Thời gian tiết kiệm |
|---|---|---|
| `REUSE` | Dùng kết quả cũ, không cần phỏng vấn lại | 100% |
| `RESCORE` | Tự động tính lại điểm, không cần gặp ứng viên | 100% |
| `LIGHT_RESCREEN` | Phỏng vấn ngắn 30 phút, verify một vài điểm | 50–60% |
| `DEEP_INTERVIEW` | Phỏng vấn đầy đủ 60–90 phút | 0% |
| `REJECT` | Điểm quá thấp, loại ngay | 100% |

---

## Kiến trúc Hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                     CV Intelligence Platform                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   PDF/CV Input              JD Input (text/HTML)                 │
│        │                          │                              │
│        ▼                          ▼                              │
│  ┌──────────────┐          ┌──────────────┐                      │
│  │  PDFExtractor│          │   JDParser   │                      │
│  │  (5-Step Geo)│          │(LLM + Regex) │                      │
│  └──────┬───────┘          └──────┬───────┘                      │
│         │                         │                              │
│         ▼                         │                              │
│  ┌──────────────┐                 │                              │
│  │HRExtractor   │                 │                              │
│  │  Agent (LLM) │                 │                              │
│  └──────┬───────┘                 │                              │
│         │                         │                              │
│         ▼                         │                              │
│  ┌──────────────┐                 │                              │
│  │PostProcessor │                 │                              │
│  │(dates+exp+   │                 │                              │
│  │  seniority)  │                 │                              │
│  └──────┬───────┘                 │                              │
│         │                         │                              │
│         ▼                         ▼                              │
│  ┌──────────────────────────────────────┐                        │
│  │           CompositeScorer            │                        │
│  │  Skill(30%) + Exp(35%) + Edu(20%)    │                        │
│  │         + Interview(15%)             │                        │
│  └──────────────────┬───────────────────┘                        │
│                     │                                             │
│                     ▼                                             │
│  ┌──────────────────────────────────────┐                        │
│  │      InterviewDecisionEngine         │                        │
│  │  ┌─────────────┐  ┌───────────────┐ │                        │
│  │  │ First-time  │  │   Returning   │ │                        │
│  │  │  branch     │  │    branch     │ │                        │
│  │  │             │  │  DeltaAnalysis│ │                        │
│  │  └─────────────┘  └───────────────┘ │                        │
│  └──────────────────┬───────────────────┘                        │
│                     │                                             │
│                     ▼                                             │
│  ┌──────────────────────────────────────┐                        │
│  │  DecisionResult                      │                        │
│  │  • decision (REUSE/RESCORE/...)      │                        │
│  │  • reasoning (1–2 câu)              │                        │
│  │  • evidence (bullet points)          │                        │
│  │  • focus_areas (câu hỏi phỏng vấn)  │                        │
│  └──────────────────────────────────────┘                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Thuật Toán Chi Tiết

### 1. PDF Extraction — 5-Step Geometric Pipeline

**Module:** `src/extraction/pdf_extractor.py`

Không dựa vào font size hay CSS styling. Chỉ dùng tọa độ hình học (x, y, width, height).

#### Step 1 — Word Extraction

```
PyMuPDF.get_text("words") → [(x0, y0, x1, y1, text, block_no, line_no, word_no)]
→ Unicode NFC normalize mỗi word
→ List[Word(text, x0, y0, x1, y1, page)]
```

#### Step 2 — Line Assembly

```
Input:  List[Word] sorted by (y_center, x0)
Logic:  Two words belong to the same line if:
          abs(word.y_center - prev.y_center) < max(word.height, prev.height) × 0.4
Output: List[Line] — mỗi Line chứa words sorted by x0
```

Ngưỡng 0.4× height cho phép words có size khác nhau nhỏ vẫn được xếp chung dòng (subscript, superscript).

#### Step 3a — Block Detection

```
Input:  List[Line], median_line_height (median của tất cả heights trong trang)
Logic:  Two lines belong to the same block if BOTH:
          vertical_gap = line.y0 - prev_line.y1 < 1.0 × median_line_height
          x_center_shift = |line.x_center - prev_line.x_center| < 20% page_width
Output: List[Block]
```

#### Step 3b — Table Detection

```
Input:  mỗi Block
Logic:  A line is a "table row" if:
          max_gap_between_words > 8% page_width
        If ALL lines in a block are table rows AND len(lines) >= 2:
          → Convert to Markdown table format
Output: Block với block_type="table", _md_override = Markdown table string
```

#### Step 3c — Block Classification (5 Rules)

Một block (single-line) là `full_width_header` nếu **TẤT CẢ** 5 điều kiện đúng:

```
Rule 1: Không có word nào khác nằm trên cùng Y-band (±0.5×height) trên toàn trang
        → Header không chạy song song với content ở cột khác

Rule 2: x_span < 60% page_width
        → Header không chiếm hết chiều ngang trang (đó là body text)

Rule 3: gap_above > 1.5 × median_line_height
     AND gap_below > 1.5 × median_line_height
        → Có khoảng cách rõ ràng trên và dưới header

Rule 4: text không kết thúc bằng  . ! ? ,
        → "Python Developer." không phải header
        → "WORK EXPERIENCE:" là header (: được cho phép)

Rule 5: 0.05 ≤ x_center / page_width ≤ 0.95
        → Loại page numbers, watermarks ở tận lề
        → Giữ lại: left-aligned, centered, right-aligned headers
```

Nếu fail bất kỳ rule nào → classify theo vị trí:
```
x_span ≥ 75% page_width  → full_width_body
x_center < 45% page_width → left_col
else                       → right_col
```

#### Step 4 — Reading Order Assembly

```
Two-column layout (có cả left_col và right_col):
  sort key = (type_priority, y0)
  type_priority: full_width_header(0) → left_col(1) → right_col(2) → body(3)

Single-column layout:
  sort key = (y0, type_priority)   ← y0 là primary key
  → giữ đúng thứ tự dọc, header không bị tách ra khỏi content
```

Output: Intermediate markdown dump với format:
```
========================================
PAGE: 1 | TYPE: FULL_WIDTH_HEADER
========================================
WORK EXPERIENCE

========================================
PAGE: 1 | TYPE: FULL_WIDTH_BODY
========================================
Senior Engineer tại Tech Corp ...
```

---

### 2. JD Parsing

**Module:** `src/extraction/jd_parser.py`

JD đơn giản hơn CV — thường là plain text, không cần geometric extraction.

#### Schema Output

```python
JobRequirements:
  title: str
  company: str
  required_skills: List[str]   # "must have" — penalize mạnh nếu thiếu
  preferred_skills: List[str]  # "nice to have" — penalize nhẹ
  min_experience_years: float
  max_experience_years: Optional[float]
  required_seniority: str      # junior/mid/senior/lead
  required_degree: str         # bachelor/master/phd
  required_languages: List[str]
  location: str
  remote_eligible: bool
```

#### Strategy

```
1. LLM extraction (primary):
   Ollama → Qwen2.5-coder:3b → JSON schema extraction
   Confidence: ~0.85

2. Regex fallback (khi LLM unavailable):
   - Keyword matching từ danh sách ~50 common tech skills
   - Experience pattern: "X years", "minimum X years", "X+ years"
   - Seniority: infer từ title keywords (senior/junior/lead/...)
   - Degree: pattern matching (bachelor/master/phd)
   Confidence: ~0.50
```

#### JD Similarity (Jaccard)

Dùng để đo mức độ thay đổi của JD giữa hai thời điểm:

```
jaccard(JD_old, JD_new) = |skills_old ∩ skills_new| / |skills_old ∪ skills_new|

Ví dụ:
  JD_old required: {python, django, docker}
  JD_new required: {python, fastapi, kubernetes}
  
  intersection = {python} → size 1
  union = {python, django, docker, fastapi, kubernetes} → size 5
  jaccard = 1/5 = 0.20  (JD thay đổi 80%)
```

Range:
- `1.0` = JD không thay đổi gì
- `0.5–0.9` = thay đổi nhỏ (thêm/bớt vài skill)
- `< 0.5` = thay đổi lớn, cần đánh giá lại candidate

---

### 3. Scoring — CompositeScorer

**Module:** `src/scoring/composite_scorer.py`

Tất cả scores trong range `[0, 100]`.

#### Công thức

```
composite_score = skill_score    × 0.30
                + experience_score × 0.35
                + education_score  × 0.20
                + interview_score  × 0.15
```

#### 3.1 Skill Scorer

```python
Input:  cv_skills: List[str], jd_required_skills: List[str]
Output: float [0, 100]

Algorithm:
  For each jd_skill in required_skills:
    For each cv_skill in cv_skills:
      similarity = SequenceMatcher(jd_skill, cv_skill).ratio()
      if similarity > 0.70:
        matched_count += 1; break

  match_percentage = matched_count / len(required_skills) × 100

  bonus = min(10, extra_skills_count × 2)   # Tối đa +10 điểm

  skill_score = min(100, match_percentage + bonus)
```

Skill normalization (aliases):
- "node.js" = "nodejs" = "node"
- "react.js" = "react" = "reactjs"
- "golang" = "go"
- "k8s" = "kubernetes"
- "postgres" = "postgresql" = "sql"

#### 3.2 Experience Scorer

```python
Input:  cv_years: float, cv_seniority: str
        jd_min_years: float, jd_seniority: str
Output: float [0, 100]

Years sub-score (weight 40%):
  if cv_years < jd_min_years:
    years_score = (cv_years / jd_min_years) × 70    # Partial credit
  elif cv_years == jd_min_years:
    years_score = 80
  else:
    excess = min(cv_years - jd_min_years, 10)
    years_score = min(100, 80 + (excess / 10) × 20)  # Max bonus +20

Seniority sub-score (weight 40%):
  Mapping: junior=1, mid=2, senior=3, lead=4, manager=5
  diff = cv_level - jd_level
  if diff == 0:  seniority_score = 85
  if diff == 1:  seniority_score = min(100, 85 + 5) = 90+   (overqualified OK)
  if diff == -1: seniority_score = 85 × (cv_level/jd_level) ≈ 57–68
  if diff <= -2: seniority_score = cv_level/jd_level × 70   (underqualified)

Progression sub-score (weight 20%):
  career_progression > 0 → min(100, 50 + progression × 10)
  else                   → 50

experience_score = years_score×0.4 + seniority_score×0.4 + progression_score×0.2
```

#### 3.3 Education Scorer

```python
Input:  cv_degrees: List[str], cv_certifications: List[str]
        jd_required_degree: str, jd_preferred_certs: List[str]
Output: float [0, 100]

Degree hierarchy: phd=4, master=3, bachelors=2, associate=1, high_school=0

Degree sub-score (weight 70%):
  cv_max_level = max(degree_hierarchy[d] for d in cv_degrees)
  jd_level = degree_hierarchy[jd_required_degree]

  if cv_max_level >= jd_level + 1:  degree_score = 95   (overqualified)
  if cv_max_level == jd_level:      degree_score = 100  (exact match)
  if cv_max_level == jd_level - 1:  degree_score = 70   (one level below)
  else:                             degree_score = 30

Cert sub-score (weight 30%):
  matched_certs = count(preferred_cert in cv_certs for each preferred_cert)
  cert_score = matched_certs / len(jd_preferred_certs) × 100

education_score = degree_score×0.7 + cert_score×0.3
```

#### 3.4 Interview Scorer

```python
Input:  interview_result: {technical_score, soft_skills_score, cultural_fit_score}
Output: float [0, 100]

if not interview_result:
  return 50  # Neutral — không có data

interview_score = technical_score × 0.40
               + soft_skills_score × 0.30
               + cultural_fit_score × 0.30
```

---

### 4. RescoringEngine — Khi Nào Tính Lại Điểm

**Module:** `src/scoring/rescoring_engine.py`

#### Trigger Events

```
CV_UPDATED      priority=8  → Invalidate tất cả scores của CV đó
JD_UPDATED      priority=8  → Invalidate tất cả scores của JD đó
INTERVIEW_RESULT priority=9  → Tính lại composite (interview weight thay đổi)
MANUAL_RESCORE  priority=5  → Ad-hoc, triggered by recruiter
```

#### Queue Processing

```
rescore_queue sorted by: (-priority, timestamp)
→ High priority items processed first
→ Same priority: FIFO

For each (cv_id, jd_id) pair:
  1. Fetch CV data (cache-first: Redis → MongoDB)
  2. Fetch JD data (cache-first: Redis → MongoDB)
  3. Fetch interview result if exists
  4. CompositeScorer.score(cv_data, jd_data, interview_result)
  5. Store new score → ScoreRepository
  6. Update cache (TTL: 24h for scores)
```

#### Cache TTL Policy

```
CV extraction data:   48 hours
CV metadata:          24 hours
Score (latest):       24 hours
JD extraction data:   7 days     (JD ít thay đổi)
Score history:        30 days
Interview results:    30 days
Comparison results:   1 hour     (short-lived analytics)
Rankings:             1 hour
```

---

### 5. Interview Decision Engine

**Module:** `src/decision/interview_decision_engine.py`

#### Default Thresholds

```
score < 40:          REJECT
40 ≤ score < 60:     DEEP_INTERVIEW   (60–90 phút)
60 ≤ score < 75:     LIGHT_RESCREEN   (30 phút)
75 ≤ score < 85:     RESCORE          (tự động, không gặp)
score ≥ 85:          REUSE            (dùng kết quả cũ)
```

*Lưu ý: REUSE và RESCORE chỉ áp dụng cho returning candidates (có lịch sử phỏng vấn). First-time candidates có thể đạt tối đa LIGHT_RESCREEN.*

#### Nhánh 1: First-Time Candidate

```
score = CompositeScorer.score(cv, jd)

if score < T_reject:        → REJECT
elif score < T_rescreen:    → DEEP_INTERVIEW
else:                       → LIGHT_RESCREEN
```

#### Nhánh 2: Returning Candidate (có previous assessment)

```
score = CompositeScorer.score(cv, jd)

delta = DeltaAnalysis(
  new_skills_count         = |current_cv_skills - prev_cv_skills|,
  new_experience_months    = total_months_now - total_months_at_prev_assessment,
  jd_similarity            = Jaccard(prev_jd_skills, curr_jd_skills),
  jd_required_skills_added = |new_required_skills - current_cv_skills|,
  days_since_last_interview = (now - prev.assessed_at).days,
)

threshold_adjustment = delta.threshold_adjustment()

adjusted_thresholds = {k: v + threshold_adjustment for k, v in DEFAULT_THRESHOLDS}

if score < adjusted_T_reject:     → REJECT
elif score < adjusted_T_deep:     → DEEP_INTERVIEW
elif score < adjusted_T_light:    → LIGHT_RESCREEN
elif score < adjusted_T_rescore:  → RESCORE
else:                             → REUSE
```

#### Delta → Threshold Adjustment
*Lưu ý: Trong mỗi category, chỉ áp dụng tier cao nhất thỏa mãn. Adjustments giữa các categories được cộng dồn.*

*Negative adjustment = nới ngưỡng (candidate được lợi). Positive = tăng ngưỡng (cần đánh giá kỹ hơn).*

```
CV improvements (→ nới ngưỡng):
  new_skills_count ≥ 3    → -5.0
  new_skills_count ≥ 1    → -2.0
  new_experience ≥ 12 mo  → -3.0
  new_experience ≥ 6 mo   → -1.5

JD changes (→ tăng ngưỡng):
  jd_change ≥ 50%         → +10.0
  jd_change ≥ 25%         → +5.0
  jd_change ≥ 10%         → +2.0
  per new required skill candidate lacks → +1.5 (max +5.0)

Time decay (→ tăng ngưỡng):
  > 365 days              → +7.0
  180–365 days            → +3.0
  90–180 days             → +1.0
  < 90 days               → 0.0

Total adjustment clamped to [-15, +15]
```

#### Ví dụ tính toán

```
Scenario: Candidate đã phỏng vấn 8 tháng trước (240 ngày)
  - CV thêm 2 skills mới (kubernetes, terraform)
  - JD thay đổi 30% (một số roles bổ sung)
  - Current score: 72/100

CV improvements:  new_skills=2 → -2.0
Time decay:       240 days → +3.0
JD changes:       30% → +5.0

total_adjustment = -2.0 + 3.0 + 5.0 = +6.0

Effective thresholds:
  reject:          40 + 6 = 46
  deep_interview:  60 + 6 = 66
  light_rescreen:  75 + 6 = 81
  rescore:         85 + 6 = 91

Score 72 < 81 → LIGHT_RESCREEN
Evidence:
  ✓ "Score 72.0/100"
  ✓ "Breakdown: Skills 68.0 | Experience 75.0 | Education 80.0"
  ✓ "Delta: +2 new skills; JD changed 30%; 240 days since interview"
  ✓ "Threshold adjusted +6.0 points (tăng ngưỡng)"
```

---

### 6. Matching Engine — Skill Normalization

**Module:** `src/scoring/matching_engine.py`

#### are_equivalent(skill1, skill2)

```python
norm1 = normalize(skill1)  # lowercase, alphanumeric only
norm2 = normalize(skill2)

if norm1 == norm2: return True

# Alias lookup
for canonical, aliases in ALIASES:
  if norm1 in [canonical] + aliases AND norm2 in [canonical] + aliases:
    return True

return False
```

#### _match_skills() trong MatchingEngine

```
candidate_skills = {normalized_name → Skill}
required_skills = [s.lower() for s in jd.required_skills]

missing_required = [
  req for req in required_skills
  if NOT any(are_equivalent(req, c_skill) for c_skill in candidate_skills)
]

matched_required = len(required_skills) - len(missing_required)
required_match_rate = matched_required / total_required

# Preferred bonus (max +25%)
preferred_bonus = (matched_preferred / total_preferred) × 0.25

skill_match_score = min(1.0, required_match_rate + preferred_bonus)
```

---

## Cài Đặt

### Yêu cầu

- Python 3.10+
- MongoDB (local hoặc Atlas)
- Redis (optional)
- [Ollama](https://ollama.ai) với model `qwen2.5-coder:3b-instruct-q4_K_M`

### Setup

```bash
git clone <repo-url> && cd cv-intelligence

pip install pymupdf rapidfuzz python-dotenv \
            pydantic fastapi uvicorn python-dateutil redis pymongo

# Ollama (optional nhưng recommended)
ollama pull qwen2.5-coder:3b-instruct-q4_K_M
ollama serve

cp .env.example .env   # Cấu hình MONGODB_URL, OLLAMA_BASE_URL
```

---

## Sử Dụng

### Parse CV

```python
from src.extraction import CVParser, CVParsingConfig

parser = CVParser(CVParsingConfig(use_llm_extraction=True))
result = parser.parse_cv("data/resume.pdf")

# result keys:
# success, filename, cleaned_text, extracted_profile,
# total_years_experience, seniority_level, markdown, errors
```

### Parse JD

```python
from src.extraction.jd_parser import JDParser

parser = JDParser()
jd = parser.parse(open("job_description.txt").read(), jd_id="jd-001")

print(jd.required_skills)     # ["python", "django", "docker"]
print(jd.min_experience_years) # 3.0
print(jd.required_seniority)   # "senior"
```

### Score CV vs JD

```python
from src.scoring import CompositeScorer

scorer = CompositeScorer()
scores = scorer.score(cv_data, jd.to_scoring_dict())

# scores keys:
# composite_score, skill_score, experience_score,
# education_score, interview_score, breakdown, has_interview
```

### Quyết định phỏng vấn

```python
from src.decision.interview_decision_engine import (
    InterviewDecisionEngine, MatchScore, PreviousAssessment
)
from datetime import datetime, timedelta

engine = InterviewDecisionEngine()

match_score = MatchScore(
    composite_score=72.0,
    skill_score=68.0,
    experience_score=75.0,
    education_score=80.0,
    missing_required_skills=["kubernetes"],
)

# First-time candidate
decision = engine.decide(match_score)

# Returning candidate
prev = PreviousAssessment(
    assessment_id="assess-001",
    assessed_at=datetime.utcnow() - timedelta(days=240),
    composite_score=70.0,
    cv_skills_snapshot=["python", "django"],
    jd_skills_snapshot=["python", "django", "docker"],
)

decision = engine.decide(
    match_score,
    previous_assessment=prev,
    cv_current_skills=["python", "django", "kubernetes", "terraform"],
    jd_current=jd,
)

print(decision.decision)      # "LIGHT_RESCREEN"
print(decision.confidence)    # 0.73
print(decision.reasoning)     # "Score 72.0/100..."
print(decision.evidence)      # ["+2 new skills", "JD changed 30%", ...]
print(decision.focus_areas)   # ["Verify skills: kubernetes", ...]
```

### Batch Processing

```bash
python scripts/batch_cv_processing.py data/resumes/ \
  --output-md output/markdown \
  --output-json output/json \
  --use-llm
```

### API Server

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Endpoints:

```
POST /api/v1/score/cv                  Score CV vs JD
POST /api/v1/score/batch               Batch scoring
GET  /api/v1/score/{cv_id}?jd_id=...  Latest score
GET  /api/v1/score/{cv_id}/history    Score history
POST /api/v1/rescore                   Trigger rescore
POST /api/v1/cv/{cv_id}/interview-result  Add interview feedback
PUT  /api/v1/job-description/{jd_id}   Update JD (triggers rescore)
GET  /api/v1/ranking?jd_id=...        Rank candidates
POST /api/v1/decision                  Get interview decision
GET  /api/v1/health                    Health check
GET  /api/v1/metrics                   Cache stats, queue length
```

---

## Testing

```bash
# All tests
python -m pytest tests/ -v

# CV parsing (41 tests)
python -m pytest tests/test_cv_parsing.py -v

# Decision engine (30 tests)
python -m pytest tests/test_decision_engine.py -v

# Scoring (15 tests)
python -m pytest tests/test_scoring.py -v

# Schema validation (40 tests)
python -m pytest tests/test_schemas_enhanced.py -v
```

---

## Cấu Trúc Thư Mục

```
cv-intelligence/
├── src/
│   ├── extraction/
│   │   ├── pdf_extractor.py       # 5-step geometric pipeline
│   │   ├── jd_parser.py           # JD parsing (LLM + regex)
│   │   ├── llm_extractor.py       # LLM JSON extraction
│   │   ├── hr_extractor_agent.py  # Orchestrator
│   │   ├── cv_pipeline.py         # Full pipeline
│   │   └── cv_parser.py           # Public API
│   ├── processing/
│   │   └── post_processor.py      # Date norm, exp calc, seniority
│   ├── scoring/
│   │   ├── skill_scorer.py
│   │   ├── experience_scorer.py
│   │   ├── education_scorer.py
│   │   ├── interview_scorer.py
│   │   ├── composite_scorer.py
│   │   ├── matching_engine.py
│   │   └── rescoring_engine.py
│   ├── decision/
│   │   └── interview_decision_engine.py  # Core business logic
│   ├── models/
│   │   ├── domain/                # CandidateProfile, JobDescription, ...
│   │   ├── extraction/            # Word, Line, Block, ExtractionResult
│   │   ├── validation/            # Enums, PhoneValidator, DateValidator
│   │   └── api/                   # Request/Response schemas
│   ├── cache/                     # Redis client, TTL config, cache warmer
│   ├── repository/                # Data access layer (in-memory + MongoDB)
│   ├── retrieval/                 # Cache-first retrieval patterns
│   ├── storage/                   # MongoDB storage layer
│   ├── translation/               # Vi→En translation via Ollama
│   └── api/                       # FastAPI application
├── tests/
│   ├── test_cv_parsing.py         # 41 tests
│   ├── test_decision_engine.py    # 30 tests
│   ├── test_scoring.py            # 15 tests
│   ├── test_schemas_enhanced.py   # 40 tests
│   ├── test_cache.py
│   ├── test_repositories.py
│   └── extraction/
│       ├── test_validation_layer.py
│       └── test_evidence_linker.py
├── scripts/
│   ├── batch_cv_processing.py
│   └── test_5step_pipeline.py
├── output/
│   ├── markdown/
│   └── json/
├── docs/
│   └── CV_PARSING_PIPELINE.md
├── pyproject.toml
└── README.md
```

---

## Performance

| Step | Thời gian | Ghi chú |
|---|---|---|
| PDF geometric extraction | ~100ms | CV 2 trang, PyMuPDF |
| LLM extraction (Qwen 3B) | 2–5s | Local Ollama |
| Post-processing | ~10ms | |
| Scoring (CompositeScorer) | ~5ms | |
| Decision engine | < 1ms | Pure computation |
| **Total với LLM** | **~5–6s** | Per CV |
| **Total không LLM** | **~150ms** | Geometric only |

---

## Known Limitations & Roadmap

**Hiện tại:**
- LLM extraction phụ thuộc Ollama (local) → cần infrastructure
- Không có validation tự động cho decision threshold calibration
- JD parser chưa handle HTML phức tạp với nested tables

**Roadmap:**
- v1.1: API endpoint `/api/v1/decision` với full integration
- v1.2: Threshold calibration từ historical data (recruiter feedback)
- v1.3: Evidence linking — highlight đoạn CV cụ thể hỗ trợ từng decision
- v2.0: Fine-tuned local model cho CV/JD parsing tiếng Việt
- v2.1: Vector search cho candidate similarity (tìm candidates tương tự)

---

## License

MIT License