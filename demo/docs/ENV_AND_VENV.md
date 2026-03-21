#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CV Intelligence Demo - Environment & .venv Information

## Virtual Environment Setup

The project uses a Python virtual environment located at the project root:

```
.venv/              ← Main virtual environment
├── bin/
│   └── python      ← Use this Python executable
├── lib/source
├── Lib/            ← Windows: site-packages
└── Scripts/        ← Windows: executable scripts
```

### Activating Virtual Environment

**Linux/macOS:**
```bash
source /root/myproject/cv-filtering/.venv/bin/activate
```

**Windows:**
```cmd
.venv\Scripts\activate
```

### Installed Packages

Core dependencies already installed in .venv:
- `pdfplumber` - PDF text extraction
- `python-docx` - DOCX file handling
- `spacy` - NLP and named entity recognition
- `pandas` - Data processing
- `fastapi`, `uvicorn` - API framework
- `streamlit` - Dashboard UI
- `sentence-transformers` - Embeddings (downloading on first use)
- `faiss-cpu` - Vector search
- `scikit-learn`, `numpy` - ML utilities

### Installing Additional Packages

```bash
# Activate venv first
source /root/myproject/cv-filtering/.venv/bin/activate

# Install from requirements
pip install pdfplumber==0.10.3 python-docx==0.8.11

# Or install all from pyproject.toml
pip install -e /root/myproject/cv-filtering
```

### Verifying Installation

```bash
# Check Python version
/root/myproject/cv-filtering/.venv/bin/python --version

# List installed packages
/root/myproject/cv-filtering/.venv/bin/pip list

# Test imports
/root/myproject/cv-filtering/.venv/bin/python -c "import pdfplumber; print('✓ pdfplumber is available')"
```

---

## Project Structure

```
/root/myproject/cv-filtering/          ← Project root
├── .venv/                              ← Virtual environment (Python + packages)
│   ├── bin/
│   │   ├── python
│   │   ├── pip
│   │   └── [other executables]
│   └── lib/
│       └── python3.10/site-packages/   ← Installed packages
│
├── demo/                               ← Main application
│   ├── pyproject.toml                  ← Package config (dev/editable install)
│   ├── requirements.txt                ← Original requirements
│   ├── data/                           ← Input CVs
│   │   ├── build_120/                  ← 120 sample CVs
│   │   ├── sample_1/                   ← 1 sample
│   │   └── test_480/                   ← 480 test CVs
│   ├── output/                         ← Processing results
│   │   ├── build_120_extracted.csv     ← 258+ extracted records
│   │   └── [other outputs]
│   ├── docs/                           ← Documentation
│   │   ├── PROGRESS_REPORT.md          ← Days 1-3 status
│   │   ├── API_DOCUMENTATION.md        ← API usage guide
│   │   ├── DAY1_REPORT.md
│   │   └── DEPLOYMENT_SUMMARY.md
│   ├── scripts/                        ← Utility scripts
│   │   ├── ingest_cvs.py               ← Batch CV ingestion
│   │   ├── demo.py                     ← Integrated demo
│   │   └── sample_data.ps1
│   └── src/                            ← Main application code
│       ├── __init__.py
│       ├── models.py                   ← Data structures
│       ├── handlers/                   ← File format handlers
│       │   ├── __init__.py
│       │   └── input_handlers.py
│       ├── extraction/                 ← Text parsing
│       │   ├── __init__.py
│       │   └── parser.py
│       ├── embeddings/                 ← Vector generation
│       │   ├── __init__.py
│       │   └── embedding_service.py
│       ├── retrieval/                  ← Search indexing
│       │   ├── __init__.py
│       │   └── retrieval_service.py
│       ├── scoring/                    ← Candidate ranking
│       │   ├── __init__.py
│       │   └── scoring_engine.py
│       ├── api/                        ← REST API
│       │   ├── __init__.py
│       │   └── main.py
│       ├── dashboard/                  ← Web UI (Day 4)
│       │   ├── __init__.py
│       │   └── app.py
│       └── recommendations/            ← Matching engine
│           └── __init__.py
│
├── data/                               ← Raw CV dataset (separate from demo)
│   ├── ACCOUNTANT/
│   ├── ADVOCATE/
│   ├── ... [20+ categories]
│   └── TEACHER/
│
├── pyproject.toml                      ← Root package config
├── setup.py                            ← Fallback setup script
└── README.md                           ← This file
```

---

## Quick Commands

### Using Python from .venv

Instead of activating venv, you can call the Python executable directly:

```bash
# Ingest CVs
/root/myproject/cv-filtering/.venv/bin/python demo/scripts/ingest_cvs.py \
  --input demo/data/build_120 \
  --output demo/output/results.csv

# Run demo
/root/myproject/cv-filtering/.venv/bin/python demo/scripts/demo.py

# Start API server
/root/myproject/cv-filtering/.venv/bin/python -m uvicorn \
  -m src.api.main:app --reload --port 8000

# Launch dashboard
/root/myproject/cv-filtering/.venv/bin/streamlit run demo/src/dashboard/app.py
```

### Or activate and use normally

```bash
source /root/myproject/cv-filtering/.venv/bin/activate

python demo/scripts/ingest_cvs.py --input demo/data/build_120
python demo/scripts/demo.py
python -m uvicorn src.api.main:app
streamlit run demo/src/dashboard/app.py

deactivate  # Exit venv when done
```

---

## Environment Variables

Create `.env` file in project root (if needed for future features):

```bash
# demo/.env
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DB_PATH=./data/vector_index
EMBEDDING_CACHE_DIR=./data/embeddings

# API settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Optional: LLM settings for future versions
# OPENAI_API_KEY=sk-...
# LLM_MODEL=gpt-4o
```

Load in Python:
```python
from dotenv import load_dotenv
import os

load_dotenv("demo/.env")
model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
```

---

## Troubleshooting

### Python Not Found
```bash
# Error: python: command not found
# Solution: Use full path to venv Python

# Instead of:
python demo/scripts/demo.py

# Use:
/root/myproject/cv-filtering/.venv/bin/python demo/scripts/demo.py
```

### Module Import Errors
```bash
# Error: ModuleNotFoundError: No module named 'pdfplumber'
# Solution: Ensure venv is active and packages installed

source /root/myproject/cv-filtering/.venv/bin/activate
pip install pdfplumber
```

### Permission Denied on .venv
```bash
# Error: Permission denied: '/root/myproject/cv-filtering/.venv/bin/python'
# Solution: Check permissions

chmod -R 755 /root/myproject/cv-filtering/.venv/bin/
```

---

## Development Workflow

### 1. Activate virtual environment
```bash
source /root/myproject/cv-filtering/.venv/bin/activate
```

### 2. Test imports
```bash
python -c "from src.models import Candidate; print('✓ OK')"
```

### 3. Run ingestion for development
```bash
python demo/scripts/ingest_cvs.py --input demo/data/sample_1 --limit 5
```

### 4. Test full pipeline
```bash
python demo/scripts/demo.py
```

### 5. Start development server
```bash
python -m uvicorn src.api.main:app --reload --port 8000
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 6. Test API endpoints
```bash
# In another terminal:
curl "http://localhost:8000/health"
curl -X POST "http://localhost:8000/search" \
  -d '{"query":"python developer","k":5}'
```

---

## Performance Notes

### Ingest Speed
- Speed: ~2 CVs/second
- 120 CVs takes: ~1 minute
- 2,484 CVs takes: ~20 minutes

### Search Speed
- Single query: <10ms (vector search)
- Hybrid search: <50ms (semantic + keyword)
- Batch: ~5ms per candidate

### Memory Usage
- 120 indexed candidates: ~50MB
- 10,000 candidates: ~5GB (in-memory FAISS)
- With compression: ~500MB

---

## Next Steps

1. **See current status**: `cat demo/docs/PROGRESS_REPORT.md`
2. **Run demo**: `python demo/scripts/demo.py`
3. **Check API docs**: `demo/docs/API_DOCUMENTATION.md`
4. **Start API**: `python -m uvicorn src.api.main:app --reload`
5. **View dashboard** (Day 4): `streamlit run demo/src/dashboard/app.py`

---

## Support & Issues

For detailed information:
- **Progress**: [demo/docs/PROGRESS_REPORT.md](demo/docs/PROGRESS_REPORT.md)
- **API Usage**: [demo/docs/API_DOCUMENTATION.md](demo/docs/API_DOCUMENTATION.md)
- **Deployment**: [demo/docs/DEPLOYMENT_SUMMARY.md](demo/docs/DEPLOYMENT_SUMMARY.md)

---

**Last Updated**: March 20, 2026  
**Status**: Days 1-3 complete, ready for Days 4-5  
**Estimated Completion**: March 24, 2026
