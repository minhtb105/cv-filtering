# 🔧 TROUBLESHOOTING.md - Common Issues & Solutions

**Date**: March 20, 2026  
**Purpose**: Guide for diagnosing and resolving platform issues  
**Target Audience**: Users, developers, support team  

---

## 🆘 Quick Troubleshooting Guide

### Dashboard Won't Load
**Symptoms**: Browser shows blank page or connection error  
**Solutions**:
1. Check if Streamlit is running: `ps aux | grep streamlit`
2. Verify port 8501 is accessible: `curl http://localhost:8501`
3. Clear browser cache: Ctrl+Shift+Delete (Chrome)
4. Check logs: `docker logs cv-dashboard`
5. Restart: `streamlit run src/dashboard/app.py`

### API Not Responding
**Symptoms**: API errors, timeout on requests  
**Solutions**:
1. Check API status: `curl http://localhost:8000/health`
2. Verify it's running: `ps aux | grep uvicorn`
3. Check port availability: `lsof -i :8000`
4. View logs: `docker logs cv-api`
5. Restart: `python -m uvicorn src.api.main:app --reload`

### File Upload Fails
**Symptoms**: "Upload failed" error, "File not supported"  
**Solutions**:
1. Verify file format:
   ```bash
   file your_cv.pdf
   # Expected: "PDF document, version 1.4"
   ```
2. Check file size: Must be < 50MB
3. Try online PDF repair: Best4tools.com
4. Ensure no special characters in filename
5. Check logs for details: `docker logs cv-api`

---

## 📋 Detailed Troubleshooting

### Category A: Data & Ingestion Issues

#### Problem: UNCATEGORIZED showing too high
**Probability**: 40% of uploads  
**Root Cause**: Category not detected from folder structure or file content

**Diagnosis**:
```bash
# Check sample file
head -20 demo/data/build_120/UNCATEGORIZED/sample.pdf | strings

# Check folder structure
ls -la demo/data/ | grep -v UNCATEGORIZED

# Count by category
find demo/data -type d -maxdepth 1 | wc -l
```

**Solutions**:
1. **Option A**: Rename files to include job title
   ```bash
   # Before
   demo/data/UNCATEGORIZED/resume.pdf
   
   # After
   demo/data/ENGINEERING/software_engineer_resume.pdf
   ```

2. **Option B**: Re-run ingestion with regex patterns
   ```python
   # demo/scripts/ingest_cvs.py
   CATEGORY_KEYWORDS = {
       'ENGINEERING': ['engineer', 'developer', 'coder'],
       'FINANCE': ['accountant', 'financial', 'analyst'],
       ...
   }
   
   def detect_category_from_content(text: str) -> str:
       for category, keywords in CATEGORY_KEYWORDS.items():
           if any(kw in text.lower() for kw in keywords):
               return category
       return 'UNCATEGORIZED'
   ```

3. **Option C**: Manual categorization
   ```bash
   # Create category-mapping.csv
   filename,category
   resume_1.pdf,ENGINEERING
   resume_2.pdf,FINANCE
   
   # Apply mapping
   python scripts/apply_category_mapping.py
   ```

#### Problem: CSV has empty cells or missing values
**Root Cause**: PDF parsing failed, data extraction incomplete

**Diagnosis**:
```bash
# Check for null values
python -c "
import pandas as pd
df = pd.read_csv('output.csv')
print(df.isnull().sum())
print(df.describe())
"
```

**Solutions**:
1. Verify PDF is valid:
   ```bash
   pdftotext resume.pdf - | head -50
   ```

2. Use alternative PDF library:
   ```python
   # Try PyPDF2 if pdfplumber fails
   import PyPDF2
   
   with open('resume.pdf', 'rb') as f:
       reader = PyPDF2.PdfReader(f)
       text = ""
       for page in reader.pages:
           text += page.extract_text()
   ```

3. Check extraction settings:
   ```python
   # demo/src/extraction/parser.py
   
   # Adjust parameters for difficult PDFs
   EXTRACTION_CONFIG = {
       'layout_aware': True,  # Preserve layout
       'char_margin': 2,      # Character spacing
       'word_margin': 0.1,    # Word spacing
   }
   ```

### Category B: Performance Issues

#### Problem: Dashboard slow (>3 seconds to load)
**Root Cause**: FAISS index too large, or embedding computation slow

**Diagnosis**:
```bash
# Measure dashboard load time
curl -w "Time: %{time_total}s\n" http://localhost:8501

# Profile Python code
python -m cProfile -s cumulative -o profile.stats src/dashboard/app.py

# View results
python -m pstats profile.stats
```

**Solutions**:
1. **Compress FAISS index**:
   ```python
   # Before: IndexFlatL2 (full index)
   # After: IndexIVFFlat (compressed)
   
   import faiss
   
   # Load full index
   index = faiss.read_index('faiss_index.bin')
   quantizer = faiss.IndexFlatL2(index.d)
   
   # Create compressed version
   compressed_index = faiss.IndexIVFFlat(quantizer, index.d, nlist=100)
   compressed_index.train(data)
   compressed_index.add(data)
   
   faiss.write_index(compressed_index, 'faiss_index_compressed.bin')
   ```

2. **Reduce embedding batch size** (if memory issue):
   ```python
   # demo/src/embeddings/embedding_service.py
   EMBEDDING_BATCH_SIZE = 32  # Reduce from 64
   ```

3. **Enable caching**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=1000)
   def cache_search_results(query: str, category: str = None):
       return perform_search(query, category)
   ```

4. **Pre-load models**:
   ```python
   # Load on startup instead of first use
   if __name__ == "__main__":
       from src.embeddings.embedding_service import EmbeddingService
       embedding_service = EmbeddingService()
       embedding_service.model  # Force load
   ```

#### Problem: Search returns no results (< 10ms too fast?)
**Root Cause**: FAISS index not loaded, empty results, threshold too high

**Diagnosis**:
```bash
# Test search directly
python -c "
from src.retrieval.retrieval_service import RetrievalService
service = RetrievalService()
results = service.search('python engineer', top_k=10)
print(f'Found {len(results)} results')
"

# Check index size
ls -lh faiss_index.bin
# Should be > 100MB for 1000+ embeddings
```

**Solutions**:
1. Rebuild index:
   ```bash
   python -c "
   from src.retrieval.retrieval_service import RetrievalService
   service = RetrievalService()
   service.rebuild_index()
   print('Index rebuilt')
   "
   ```

2. Lower similarity threshold:
   ```python
   # demo/src/retrieval/retrieval_service.py
   
   MIN_SIMILARITY_SCORE = 0.3  # Lower from 0.5
   results = [r for r in results if r['score'] > MIN_SIMILARITY_SCORE]
   ```

3. Verify index exists:
   ```bash
   find . -name "*.bin" -o -name "faiss*"
   ls -la demo/src/retrieval/cache/
   ```

### Category C: API Issues

#### Problem: /api/score endpoint timeout (>30s)
**Root Cause**: Scoring 100+ candidates, slow embeddings

**Diagnosis**:
```bash
# Test with small dataset
curl -X POST http://localhost:8000/api/score \
  -H "Content-Type: application/json" \
  -d '{"job_id": "test", "candidates": ["cv1.pdf", "cv2.pdf"]}'

# Check API logs
docker logs cv-api | grep "score"
```

**Solutions**:
1. Increase batch size for embeddings:
   ```python
   # demo/src/embeddings/embedding_service.py
   EMBEDDING_BATCH_SIZE = 128  # From 64
   ```

2. Limit candidates per request:
   ```python
   # demo/src/api/main.py
   
   MAX_SCORING_CANDIDATES = 50  # Limit per request
   
   @app.post("/api/score")
   def score_candidates(request: ScoringRequest):
       if len(request.candidates) > MAX_SCORING_CANDIDATES:
           raise HTTPException(
               status_code=400,
               detail=f"Max {MAX_SCORING_CANDIDATES} candidates per request"
           )
   ```

3. Use async processing:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   def score_batch_async(candidates: List[str]):
       with ThreadPoolExecutor(max_workers=4) as executor:
           results = executor.map(score_single, candidates)
       return list(results)
   ```

4. Increase timeout in client:
   ```python
   import requests
   
   response = requests.post(
       'http://localhost:8000/api/score',
       json=payload,
       timeout=120  # 120 seconds
   )
   ```

#### Problem: /api/extract returns partial text
**Root Cause**: PDF parsing incomplete, image PDF, scanned document

**Diagnosis**:
```bash
# Test extraction
curl -X POST http://localhost:8000/api/extract \
  -F "file=@resume.pdf" 2>&1 | head -100

# Check if PDF is image-based
pdfimages -list resume.pdf | head -5
```

**Solutions**:
1. Use OCR for scanned PDFs:
   ```python
   import pytesseract
   from pdf2image import convert_from_path
   
   def extract_from_scanned_pdf(pdf_path: str) -> str:
       images = convert_from_path(pdf_path)
       text = ""
       for image in images:
           text += pytesseract.image_to_string(image)
       return text
   ```

2. Try alternative library:
   ```python
   # If pdfplumber fails, try PyPDF2
   import PyPDF2
   
   with open(pdf_path, 'rb') as f:
       reader = PyPDF2.PdfReader(f)
       text = '\n'.join(p.extract_text() for p in reader.pages)
   ```

3. Manual review:
   ```bash
   # View PDF in text editor
   pdftotext resume.pdf resume.txt
   less resume.txt
   ```

### Category D: Database Issues

#### Problem: CSV export empty or incomplete
**Root Cause**: Database connection failed, query returned 0 rows

**Diagnosis**:
```bash
# Check CSV size
ls -lh *.csv

# Count rows
wc -l output.csv

# Check contents
head -20 output.csv
tail -20 output.csv
```

**Solutions**:
1. Verify data exists:
   ```python
   import pandas as pd
   
   df = pd.read_csv('original_data.csv')
   print(f"Original: {len(df)} rows")
   
   df_output = pd.read_csv('output.csv')
   print(f"Output: {len(df_output)} rows")
   ```

2. Re-export with logging:
   ```python
   def export_with_logging(query_result):
       logger = logging.getLogger(__name__)
       logger.info(f"Exporting {len(query_result)} rows")
       
       df = pd.DataFrame(query_result)
       df.to_csv('output.csv', index=False)
       
       logger.info(f"Exported successfully")
   ```

3. Check file permissions:
   ```bash
   chmod 644 output.csv
   ls -la output.csv
   ```

### Category E: Dependency Issues

#### Problem: ImportError on startup
**Symptoms**: `ModuleNotFoundError: No module named 'X'`

**Diagnosis**:
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# List installed packages
pip list | grep -i sentence

# Try import in isolation
python -c "from sentence_transformers import SentenceTransformer"
```

**Solutions**:
1. Install missing package:
   ```bash
   pip install sentence-transformers
   ```

2. Reinstall dependencies:
   ```bash
   pip install --upgrade -r demo/requirements.txt
   ```

3. Use fresh virtual environment:
   ```bash
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   pip install -r demo/requirements.txt
   ```

4. Check Python version:
   ```bash
   python --version  # Should be 3.10+
   ```

#### Problem: CUDA out of memory
**Symptoms**: `RuntimeError: CUDA out of memory`

**Diagnosis**:
```bash
# Check GPU memory
nvidia-smi

# Monitor during run
watch nvidia-smi
```

**Solutions**:
1. Clear cache:
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

2. Reduce batch size:
   ```python
   # demo/src/embeddings/embedding_service.py
   EMBEDDING_BATCH_SIZE = 16  # Reduce from 64
   ```

3. Disable GPU (use CPU):
   ```python
   import os
   os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
   ```

4. Allocate more GPU memory:
   ```python
   gpus = tf.config.list_physical_devices('GPU')
   for gpu in gpus:
       tf.config.experimental.set_memory_growth(gpu, True)
   ```

---

## 📊 Debugging Tools & Commands

### Python Debugging

```bash
# Interactive debugger
python -m pdb your_script.py

# Breakpoint in code
breakpoint()  # Python 3.7+

# Post-mortem debugging
python -c "import traceback; exec(open('script.py').read())"
```

### Log Analysis

```bash
# View error logs
tail -f demo/logs/error.log

# Search for specific errors
grep "traceback" demo/logs/*.log

# Count error types
grep "Error\|Exception" demo/logs/*.log | cut -d: -f2 | sort | uniq -c

# Real-time monitoring
watch tail -100 demo/logs/app.log
```

### Performance Profiling

```bash
# Memory profiling
python -m memory_profiler src/dashboard/app.py

# CPU profiling
python -m timeit "import src.embeddings"

# Line profiler
pip install line_profiler
kernprof -l -v src/dashboard/app.py
```

### Network Debugging

```bash
# Test connectivity
curl -v http://localhost:8000/health

# Trace requests
curl -w "@curl-format.txt" http://localhost:8000/health

# Monitor network traffic
ngrep -d any 'HTTP' 'port 8000'

# Check ports
netstat -tlnp | grep 8000
ss -tlnp | grep 8000
```

---

## 🧪 Health Check Commands

Run these regularly to ensure system health:

```bash
#!/bin/bash
# health_check.sh

echo "=== System Status ==="
ps aux | grep -E "uvicorn|streamlit" | grep -v grep

echo "\n=== API Health ==="
curl -s http://localhost:8000/health | jq .

echo "\n=== Dashboard Health ==="
curl -s http://localhost:8501 --max-time 5 > /dev/null && echo "✓ Running" || echo "✗ Down"

echo "\n=== Disk Space ==="
df -h . | tail -1

echo "\n=== Memory Usage ==="
free -h | grep Mem

echo "\n=== Docker Status ==="
docker-compose ps

echo "\n=== Error Count (last hour) ==="
grep -c "ERROR" demo/logs/error.log || echo "0"
```

Run with: `bash health_check.sh`

---

## 📞 Getting Help

### Before Reporting an Issue

1. **Check this document** for known issues
2. **Collect system info**:
   ```bash
   python --version
   pip list | head -20
   uname -a
   docker --version
   ```

3. **Gather error context**:
   ```bash
   # Last 50 lines of errors
   tail -50 demo/logs/error.log
   
   # Full traceback
   docker logs cv-api 2>&1 | tail -100
   ```

4. **Test in isolation**:
   ```bash
   # Run specific component
   python -c "from src.extraction.parser import CVParser; p = CVParser(); print('OK')"
   ```

### Reporting Issues

**Format**: 
```markdown
## Issue Title

**Environment**:
- OS: Ubuntu 20.04
- Python: 3.10.4
- Docker: Yes

**Steps to Reproduce**:
1. Upload file X
2. Click button Y
3. Error appears

**Expected Behavior**:
Results should load

**Actual Behavior**:
Error: Something went wrong

**Logs**:
[Paste relevant logs]

**Attempted Fixes**:
- Restarted dashboard
- Cleared cache
```

**Submit to**: GitHub Issues → [project-name]/issues

---

## 🔮 Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `CUDA out of memory` | GPU overloaded | Reduce batch size, use CPU |
| `No module named 'X'` | Dependency missing | `pip install X` |
| `Connection refused` | Service down | Check `docker ps`, restart |
| `File not found` | Path incorrect | Use absolute paths, check `ls` |
| `Permission denied` | File permissions | `chmod 755 file` |
| `Port already in use` | Service running twice | `lsof -i :8000` |
| `Invalid file format` | Unsupported file | Use PDF/DOCX only |
| `Timeout error` | Request too slow | Increase timeout, optimize |

---

## 📚 Additional Resources

- **Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Features**: See [FEATURE_ROADMAP.md](FEATURE_ROADMAP.md)
- **Format Support**: See [ADD_NEW_FORMAT.md](ADD_NEW_FORMAT.md)
- **Source Code**: [demo/src/](demo/src/)
- **Logs**: [demo/logs/](demo/logs/)

---

**Document Version**: 1.0  
**Last Updated**: March 20, 2026  
**Status**: Ready for Use
