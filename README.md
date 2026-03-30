# CV Intelligence Platform

> Nền tảng AI giúp nhà tuyển dụng quyết định **có cần phỏng vấn lại ứng viên hay không** — tự động parse CV, so sánh với JD, và đưa ra khuyến nghị có giải thích.

---

## Mục tiêu

Bài toán cốt lõi: *Ứng viên A đã được phỏng vấn 6 tháng trước cho vị trí X. Hôm nay công ty mở thêm vị trí Y tương tự. Có cần phỏng vấn lại không?*

Hệ thống trả lời bằng một trong 5 quyết định có lý giải:

| Quyết định | Ý nghĩa |
|---|---|
| `REUSE` | Dùng kết quả cũ, không cần phỏng vấn lại |
| `RESCORE` | Tự động rescore, không cần tiếp xúc ứng viên |
| `LIGHT_RESCREEN` | Phỏng vấn ngắn (30 phút), chỉ verify một vài điểm |
| `DEEP_INTERVIEW` | Phỏng vấn đầy đủ |
| `REJECT` | Điểm quá thấp, loại ngay |

---

## Kiến trúc Hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                    CV Intelligence Platform                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  PDF Input                    JD Input                        │
│     │                            │                           │
│     ▼                            ▼                           │
│  ┌──────────────┐         ┌──────────────┐                   │
│  │ PDFExtractor │         │  JDParser    │                   │
│  │ (5-Step Geo) │         │  (LLM-based) │                   │
│  └──────┬───────┘         └──────┬───────┘                   │
│         │                        │                           │
│         ▼                        ▼                           │
│  ┌──────────────┐         ┌──────────────┐                   │
│  │HRExtractor   │         │ JobDescription│                  │
│  │  Agent (LLM) │         │   Schema     │                   │
│  └──────┬───────┘         └──────┬───────┘                   │
│         │                        │                           │
│         ▼                        │                           │
│  ┌──────────────┐                │                           │
│  │PostProcessor │                │                           │
│  │(dates, exp,  │                │                           │
│  │ seniority)   │                │                           │
│  └──────┬───────┘                │                           │
│         │                        │                           │
│         ▼                        ▼                           │
│  ┌─────────────────────────────────────┐                     │
│  │        MatchingEngine               │                     │
│  │  (Skill + Exp + Edu + Location)     │                     │
│  └─────────────────┬───────────────────┘                     │
│                    │                                          │
│                    ▼                                          │
│  ┌─────────────────────────────────────┐                     │
│  │      InterviewDecisionEngine        │                     │
│  │  (REUSE/RESCORE/INTERVIEW/REJECT)   │                     │
│  └─────────────────┬───────────────────┘                     │
│                    │                                          │
│                    ▼                                          │
│  ┌─────────────────────────────────────┐                     │
│  │     Decision + Evidence + Reason    │                     │
│  └─────────────────────────────────────┘                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Pipeline Chi Tiết

### Bước 1-4: Geometric PDF Extraction

Module: `src/extraction/pdf_extractor.py`

```
PDF → STEP 1: Word extraction (PyMuPDF, NFC normalize)
    → STEP 2: Line assembly (y-proximity grouping)
    → STEP 3a: Block detection (vertical gap + x-shift)
    → STEP 3b: Table detection (1D gap clustering → Markdown table)
    → STEP 3c: Block classification (5 geometric rules)
    → STEP 4: Reading order assembly → intermediate markdown dump
```

**5 điều kiện để classify `full_width_header`:**
1. Không có word nào khác cùng Y-band trên toàn trang (không chạy song song)
2. `x_span < 60%` chiều rộng trang
3. Khoảng cách trên VÀ dưới > 1.5 × median line height
4. Không kết thúc bằng `.`, `!`, `?`, `,` (nhưng `:` được chấp nhận)
5. `x_center` nằm trong vùng `[10%, 90%]` chiều rộng trang

### Bước 5: LLM Structured Extraction

Module: `src/extraction/llm_extractor.py`

- Model: Qwen2.5-coder:3b-instruct via Ollama (local)
- Schema: Contact, Skills+Evidence, Experience, Projects, Education, Certifications, Languages
- Fallback: raw text nếu LLM không available

### Bước 6: Post-Processing Enrichment

Module: `src/processing/post_processor.py`

- Normalize dates → `YYYY-MM-DD`
- Tính `total_years_experience` từ experience entries
- Assign `seniority_level` từ experience + title keywords

---

## Cài Đặt

### Yêu cầu

- Python 3.10+
- MongoDB (local hoặc Atlas)
- Redis (optional, cho caching)
- [Ollama](https://ollama.ai) (optional, cho LLM extraction)

### Setup

```bash
# Clone repo
git clone <repo-url>
cd cv-intelligence

# Cài dependencies
pip install pymupdf pdfplumber rapidfuzz python-dotenv pydantic fastapi uvicorn

# Ollama (optional)
ollama pull qwen2.5-coder:3b-instruct-q4_K_M
ollama serve

# Config
cp .env.example .env
# Chỉnh sửa .env theo môi trường của bạn
```

### File .env

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=cv_intelligence
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b-instruct-q4_K_M
```

---

## Sử Dụng

### Parse một CV

```python
from src.extraction import CVParser, CVParsingConfig

config = CVParsingConfig(
    use_llm_extraction=True,
    output_markdown_dir="output/markdown",
    output_json_dir="output/json",
)

parser = CVParser(config)
result = parser.parse_cv("data/resume.pdf")

print(f"Experience: {result['total_years_experience']} years")
print(f"Seniority: {result['seniority_level']}")
```

### So sánh CV với JD

```python
from src.scoring import CompositeScorer

scorer = CompositeScorer()
scores = scorer.score(cv_data, jd_data)

print(f"Match: {scores['composite_score']:.1f}/100")
print(f"Skill: {scores['skill_score']:.1f}")
print(f"Experience: {scores['experience_score']:.1f}")
```

### Quyết định phỏng vấn

```python
from src.decision import InterviewDecisionEngine

engine = InterviewDecisionEngine()
decision = engine.decide(
    cv_profile=profile,
    jd=job_description,
    previous_assessment=prev_result,  # None nếu lần đầu
    days_since_last_interview=180,
)

print(f"Decision: {decision.decision}")          # LIGHT_RESCREEN
print(f"Confidence: {decision.confidence:.0%}")  # 78%
print(f"Reason: {decision.reasoning}")
print(f"Evidence: {decision.evidence}")
```

### Batch Processing

```bash
# Process toàn bộ thư mục
python scripts/batch_cv_processing.py data/resumes/ \
  --output-md output/markdown \
  --output-json output/json \
  --use-llm
```

### API Server

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Endpoints
POST /api/v1/score/cv          # Score CV vs JD
POST /api/v1/decision          # Get interview decision
GET  /api/v1/score/{cv_id}     # Get latest score
POST /api/v1/score/batch       # Batch scoring
GET  /api/v1/ranking           # Rank candidates for a JD
GET  /api/v1/health            # Health check
```

---

## Cấu Trúc Thư Mục

```
cv-intelligence/
├── src/
│   ├── extraction/           # CV parsing pipeline
│   │   ├── pdf_extractor.py      # 5-step geometric extraction
│   │   ├── llm_extractor.py      # LLM JSON extraction
│   │   ├── hr_extractor_agent.py # Orchestrator
│   │   ├── cv_pipeline.py        # Full pipeline
│   │   └── cv_parser.py          # Public API
│   ├── processing/           # Post-processing
│   │   └── post_processor.py     # Date norm, exp calc, seniority
│   ├── scoring/              # Scoring engines
│   │   ├── skill_scorer.py
│   │   ├── experience_scorer.py
│   │   ├── education_scorer.py
│   │   ├── interview_scorer.py
│   │   ├── composite_scorer.py
│   │   └── matching_engine.py
│   ├── decision/             # Interview decision engine
│   │   └── interview_decision_engine.py
│   ├── models/               # Pydantic schemas
│   │   ├── domain/               # Business models
│   │   ├── extraction/           # Pipeline models
│   │   ├── validation/           # Validators & enums
│   │   └── api/                  # Request/response models
│   ├── cache/                # Redis caching
│   ├── repository/           # Data access layer
│   ├── retrieval/            # Cache-first retrieval
│   ├── storage/              # MongoDB storage
│   ├── translation/          # Vi→En translation
│   └── api/                  # FastAPI application
├── tests/                    # Test suite (41+ tests)
├── scripts/                  # Utility scripts
├── output/                   # Generated outputs
│   ├── markdown/             # CV markdown dumps
│   └── json/                 # Extracted JSON
├── docs/                     # Documentation
│   └── CV_PARSING_PIPELINE.md
├── pyproject.toml
└── README.md
```

---

## Scoring Model

| Component | Weight | Mô tả |
|---|---|---|
| Skill Match | 30% | Fuzzy matching required + preferred skills |
| Experience | 35% | Years, seniority level, progression |
| Education | 20% | Degree alignment + certifications |
| Interview | 15% | Technical + soft skills + culture fit |

---

## Multilingual Support

- **Tiếng Việt**: Section headers (kinh nghiệm làm việc, học vấn, kỹ năng...)
- **Tiếng Anh**: Full support
- **Bilingual CVs**: Tự detect và process từng section

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# CV parsing tests (41 tests)
python -m pytest tests/test_cv_parsing.py -v

# Scoring tests
python -m pytest tests/test_scoring.py -v

# Schema tests
python -m pytest tests/test_schemas_enhanced.py -v
```

---

## Performance

| Step | Thời gian | Ghi chú |
|---|---|---|
| PDF extraction (5-step) | ~100ms | Typical 2-page CV |
| LLM extraction | 2-5s | Via local Ollama |
| Post-processing | ~10ms | |
| Scoring | ~5ms | |
| **Total (with LLM)** | **~5-6s** | Per CV |
| **Total (no LLM)** | **~150ms** | Geometric only |

---

## Roadmap

- [ ] **v1.1**: JD parsing pipeline (mirror of CV pipeline)
- [ ] **v1.2**: Interview Decision Engine với delta analysis
- [ ] **v1.3**: Evidence linking trong scoring (explainable AI)
- [ ] **v1.4**: Web dashboard cho recruiters
- [ ] **v2.0**: Fine-tuned local model cho CV parsing
- [ ] **v2.1**: Vector search cho candidate similarity

---

## License

MIT License — xem [LICENSE](LICENSE)