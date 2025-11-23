# Math Olympic Question Search - Implementation Plan

## 1. Objective & Architecture

Build a local system that:
1. Scrapes Gauss competition problems (G7 + G8) from CEMC Waterloo
2. Tags problems via local Ollama (qwen3-30b)
3. Provides a web interface where users can input LaTeX equations, get concept tag suggestions, and find matching practice problems

**Tech Stack:**
- **Frontend:** React (Vite) + KaTeX for math rendering
- **Backend:** FastAPI
- **LLM:** Ollama with qwen3-30b (local)
- **Storage:** `problems.json` (upgradeable to SQLite/Postgres)

## 2. Data Model

Define a `Problem` object with:
- `id`: Unique identifier
- `source`: "gauss"
- `grade`: 7 or 8
- `year`: Contest year (e.g., 2025)
- `problem_number`: 1-25
- `statement`: Problem text (may contain LaTeX)
- `choices`: Array of answer options (A-E)
- `answer`: Correct answer letter
- `solution`: Solution explanation
- `tags`: Array of concept tags
- `url`: Source URL

Persist all problems as an array in `problems.json`.

## 3. Scraping Workflow

### Data Sources (CEMC Waterloo)
- **List page:** `https://cemc.uwaterloo.ca/resources/past-contests?grade=All&academic_year=All&contest_category=13`
- **Problems:** `https://cemc.uwaterloo.ca/sites/default/files/documents/{year}/{year}Gauss{grade}Contest.html`
- **Solutions:** `https://cemc.uwaterloo.ca/sites/default/files/documents/{year}/{year}GaussSolution.html`

### Scraping Strategy
1. Parse the list page to discover available years
2. For each year, scrape both Grade 7 and Grade 8 contest pages
3. Parse problem statements, choices, and answer keys
4. Scrape solution page and match solutions to problems
5. Store unified problem records in `problems.json`

**Initial scope:** 2025 Gauss G7 + G8, with scraper designed to handle other years.

## 4. Tagging Pipeline

Batch job that:
1. Loads `problems.json`
2. Sends each problem statement to Ollama (qwen3-30b)
3. Receives tags with confidence scores
4. Updates each problem's `tags` field
5. Saves back to `problems.json`

### Tag Whitelist
Ollama may only choose from these tags:

**Number Theory:**
- `divisibility`, `primes`, `factors`, `gcd-lcm`, `remainders`, `exponents`, `powers-and-patterns`, `digits`, `parity`

**Arithmetic & Algebra:**
- `fractions`, `ratios`, `percentages`, `expressions`, `equations`, `substitution`, `patterns`, `sequences`, `inequalities`, `polynomials`

**Geometry:**
- `triangles`, `angles`, `similarity`, `circles`, `coordinates`, `distance`, `area`, `perimeter`, `3d-geometry`, `transformations`

**Combinatorics & Probability:**
- `counting`, `arrangements`, `casework`, `probability`, `paths`

**Word Problems & Applications:**
- `rates`, `averages`, `money`, `tables-and-graphs`

**Problem-Solving Strategies:**
- `logic`, `working-backwards`, `guess-check`, `symmetry`, `invariants`, `extremal`

## 5. Backend API (FastAPI)

### Endpoints

**`POST /api/analyze`**
- Input: `{ "latex": "x^2 + 5x + 6 = 0" }`
- Process: Send to Ollama for concept tagging
- Output: `{ "tags": [{"name": "equations", "confidence": 0.95}, {"name": "polynomials", "confidence": 0.82}] }`

**`GET /api/problems`**
- Query params: `?tags=equations,polynomials` (comma-separated)
- Output: Array of matching problems (intersection of all selected tags)

**`GET /api/problems/{id}`**
- Output: Single problem with full details including solution

### Startup
- Load `problems.json` into memory on startup

## 6. Frontend Flow (React + Vite)

### User Interface

1. **LaTeX Input Section**
   - Text input field for LaTeX equation
   - Live KaTeX preview below input showing rendered equation
   - "Analyze" button to submit

2. **Tag Suggestions Section**
   - Display suggested tags from Ollama
   - Each tag shows confidence score as a **visual progress bar**
   - Tags are **unselected by default** - user picks relevant ones
   - Checkbox or toggle for each tag

3. **Results Section**
   - Display matching problems based on selected tags
   - Show problem statement, choices, answer
   - Expandable solution section
   - Filter/sort options

### Component Structure
```
App
├── LatexInput (text input + KaTeX preview)
├── TagSelector (tags with confidence progress bars)
└── ProblemList
    └── ProblemCard (statement, choices, expandable solution)
```

## 7. Implementation Steps

### Phase 1: Data Collection
1. Implement Gauss scraper for CEMC website
2. Scrape 2025 G7 + G8 problems and solutions
3. Store in `problems.json`

### Phase 2: Tagging
4. Create tagging batch script using Ollama qwen3-30b
5. Run tagging on all scraped problems
6. Verify and adjust tag quality

### Phase 3: Backend
7. Set up FastAPI project structure
8. Implement `/api/analyze` endpoint (Ollama integration)
9. Implement `/api/problems` endpoint (tag filtering)

### Phase 4: Frontend
10. Set up React + Vite project
11. Build LaTeX input with KaTeX preview
12. Build tag selector with confidence progress bars
13. Build problem list and card components
14. Connect to backend API

### Phase 5: Polish
15. Add error handling and loading states
16. Style the UI
17. Test end-to-end flow
