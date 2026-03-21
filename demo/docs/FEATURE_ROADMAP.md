# 🗺️ FEATURE_ROADMAP.md - CV Intelligence Platform Roadmap

**Date**: March 20, 2026  
**Purpose**: Vision for future features and capabilities  
**Target Audience**: Product managers, stakeholders, developers  

---

## 📊 Roadmap Overview

```
2025:
Q1: Core Platform ✅
    └─ PDF/DOCX parsing ✅
    └─ Basic embeddings ✅
    └─ Search & scoring ✅

Q2: MVP Enhancement ✅
    └─ Streamlit dashboard ✅
    └─ FastAPI REST API ✅
    └─ Category detection ✅
    └─ Job matching scoring ✅

Q3: Production Ready ✅
    └─ CSV export ✅
    └─ Performance optimization ✅
    └─ Error handling ✅
    └─ Documentation ✅

2026:
Q1: Advanced Format Support 🔄
    └─ Image OCR (PNG, JPG)
    └─ Email parsing (EML, MSG)
    └─ Legacy formats (DOC, RTF, ODP)

Q2: AI Enhancement 📅
    └─ Fine-tuned embedding models
    └─ Custom scoring weights
    └─ Resume summarization

Q3: Enterprise Features 📅
    └─ Multi-user authentication
    └─ Role-based access control
    └─ Audit logging

Q4: Intelligence & Analytics 📅
    └─ Predictive hiring insights
    └─ Candidate pipeline analytics
    └─ Skills gap analysis

2027:
Q1+: Vision AI & Advanced Features 🎯
    └─ Video interview analysis
    └─ Skill validation testing
    └─ Salary benchmarking
```

---

## 🎯 Q1 2026: Advanced Format Support

### Objective
Expand CV parsing to handle non-traditional document formats.

### Features

#### 1.1 Image-Based CV Parsing (OCR)
**Priority**: High | **Effort**: Medium | **Status**: Planned

Automatically extract text from image-formatted CVs using Tesseract OCR.

**Requirements**:
- Support PNG, JPG, JPEG formats
- Automatic image preprocessing (deskew, denoise)
- High accuracy (>90% character recognition)
- Performance: <3s per image

**Implementation**:
```python
class ImageOCRHandler:
    """OCR-based resume extraction"""
    def extract_text(self, file_path: str) -> str:
        # Preprocess image
        image = preprocess_image(file_path)
        
        # Extract text
        text = pytesseract.image_to_string(image)
        
        # Post-process
        text = clean_ocr_text(text)
        
        return text
    
    def batch_extract(self, file_paths: List[str]) -> Dict[str, str]:
        """Parallel OCR processing"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = executor.map(self.extract_text, file_paths)
        return dict(zip(file_paths, results))
```

**Acceptance Criteria**:
- [ ] OCR handler created and integrated
- [ ] Character accuracy > 90%
- [ ] Processing time < 3s per image
- [ ] Handles rotated/skewed images
- [ ] Error handling for corrupt images
- [ ] Performance benchmarks documented

**Dependencies**:
- `pytesseract >= 0.3.10`
- `Pillow >= 9.0.0`
- `OpenCV >= 4.5.0` (for preprocessing)
- Tesseract-OCR system package

#### 1.2 Email Resume Parsing
**Priority**: Medium | **Effort**: Low | **Status**: Planned

Extract CV text from emailed resumes (EML, MSG formats).

**Implementation**:
```python
class EmailHandler:
    """Extract resume from email attachments"""
    def extract_from_attachment(self, email_path: str) -> str:
        msg = email.message_from_file(open(email_path))
        
        for part in msg.walk():
            # Find attached documents
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                
                if filename.endswith(('.pdf', '.docx')):
                    # Extract from attachment
                    text = extract_from_bytes(part.get_payload())
                    return text
        
        # Fall back to email body
        return msg.get_payload(decode=True).decode('utf-8')
```

#### 1.3 Legacy Document Formats
**Priority**: Medium | **Effort**: Medium | **Status**: Planned

Support older office formats: DOC (Word 97-2003), RTF, ODP.

**Handlers**:
- DOCHandler: Word 97-2003 using `python-docx2pdf`
- RTFHandler: Rich Text Format using `striprtf`
- ODPHandler: OpenDocument using `odfpy`

**Implementation Timeline**:
- Month 1: OCR image parsing (Week 1-2), Email parsing (Week 3)
- Month 2: Legacy formats (Week 1-2), Integration & testing (Week 3-4)
- Month 3: Performance optimization, launch

---

## 🤖 Q2 2026: AI Enhancement

### Objective
Improve matching quality with fine-tuned models and advanced scoring.

### Features

#### 2.1 Fine-Tuned Embedding Models
**Priority**: High | **Effort**: High | **Status**: Planned

Train custom embeddings on HR domain data for better semantic understanding.

**Current**: `sentence-transformers/all-MiniLM-L6-v2` (generic)  
**Target**: Custom model trained on 10K HR job-CV pair annotations

**Process**:
1. Collect training pairs (job descriptions ↔ CVs)
2. Create similarity labels (0-1 scale)
3. Fine-tune using Siamese Loss
4. Benchmark against baseline
5. Deploy and A/B test

**Expected Improvements**:
- Relevance precision: +15%
- Edge case handling: +25%
- Inference speed: +10%

**Code Structure**:
```python
from sentence_transformers import SentenceTransformer, InputExample, losses

# Load base model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Prepare training data
train_examples = [
    InputExample(texts=['job_desc_1', 'cv_1'], label=0.95),
    InputExample(texts=['job_desc_2', 'cv_2'], label=0.45),
    ...
]

# Fine-tune
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
train_loss = losses.CosineSimilarityLoss(model)

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=10,
    warmup_steps=1000,
    show_progress_bar=True
)

model.save('models/cv-domain-fine-tuned')
```

#### 2.2 Custom Scoring Weights
**Priority**: Medium | **Effort**: Medium | **Status**: Planned

Allow HR teams to customize how candidates are scored based on priorities.

**Weight Categories**:
- Experience relevance: 30-50%
- Skills match: 20-40%
- Location: 0-20%
- Education: 5-20%
- Seniority alignment: 10-30%

**UI/API**:
```python
@app.post("/api/scoring/weights")
def set_custom_weights(
    user_id: str,
    job_id: str,
    weights: ScoringWeights
) -> Dict[str, float]:
    """
    Custom weights for a specific job
    {
        "experience_relevance": 0.40,
        "skills_match": 0.35,
        "location_match": 0.10,
        "education_match": 0.10,
        "seniority_alignment": 0.05
    }
    """
    # Store weights
    db.save_weights(user_id, job_id, weights)
    
    # Recalculate scores for all candidates
    recalculate_scores(job_id, weights)
    
    return weights
```

**Dashboard Feature**:
```
┌─────────────────────────────────┐
│ Customize Scoring Weights       │
├─────────────────────────────────┤
│ Experience Relevance: ▒░░ 40%   │
│ Skills Match: ▒▒▒░░░░ 35%       │
│ Location Match: ▒░░░░░░░░░ 10%  │
│ Education Match: ▒░░░░░░░░░ 10% │
│ Seniority Alignment: ░░░░░░░░░ 5%│
│                                 │
│ [Save & Recalculate]           │
└─────────────────────────────────┘
```

#### 2.3 Resume Summarization
**Priority**: Medium | **Effort**: Medium | **Status**: Planned

Generate executive summaries of CVs using language models.

**Features**:
- 50-word summary
- Key highlights extraction
- Skills quick-view
- Career trajectory

**Implementation**:
```python
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_cv(cv_text: str) -> Dict[str, str]:
    """Generate CV summary"""
    
    # Split into chunks
    chunks = chunk_text(cv_text, chunk_size=512)
    
    # Summarize each section
    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=50, min_length=30)
        summaries.append(summary[0]['summary_text'])
    
    # Combine
    executive_summary = " ".join(summaries)
    
    # Extract highlights
    highlights = extract_highlights(cv_text)
    
    return {
        "summary": executive_summary,
        "highlights": highlights,
        "top_skills": extract_top_skills(cv_text, n=5),
        "career_trajectory": analyze_career_progression(cv_text)
    }
```

**Timeline**:
- Month 1: Fine-tune embedding model (Week 1-3)
- Month 2: Custom weights system (Week 1-2), Resume summarization (Week 3-4)
- Month 3: Integration, testing, launch

---

## 🔐 Q3 2026: Enterprise Features

### Objective
Add multi-user capabilities and enterprise-grade security.

### Features

#### 3.1 Multi-User Authentication
**Priority**: High | **Effort**: Medium | **Status**: Planned

Support different user accounts, authentication, and session management.

**Methods**:
- Email/password with hashing (bcrypt)
- OAuth2 integration (Google, Microsoft)
- SAML for enterprise SSO
- MFA support (TOTP)

**Implementation**:
```python
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

auth_backend = JWTAuthentication(
    secret=settings.JWT_SECRET,
    lifetime_seconds=3600 * 24,  # 24 hours
)

fastapi_users = FastAPIUsers(
    UserManager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(),
    prefix="/api/auth",
    tags=["auth"],
)

# Protected endpoint
@app.get("/api/protected")
async def protected_route(user: User = Depends(fastapi_users.get_current_user)):
    return {"user": user.email}
```

#### 3.2 Role-Based Access Control (RBAC)
**Priority**: High | **Effort**: Medium | **Status**: Planned

Different user roles with specific permissions.

**Roles**:
- **Admin**: Full system access, user management, settings
- **Recruiter**: Upload CVs, view results, export data
- **Hiring Manager**: View rankings, provide feedback
- **Candidate**: View own profile, apply for jobs
- **Analyst**: View dashboards, generate reports

**Permission Matrix**:
```
Action                 | Admin | Recruiter | Manager | Analyst | Candidate
─────────────────────────────────────────────────────────────────────────────
Upload CVs             | ✓     | ✓         | ✗       | ✗       | ✗
Search Candidates      | ✓     | ✓         | ✓       | ✓       | ✗
View Rankings          | ✓     | ✓         | ✓       | ✓       | ✗
Export Data            | ✓     | ✓         | ✗       | ✓       | ✗
Manage Users           | ✓     | ✗         | ✗       | ✗       | ✗
View Reports           | ✓     | ✓         | ✓       | ✓       | ✗
```

**Implementation**:
```python
from enum import Enum
from functools import wraps

class Role(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    ANALYST = "analyst"
    CANDIDATE = "candidate"

def require_role(*required_roles: Role):
    """Decorator for role-based access"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = kwargs.get('user')
            
            if user.role not in required_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Requires one of: {required_roles}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

@app.post("/api/cvs/upload")
@require_role(Role.ADMIN, Role.RECRUITER)
async def upload_cvs(
    files: List[UploadFile],
    user: User = Depends(get_current_user)
):
    """Only admin and recruiter can upload"""
    ...
```

#### 3.3 Audit Logging
**Priority**: High | **Effort**: Low | **Status**: Planned

Track all user actions for security and compliance.

**Logged Events**:
- User login/logout
- CV uploads
- Search queries
- Data exports
- Settings changes
- Account actions

**Implementation**:
```python
from datetime import datetime
from enum import Enum

class AuditAction(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    UPLOAD_CV = "upload_cv"
    SEARCH = "search"
    EXPORT = "export"
    DELETE = "delete"
    UPDATE_SETTINGS = "update_settings"

class AuditLog(BaseModel):
    user_id: str
    action: AuditAction
    resource_id: str = None
    timestamp: datetime
    ip_address: str
    user_agent: str
    details: Dict = {}
    status: str = "success"
    error_message: str = None

def log_audit(action: AuditAction, user: User, **details):
    """Log user action"""
    log_entry = AuditLog(
        user_id=user.id,
        action=action,
        timestamp=datetime.utcnow(),
        ip_address=request.client.host,
        user_agent=request.headers.get('user-agent'),
        details=details
    )
    
    db.save_audit_log(log_entry)

# Usage
@app.post("/api/cvs/upload")
async def upload_cvs(user: User = Depends(get_current_user)):
    # ... upload logic ...
    log_audit(AuditAction.UPLOAD_CV, user, count=5)
```

**Timeline**:
- Month 1: Multi-user auth system (Week 1-2)
- Month 2: RBAC implementation (Week 1-2), Audit logging (Week 3)
- Month 3: Testing, security review, launch

---

## 📈 Q4 2026: Intelligence & Analytics

### Objective
Provide data-driven hiring insights and analytics.

### Features

#### 4.1 Predictive Hiring Insights
**Priority**: High | **Effort**: High | **Status**: Planned

ML models to predict hiring success, retention, and performance.

**Predictions**:
- Likelihood of offer acceptance
- 12-month retention probability
- Performance rating (if hired)
- Time-to-productivity

**Data Requirements**:
- Historical hires (500+)
- Employment outcomes
- Performance reviews
- Retention data

**Implementation**:
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class HiringSuccessPredictor:
    """Predict hiring outcomes"""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.scaler = StandardScaler()
        
        if model_path:
            self.load_model(model_path)
    
    def train(self, X_train, y_train):
        """Train on historical data"""
        X_scaled = self.scaler.fit_transform(X_train)
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            random_state=42
        )
        
        self.model.fit(X_scaled, y_train)
    
    def predict(self, cv_data: Dict) -> Dict[str, float]:
        """
        Predict outcomes for a candidate
        
        Returns:
        {
            "offer_acceptance_prob": 0.78,
            "retention_12mo_prob": 0.85,
            "performance_rating": 3.5,
            "time_to_productivity_days": 45
        }
        """
        # Extract features from CV
        features = extract_features(cv_data)
        
        # Predict
        X_scaled = self.scaler.transform([features])[0]
        prediction = self.model.predict_proba(X_scaled)
        
        return {
            "offer_acceptance_prob": float(prediction[1]),
            "retention_12mo_prob": self._predict_retention(features),
            "performance_rating": self._predict_performance(features),
            "time_to_productivity_days": self._predict_ramp_time(features)
        }
```

#### 4.2 Candidate Pipeline Analytics
**Priority**: Medium | **Effort**: Medium | **Status**: Planned

Dashboard showing hiring funnel, conversion rates, and time-to-hire metrics.

**Metrics**:
- Application → Interview conversion
- Interview → Offer conversion
- Offer → Acceptance rate
- Average time-to-hire
- Cost-per-hire
- Hiring by source
- Candidate velocity

**Visualizations**:
```python
# Using plotly
import plotly.graph_objects as go

def create_hiring_funnel():
    """Candidate pipeline visualization"""
    stages = ['Applied', 'Screened', 'Interviewed', 'Offered', 'Hired']
    counts = [100, 75, 30, 12, 8]
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=counts,
        text=[f"{c} candidates" for c in counts],
        textposition="inside",
        textinfo="text+percent previous"
    ))
    
    return fig
```

#### 4.3 Skills Gap Analysis
**Priority**: Medium | **Effort**: Medium | **Status**: Planned

Identify skills gaps and training needs in candidate pool.

**Features**:
- Required vs. available skills
- Training recommendations
- Skill proficiency heatmaps
- Upskilling costs/timelines

**Implementation**:
```python
def analyze_skills_gap(job_id: str) -> Dict:
    """
    Analyze gap between job requirements and candidate skills
    
    Returns:
    {
        "required_skills": ["Python", "Machine Learning", ...],
        "available_skills": ["Python", "Data Analysis", ...],
        "gaps": [
            {
                "skill": "Machine Learning",
                "demand": 85,
                "supply": 45,
                "gap": 40,
                "training_time_weeks": 12,
                "candidates_capable": 23
            },
            ...
        ]
    }
    """
    
    # Get job requirements
    job = db.get_job(job_id)
    required_skills = extract_skills(job.description)
    
    # Get candidate skills
    candidates = db.get_candidates_for_job(job_id)
    all_skills = aggregate_candidate_skills(candidates)
    
    # Calculate gaps
    gaps = []
    for skill in required_skills:
        candidates_with_skill = count_candidates_with_skill(candidates, skill)
        gap = {
            "skill": skill,
            "demand": required_skills[skill],
            "supply": candidates_with_skill / len(candidates) * 100,
            "gap": required_skills[skill] - (candidates_with_skill / len(candidates) * 100)
        }
        gaps.append(gap)
    
    return {
        "required_skills": list(required_skills.keys()),
        "available_skills": list(set(all_skills.keys())),
        "gaps": sorted(gaps, key=lambda x: x['gap'], reverse=True)
    }
```

**Timeline**:
- Month 1: Hiring success prediction (Week 1-3)
- Month 2: Pipeline analytics dashboard (Week 1-2), Skills gap analysis (Week 3-4)
- Month 3: Integration, visualization refinement, launch

---

## 🚀 2027: Vision AI & Advanced Features

### Objective
Introduce cutting-edge AI capabilities for comprehensive candidate evaluation.

### Features

#### Next-Generation Capabilities
- 🎥 **Video Interview Analysis**: Analyze speech, tone, body language for fit assessment
- ✅ **Skill Validation Testing**: Automated coding/skills challenges with evaluation
- 💰 **Salary Benchmarking**: Market rates for skills/locations/roles
- 🌐 **Global Hiring**: Multi-language support, international credentials mapping
- 🔮 **Career Trajectory Prediction**: Where candidates are headed
- 👥 **Team Fit Analysis**: Personality compatibility, team dynamics
- 🎓 **Credential Verification**: Auto-verify degrees, certifications
- 📊 **Market Intelligence**: Industry trends, skill demands, salary ranges

---

## 📊 Success Metrics by Phase

### Q1 2026 (Format Support)
- [ ] Support 4+ document formats
- [ ] OCR accuracy > 90%
- [ ] Processing speed < 3s per document
- [ ] Adoption rate on 50% of uploads

### Q2 2026 (AI Enhancement)
- [ ] Fine-tuned model precision +15%
- [ ] 80% of jobs using custom weights
- [ ] Summary generation accuracy > 85%
- [ ] User satisfaction +20%

### Q3 2026 (Enterprise)
- [ ] 10+ concurrent users supported
- [ ] 99.9% uptime
- [ ] Audit trail 100% complete
- [ ] SOC2 Type II compliant

### Q4 2026 (Analytics)
- [ ] Predictive models accuracy > 75%
- [ ] 30+ analytical insights per job
- [ ] Time-to-hire reduced by 25%
- [ ] Offer acceptance rate improved

---

## 💰 Investment Roadmap

| Phase | Quarter | Dev Days | Cost | ROI Target |
|-------|---------|----------|------|-----------|
| Format Support | Q1 '26 | 40 | $12K | 15% adoption |
| AI Enhancement | Q2 '26 | 60 | $18K | 20% UX improvement |
| Enterprise | Q3 '26 | 50 | $15K | $50K ARR |
| Analytics | Q4 '26 | 80 | $24K | $100K ARR |
| **Total 2026** | - | 230 | $69K | $150K+ ARR |

---

## 🎯 Strategic Priorities

**2026 Focus Areas** (in order):
1. **Format Expansion** - Increase data accessibility
2. **AI Quality** - Better matching and predictions
3. **Enterprise Scale** - Support business growth
4. **Data Intelligence** - Enable strategic decisions

**Not Planned for 2026**:
- Mobile app (see v2.0)
- Video interview creation tool
- Third-party integrations (HRMs, ATS)
- Compliance automation (GDPR, CCPA)
- Blockchain credentials

---

## 📞 Feedback & Contributions

**Request a Feature**:
1. Create GitHub issue with `[FEATURE REQUEST]` prefix
2. Describe problem statement
3. Explain expected outcome
4. Vote with 👍 reactions

**Contribute**:
1. Fork repository
2. Create feature branch
3. Submit pull request
4. Code review & merge

---

**Document Version**: 1.0  
**Last Updated**: March 20, 2026  
**Next Review**: June 2026
