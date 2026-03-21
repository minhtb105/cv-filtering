# 🎨 Dashboard Visual Guide & Navigation

## 📊 Streamlit Dashboard Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  CV INTELLIGENCE DASHBOARD v0.1.0 (March 20, 2026)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌────────────────────────────────────────┐   │
│  │   SIDEBAR    │  │      MAIN CONTENT AREA                 │   │
│  │              │  │                                         │   │
│  │ 📊 Nav Menu  │  │  [Page Title]                          │   │
│  │              │  │  [Page Description]                    │   │
│  │ ○ Search     │  │  ─────────────────────────────────    │   │
│  │ ○ Score      │  │  [Main Interactive Elements]           │   │
│  │ ○ Similar    │  │                                         │   │
│  │ ○ Metrics    │  │  [Charts & Visualizations]             │   │
│  │              │  │                                         │   │
│  │ ─────────────│  │  [Tables & Results]                    │   │
│  │              │  │                                         │   │
│  │ System Info  │  │                                         │   │
│  │ • Online     │  │                                         │   │
│  │ • 258 items  │  │                                         │   │
│  │ • v0.1.0     │  │                                         │   │
│  │              │  │                                         │   │
│  └──────────────┘  └────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 PAGE 1: SEARCH CVS

```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 Search Candidates                                            │
│  Find candidates matching specific skills or job titles          │
│  ─────────────────────────────────────────────────────────────  │
│                                                                   │
│  ┌─ SEARCH CONTROLS ──────────────────── ─────────────────────┐ │
│  │                                                             │ │
│  │  Query Input: [Python developer with Django ________]     │ │
│  │  Results Limit: 1 ──●──────────── 20                      │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ✓ Found 8 matching candidates                                  │
│                                                                   │
│  ┌─ SEARCH RESULTS TABLE ─────────────────────────────────────┐ │
│  │ │ Name              │ Score │ Skills          │ Experience   │ │
│  │ ├─────────────────┼───────┼─────────────────┼──────────┤ │
│  │ │ John Developer  │ 5.50  │ Python, Django  │ 5.0 yrs  │ │
│  │ │ Alice Smith     │ 4.25  │ Python, Flask   │ 4.5 yrs  │ │
│  │ │ Bob Code        │ 3.75  │ Python, REST    │ 3.0 yrs  │ │
│  │ └─────────────────┴───────┴─────────────────┴──────────┘ │
│  │                                                             │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─ CANDIDATE DETAILS ────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  Select: [John Developer ▼]                               │ │
│  │                                                             │ │
│  │  ┌─ Personal Info ────┐  ┌─ Skills ───────────────────┐  │ │
│  │  │ • John Developer   │  │ Python, Django, REST,      │  │ │
│  │  │ • john@email.com   │  │ PostgreSQL, Docker,        │  │ │
│  │  │ • ENGINEERING      │  │ Kubernetes, Git, AWS       │  │ │
│  │  │ • 5 years exp      │  │ ... and 5 more             │  │ │
│  │  └────────────────────┘  └────────────────────────────┘  │ │
│  │                                                             │ │
│  │  [SKILL DISTRIBUTION CHART - Plotly Bar]                  │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  █ Python                                            │ │ │
│  │  │  █ Django                                            │ │ │
│  │  │  ▇ PostgreSQL                                        │ │ │
│  │  │  ▆ REST API                                          │ │ │
│  │  │  ▄ Docker                                            │ │ │
│  │  │  ▃ Kubernetes                                        │ │ │
│  │  │  ▂ Git                                               │ │ │
│  │  │  ▁ AWS                                               │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Interactions**:
- Type in query box → See results live
- Adjust slider → More/fewer results
- Click candidate → See full profile
- View chart → Understand skill distribution

---

## ⭐ PAGE 2: SCORE JOB

```
┌─────────────────────────────────────────────────────────────────┐
│  ⭐ Score Candidates for Job                                    │
│  Rank candidates based on job requirements                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                   │
│  ┌─ JOB DESCRIPTION ──────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ Job Description                                    │ │ │
│  │  │                                                  │ │ │
│  │  │ [________________________________________...     │ │ │
│  │  │  ________________________________________...     │ │ │
│  │  │  ________________________________________...     │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  Quick Templates:                                           │ │
│  │  [📋 Senior Python]  [☕ Java Dev]  [💼 Sales Mgr]       │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─ SCORING RESULTS ──────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  Top 3 Candidates:                                          │ │
│  │                                                             │ │
│  │  ┌─ #1 ─────────────┐  ┌─ #2 ─────────────┐  ┌─ #3 ───┐ │ │
│  │  │ John Developer   │  │ Alice Smith     │  │ Bob    │ │ │
│  │  │ 0.92             │  │ 0.87            │  │ 0.78   │ │ │
│  │  │ ⭐⭐⭐⭐⭐❌    │  │ ⭐⭐⭐⭐❌❌    │  │ ⭐⭐⭐ │ │
│  │  └──────────────────┘  └─────────────────┘  └────────┘ │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─ FULL RANKING (Top 20) ────────────────────────────────────┐ │
│  │                                                             │ │
│  │ │ Rank │ Name         │ Total │ Skills │ Exp │ Sr │ Edu  │ │
│  │ ├──────┼──────────────┼───────┼────────┼─────┼────┼──────┤ │
│  │ │  1   │ John Dev...  │ 0.92  │ 0.95   │1.00 │1.00│ 0.80 │ │
│  │ │  2   │ Alice Smith  │ 0.87  │ 0.85   │0.95 │0.90│ 0.75 │ │
│  │ │  3   │ Bob Code     │ 0.78  │ 0.82   │0.90 │0.75│ 0.70 │ │
│  │ │  4   │ Carol Data   │ 0.72  │ 0.78   │0.85 │0.60│ 0.65 │ │
│  │ │  ... │ ...          │ ...   │ ...    │ ... │ ...│ ...  │ │
│  │ │ 20   │ Zoe Analytics│ 0.45  │ 0.40   │0.50 │0.40│ 0.45 │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  [RADAR CHART - Score Breakdown ✓]                              │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │          Top Candidate Score Breakdown                      │ │
│  │                                                             │ │
│  │              ▲                                              │ │
│  │            / │ \                                            │ │
│  │          /   │   \                                          │ │
│  │       Skills Seniority Education                            │ │
│  │       0.95  \ │ /  0.80                                     │ │
│  │             \│/                                             │ │
│  │      ───────────────  Experience = 1.00                    │ │
│  │     /                 \                                     │ │
│  │   /                     \                                   │ │
│  │ Language               (RADAR)                              │ │
│  │ 0.95                                                        │ │
│  │            Overall Score: 0.92                             │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Interactions**:
- Type job description OR click template
- Click "🚀 Score All Candidates"
- View top 3 in metric cards
- See full ranking + click to sort
- View radar chart for detailed breakdown

---

## 👥 PAGE 3: RECOMMENDATIONS

```
┌─────────────────────────────────────────────────────────────────┐
│  👥 Candidate Recommendations                                   │
│  Find similar candidates and job matches                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                   │
│  ┌─ REFERENCE CANDIDATE ──────────────────────────────────────┐ │
│  │                                                             │ │
│  │  Select: [John Developer (a1b2c3d4) ▼]                    │ │
│  │                                                             │ │
│  │  Reference Profile:                                         │ │
│  │  • Experience: 5.0 years                                    │ │
│  │  • Skills: Python, Django, REST APIs, PostgreSQL, Docker  │ │
│  │  • Category: ENGINEERING                                    │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ✓ Found 10 similar candidates                                  │
│                                                                   │
│  ┌─ SIMILAR CANDIDATES TABLE ─────────────────────────────────┐ │
│  │                                                             │ │
│  │ │ Name         │ Similarity │ Skill Matches │ Experience  │ │
│  │ ├──────────────┼────────────┼───────────────┼─────────────┤ │
│  │ │ Alice Smith  │ 85%        │ 4             │ 4.5 yrs     │ │
│  │ │ Bob Code     │ 78%        │ 3             │ 5.5 yrs     │ │
│  │ │ Carol Data   │ 72%        │ 3             │ 5.0 yrs     │ │
│  │ │ Diana Park   │ 65%        │ 2             │ 6.0 yrs     │ │
│  │ │ Eve Martin   │ 60%        │ 2             │ 4.5 yrs     │ │
│  │ │ Frank Lee    │ 58%        │ 2             │ 5.5 yrs     │ │
│  │ │ Grace Wong   │ 52%        │ 1             │ 3.5 yrs     │ │
│  │ │ Henry James  │ 48%        │ 1             │ 5.0 yrs     │ │
│  │ │ Iris Brown   │ 45%        │ 1             │ 4.5 yrs     │ │
│  │ │ Jack Smith   │ 42%        │ 1             │ 6.5 yrs     │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  [BAR CHART - Similarity Scores ✓]                              │ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Similarity Scores (Top 8)                                 │ │
│  │                                                             │ │
│  │  Alice Smith  ████████░░░░░░░░░░ 85%                      │ │
│  │  Bob Code     ███████░░░░░░░░░░░░ 78%                      │ │
│  │  Carol Data   ███████░░░░░░░░░░░░ 72%                      │ │
│  │  Diana Park   ██████░░░░░░░░░░░░░ 65%                      │ │
│  │  Eve Martin   █████░░░░░░░░░░░░░░ 60%                      │ │
│  │  Frank Lee    █████░░░░░░░░░░░░░░ 58%                      │ │
│  │  Grace Wong   ████░░░░░░░░░░░░░░░ 52%                      │ │
│  │  Henry James  ████░░░░░░░░░░░░░░░ 48%                      │ │
│  │                                                             │ │
│  │  ■ Good Match (70%+)  ■ Fair Match (50-70%)  ■ Weak (30%) │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Interactions**:
- Select reference candidate
- View their profile summary
- See table of similar candidates
- View bar chart of similarity scores
- Use results to build candidate pools

---

## 📈 PAGE 4: SYSTEM METRICS

```
┌─────────────────────────────────────────────────────────────────┐
│  📈 System Metrics & Statistics                                 │
│  Platform performance and data overview                         │
│  ─────────────────────────────────────────────────────────────  │
│                                                                   │
│  ┌─ KEY METRICS ──────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐           │ │
│  │  │   Total    │  │  Unique    │  │    Avg     │           │ │
│  │  │ Candidates │  │   Skills   │  │ Experience │           │ │
│  │  │            │  │            │  │            │           │ │
│  │  │    258     │  │   2,000+   │  │   4.5      │           │ │
│  │  │ indexed    │  │   terms    │  │   years    │           │ │
│  │  │            │  │            │  │            │           │ │
│  │  └────────────┘  └────────────┘  └────────────┘           │ │
│  │                                                             │ │
│  │              ┌────────────┐                                │ │
│  │              │ Categories │                                │ │
│  │              │     31     │                                │ │
│  │              │    types   │                                │ │
│  │              └────────────┘                                │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─ DISTRIBUTION CHARTS ──────────────────────────────────────┐ │
│  │                                                             │ │
│  │  [BAR CHART]              [PIE CHART]                      │ │
│  │  Category Distribution    Category Proportions             │ │
│  │                                                             │ │
│  │  UNCATEGORIZED ███░░░     ┌─────────────────┐             │ │
│  │  ENGINEERING   ██░░░░     │ ■ UNCATEGORIZED │             │ │
│  │  SALES         █░░░░░     │ ■ ENGINEERING   │             │ │
│  │  FINANCE       █░░░░░     │ ■ SALES         │             │ │
│  │  BANKING       █░░░░░     │ ■ FINANCE       │             │ │
│  │  HD            ░░░░░░     │ ■ OTHER         │             │ │
│  │  ...           ░░░░░░     └─────────────────┘             │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─ EXPERIENCE DISTRIBUTION ──────────────────────────────────┐ │
│  │                                                             │ │
│  │  [HISTOGRAM] Years of Experience                           │ │
│  │                                                             │ │
│  │  ▲ Count                                                    │ │
│  │  │                    ┌─┐                                  │ │
│  │  │            ┌─┐    ┌─┴─┐            ┌─┐                │ │
│  │  │    ┌─┐    ┌─┴─┐  ┌───┴─┐    ┌─┐  ┌─┴─┐    ┌─┐        │ │
│  │  │ ┌──┴─┴──┬─┴───┴──┴─────┴───┬─┴─┴──┴───┴────┴─┬───    │ │
│  │  │ 0      5      10     15    20     25     30    35      │ │
│  │  │─── Years of Experience ───›                            │ │
│  │  │ Bulk: 3-7 years (entry to mid-level)                   │ │
│  │ ▼                                                           │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─ TOP 15 SKILLS ────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  [HORIZONTAL BAR CHART]                                    │ │
│  │                                                             │ │
│  │  Python                    ████████████████ 42             │ │
│  │  Java                      ███████████████░ 38             │ │
│  │  SQL                       ███████████░░░░░ 35             │ │
│  │  Django                    ██████████░░░░░░ 28             │ │
│  │  REST API                  █████████░░░░░░░ 25             │ │
│  │  PostgreSQL                ████████░░░░░░░░ 22             │ │
│  │  Docker                    ███████░░░░░░░░░ 20             │ │
│  │  JavaScript                ███████░░░░░░░░░ 19             │ │
│  │  AWS                       ██████░░░░░░░░░░ 18             │ │
│  │  React                     ██████░░░░░░░░░░ 17             │ │
│  │  MongoDB                   █████░░░░░░░░░░░ 15             │ │
│  │  Git                       █████░░░░░░░░░░░ 14             │ │
│  │  Kubernetes                ████░░░░░░░░░░░░ 13             │ │
│  │  Spring                    ████░░░░░░░░░░░░ 12             │ │
│  │  Microservices             ███░░░░░░░░░░░░░ 10             │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─ SYSTEM STATUS ────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  ✓ API Server: Ready         (localhost:8000)             │ │
│  │  ✓ Vector DB: Configured     (10,000+ capacity)           │ │
│  │  ✓ Search Engine: Ready      (<50ms query time)           │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Dashboard Version 0.1.0 | Last Updated: 2026-03-20 14:30       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Interactions**:
- View metrics cards
- Explore category distribution
- Analyze experience distribution
- Identify skill trends
- Monitor system health

---

## 🎛️ Navigation Quick Reference

```
Dashboard Sidebar:
─────────────────────────────
  📊 CV Intelligence
  ─────────────────────────────
  
  🔍 SEARCH          [Select Page]
  ⭐ SCORE JOB       [Page 1-4]
  👥 RECOMMEND
  📈 METRICS
  
  ─────────────────────────────
  System Status: ✓ Online
  
  Candidates: 258
  Last Updated: Today
  Version: 0.1.0
```

---

## ⌨️ Keyboard Navigation

| Action | Key |
|--------|-----|
| Search within page | Ctrl+F |
| Page refresh | F5 |
| Copy table | Ctrl+A, Ctrl+C |
| Focus search | Ctrl+L |
| Stop app | Ctrl+C (terminal) |

---

## 🎨 Visual Design Features

### Color Scheme
- **Primary**: Blue (navigation, highlights)
- **Success**: Green (positive metrics)
- **Warning**: Orange (moderate scores)
- **Danger**: Red (low scores, issues)
- **Neutral**: Gray (background, borders)

### Typography
- **Headers**: Large, bold, clear hierarchy
- **Body**: Readable sans-serif, good contrast
- **Monospace**: Code/technical info

### Layout
- **Responsive**: Works on 1024px+ screens
- **Scalable**: Charts zoom with window
- **Organized**: Logical sections with dividers
- **Spacious**: Good whitespace and margins

---

## 📱 Browser Compatibility

✅ **Recommended**: Chrome, Firefox, Safari (latest)  
✅ **Minimum Width**: 1024px  
✅ **JavaScript**: Required (Streamlit + Plotly)  
✅ **Performance**: Tested on macOS, Linux, Windows  

---

## 🎯 Common User Journeys

### Journey 1: Find Django Developers (3 min)
```
1. Search Page
   Input: "Django"
   
2. View Results
   See 5 Django developers
   
3. Examine Profiles
   Click "Alice Smith"
   Check: 5 years exp, 8 skills
   
4. Action
   Interview shortlist
```

### Journey 2: Score Candidates for Job (5 min)
```
1. Score Page
   Click "📋 Senior Python" template
   
2. Review Results
   Top 3: John (0.92), Alice (0.87), Bob (0.78)
   
3. Analyze Breakdown
   View radar chart
   Notice: Skills 0.95, Exp 1.0, Education 0.80
   
4. Action
   Contact top 3 candidates
```

### Journey 3: Build Backup candidate Pool (5 min)
```
1. Recommendations Page
   Select "John Developer"
   
2. View Similar
   See 10 alternatives
   Top: Alice (85%), Bob (78%), Carol (72%)
   
3. Compare
   Check experience range
   All 4.5-5.5 years (perfect range)
   
4. Action
   Add 3 backup candidates to list
```

### Journey 4: Understand Market Trends (3 min)
```
1. Metrics Page
   Scroll down
   
2. Analyze Skills
   Python (42), Java (38), SQL (35)
   Django (28) popular
   
3. Check Distribution
   Bulk at 3-7 years
   Good mid-level talent pool
   
4. Action
   Plan hiring: Python focus, mid-level preferred
```

---

## 🔐 Data Privacy

- ✅ All data processed locally (no external calls)
- ✅ No telemetry or tracking enabled
- ✅ CSV data stored in project directory
- ✅ Embeddings cached locally
- ✅ No authentication required (local only)

---

## ⚡ Performance Tips

1. **Faster Searches**: Use specific terms ("Python" better than "dev")
2. **Faster Scoring**: Fewer candidates = faster results
3. **Faster Navigation**: Use sidebar buttons (fastest)
4. **Faster Charts**: Let page load completely before scrolling
5. **Faster Recommendations**: Pick candidates with common skills

---

This visual guide provides complete reference for the Streamlit dashboard!

**Last Updated**: March 20, 2026  
**Dashboard Version**: 0.1.0  
**Status**: Production Ready ✓
