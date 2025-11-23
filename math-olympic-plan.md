# Math Olympic Project Plan

## 1. Objective & Architecture
- Build a local system that scrapes AMC8 (RandomMath) and Gauss 2021 G7/G8 (CEMC), tags problems via local Ollama, and exposes a FastAPI backend plus React UI for screenshot capture, OCR, tagging, and similarity search over the curated dataset.
- Stack: React (Vite or CRA) frontend, FastAPI backend, Ollama LLM, MinerU OCR (plug-in), and `problems.json` storage (upgradeable to SQLite/Postgres).

## 2. Data Model
- Define a `Problem` object with metadata (source, year, statement, choices, answer, solution, tags, URLs).
- Persist all problems as an array in `problems.json`, mirroring future database schema.

## 3. Scraping Workflow
- AMC8 2024: Parse problem blocks, answers, and “View Solution” links from RandomMath; scrape each solution page to capture solution text and answer letter; build unified AMC8 records.
- Gauss 2021 G7/G8: Scrape contest pages for statements/options, solution page for grade-specific explanations; merge contest & solution data into problem entries.
- Output all scraped records into `problems` list for later tagging/storage.

## 4. Tagging Pipeline
- Batch job loads `problems.json`, sends statements (optionally solutions) to Ollama with whitelist of tags, receives JSON response, updates each problem’s `tags`, and saves the file back.
- Ollama may only choose tags from the following list:
  - `divisibility`
  - `primes`
  - `factors`
  - `gcd-lcm`
  - `remainders`
  - `exponents`
  - `powers-and-patterns`
  - `digits`
  - `parity`
  - `fractions`
  - `ratios`
  - `percentages`
  - `expressions`
  - `equations`
  - `substitution`
  - `patterns`
  - `sequences`
  - `inequalities`
  - `polynomials`
  - `triangles`
  - `angles`
  - `similarity`
  - `circles`
  - `coordinates`
  - `distance`
  - `area`
  - `perimeter`
  - `3d-geometry`
  - `transformations`
  - `counting`
  - `arrangements`
  - `casework`
  - `probability`
  - `paths`
  - `rates`
  - `averages`
  - `money`
  - `tables-and-graphs`
  - `logic`
  - `working-backwards`
  - `guess-check`
  - `symmetry`
  - `invariants`
  - `extremal`

## 5. Backend API
- FastAPI loads `problems.json` on startup.
- `POST /api/analyze-screenshot`: accepts image, runs OCR to markdown, tags via Ollama, performs similarity search by tag overlap, returns markdown/tags/problems.
- (Optional) `GET /api/problems?tags=…` to search by tag list.
- Similarity search scores by tag intersection and returns top matches.

## 6. Frontend Flow
- React UI with “Capture Question” button using `getDisplayMedia`, preview overlay, and capture-to-canvas flow that posts image to backend.
- Display recognized markdown, tags, and similar problems with expandable solutions.

## Next Steps
1. Implement scrapers for AMC8 and Gauss contests/solutions.
2. Create tagging batch job and ensure `problems.json` persists curated data.
3. Build FastAPI endpoints (OCR integration, Ollama tagging, similarity search).
4. Develop React capture UI and hook it to backend APIs.
