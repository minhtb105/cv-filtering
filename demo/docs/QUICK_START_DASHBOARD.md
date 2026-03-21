# 🚀 Quick Start - Dashboard Launch

## One-Command Launch

```bash
cd /root/myproject/cv-filtering/demo && bash scripts/run_dashboard.sh
```

## Open in Browser

```
http://localhost:8501
```

---

## 4 Pages Overview (60 seconds)

### Page 1: 🔍 Search
- Type a skill or job title → See matching candidates
- Click a name for detailed profile
- Example: "Python developer"

### Page 2: ⭐ Score  
- Click a job template (Senior Python, Java, Sales)
- OR paste your own job description
- Click "Score All Candidates"
- See ranked list and breakdown chart

### Page 3: 👥 Similar
- Pick a candidate you like
- See 10 similar candidates
- Use for backup hiring plans

### Page 4: 📈 Metrics
- View system statistics
- See skill trends
- Check data distribution

---

## Key Numbers

- **258 candidates indexed** ✓
- **30+ unique job categories** ✓  
- **2,000+ unique skills** ✓
- **Average experience: 4-5 years** ✓
- **Search speed: <500ms** ✓

---

## 3-Minute Demo Workflow

### Step 1: Search (1 min)
```
Page: 🔍 Search CVs
Query: "Python"
→ See all Python developers
→ Click top candidate
→ View their full skills
```

### Step 2: Score (1 min)
```
Page: ⭐ Score Job
Click: "📋 Senior Python"
→ System ranks all candidates
→ View top 3 with scores
→ See radar breakdown
```

### Step 3: Recommend (1 min)
```
Page: 👥 Recommendations  
Select: Top candidate from Step 2
→ See 10 similar candidates
→ Review alternatives
→ Compare experience levels
```

---

## Requirements

✓ Python 3.10+  
✓ Virtual environment active  
✓ Streamlit installed (pip install streamlit)  
✓ CSV file at: demo/output/build_120_extracted.csv  

---

## Keyboard Shortcuts in Dashboard

| Action | Shortcut |
|--------|----------|
| Search within page | Ctrl+F |
| Refresh | F5 |
| Go home | Alt+Home |
| Stop app | Ctrl+C (in terminal) |

---

## Common Questions

**Q: Where's my data?**  
A: All from `demo/output/build_120_extracted.csv` (258 candidates)

**Q: Can I add more CVs?**  
A: Yes! Run `python demo/scripts/ingest_cvs.py --input data/build_120 --output output/new_candidates.csv`

**Q: How do I customize scoring?**  
A: Edit weights in `demo/src/scoring/scoring_engine.py` and restart

**Q: Can I export results?**  
A: Not yet (v0.1), manual copy from tables for now

---

## Troubleshooting

**Dashboard won't start?**
```bash
# Check virtualenv
source /root/myproject/cv-filtering/.venv/bin/activate

# Run directly
streamlit run demo/src/dashboard/app.py
```

**No candidates showing?**
```bash
# Verify CSV exists
ls -lh demo/output/build_120_extracted.csv

# Check CSV format
head -5 demo/output/build_120_extracted.csv
```

**Errors after changes?**
```bash
# Hard refresh browser: Ctrl+Shift+R
# Or restart streamlit app
```

---

**Status**: ✅ Ready to Launch!  
**Version**: 0.1.0  
**Date**: March 20, 2026
