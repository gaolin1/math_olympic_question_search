# Math Olympic Question Search

A local system for searching math competition problems by concept. Enter a LaTeX math expression, get AI-suggested concept tags, and find matching practice problems from Gauss competitions.

## Features

- **LaTeX Input**: Enter math expressions with live KaTeX preview
- **AI Tagging**: Uses Ollama (qwen3:30b) to identify mathematical concepts
- **Problem Search**: Filter 50+ Gauss competition problems by concept tags
- **Hint System**: Get step-by-step hints without revealing answers
- **Responsive UI**: Clean React interface with inline chat

## Architecture

```
math_olympic_question_search/
├── backend/
│   ├── api/           # FastAPI backend
│   ├── data/          # problems.json database
│   ├── scraper/       # CEMC Gauss problem scraper
│   └── tagging/       # Ollama tagging pipeline
├── frontend/          # React + Vite + KaTeX
└── scripts/           # Convenience scripts
```

## Prerequisites

1. **Python 3.10+**
2. **Node.js 18+**
3. **Ollama** with `qwen3:30b` model

### Install Ollama

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull qwen3:30b

# Start Ollama server
ollama serve
```

## Quick Start

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Run the Tagging Pipeline (Optional)

Tag all problems with concept tags (requires Ollama running):

```bash
./scripts/run_tagger.sh
```

### 4. Start the Backend

```bash
./scripts/run_backend.sh
# or manually:
cd backend && uvicorn api.main:app --reload --port 8000
```

### 5. Start the Frontend

```bash
./scripts/run_frontend.sh
# or manually:
cd frontend && npm run dev
```

### 6. Open the App

Visit http://localhost:5173

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze LaTeX and get concept tags |
| `/api/problems` | GET | List problems (filter by `?tags=`) |
| `/api/problems/{id}` | GET | Get single problem with solution |
| `/api/hint` | POST | Get a hint for a problem |
| `/api/tags` | GET | Get all available tags |
| `/health` | GET | Health check |

## Tag Categories

**Number Theory:** divisibility, primes, factors, gcd-lcm, remainders, exponents, powers-and-patterns, digits, parity

**Arithmetic & Algebra:** fractions, ratios, percentages, expressions, equations, substitution, patterns, sequences, inequalities, polynomials

**Geometry:** triangles, angles, similarity, circles, coordinates, distance, area, perimeter, 3d-geometry, transformations

**Combinatorics & Probability:** counting, arrangements, casework, probability, paths

**Word Problems:** rates, averages, money, tables-and-graphs

**Problem-Solving:** logic, working-backwards, guess-check, symmetry, invariants, extremal

## Data Sources

Problems are scraped from the [CEMC (Centre for Education in Mathematics and Computing)](https://cemc.uwaterloo.ca/) Gauss Competition archives.

Currently includes:
- 2025 Gauss Grade 7 (25 problems)
- 2025 Gauss Grade 8 (25 problems)

## Scraping More Problems

The scraper supports downloading problems from CEMC. Due to anti-bot measures, you may need to manually save HTML files:

```bash
cd backend
python -m scraper.gauss_scraper --urls  # Show URLs to download
# Save HTML files to backend/cache/
python -m scraper.gauss_scraper
```

## Development

### Backend

```bash
cd backend
uvicorn api.main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

### Build for Production

```bash
cd frontend
npm run build
```

## License

MIT
