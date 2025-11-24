"""FastAPI backend for Math Olympic Question Search."""
import json
import re
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Tag whitelist organized by category
TAG_WHITELIST = {
    "Number Theory": [
        "divisibility", "primes", "factors", "gcd-lcm", "remainders",
        "exponents", "powers-and-patterns", "digits", "parity", "modular-arithmetic"
    ],
    "Arithmetic & Algebra": [
        "fractions", "ratios", "percentages", "expressions", "equations",
        "substitution", "patterns", "sequences", "inequalities", "polynomials",
        "multiplication", "division", "linear-equations"
    ],
    "Geometry": [
        "triangles", "angles", "similarity", "circles", "coordinates",
        "distance", "area", "perimeter", "3d-geometry", "transformations",
        "reflections"
    ],
    "Combinatorics & Probability": [
        "counting", "arrangements", "casework", "probability", "paths"
    ],
    "Word Problems & Applications": [
        "rates", "averages", "money", "tables-and-graphs", "time", "calendar",
        "bar-graphs"
    ],
    "Problem-Solving Strategies": [
        "logic", "working-backwards", "guess-check", "symmetry", "invariants", "extremal"
    ],
    "Statistics": [
        "mean", "median", "mode", "statistics"
    ]
}

# Flatten all tags for validation
ALL_TAGS = [tag for tags in TAG_WHITELIST.values() for tag in tags]

def _normalize_tag(tag: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")

NORMALIZED_TAGS = {_normalize_tag(tag): tag for tag in ALL_TAGS}
TAG_ALIASES = {
    "bar-graph": "bar-graphs",
    "bar-chart": "bar-graphs",
    "graph": "bar-graphs",
    "translate": "coordinates",
    "translation": "coordinates",
    "reflections": "reflections",
    "reflect": "reflections",
    "day-of-week": "calendar",
    "calendar-problem": "calendar",
    "die": "probability",
    "dice": "probability",
    "ratio": "ratios",
    "ratios": "ratios",
    "multiplying": "multiplication",
    "divide": "division",
}

def _resolve_tag(tag: str) -> str | None:
    norm = _normalize_tag(tag)
    if norm in TAG_ALIASES:
        norm = _normalize_tag(TAG_ALIASES[norm])
    if norm in NORMALIZED_TAGS:
        return NORMALIZED_TAGS[norm]
    if norm.endswith("s") and norm[:-1] in NORMALIZED_TAGS:
        return NORMALIZED_TAGS[norm[:-1]]
    if norm + "s" in NORMALIZED_TAGS:
        return NORMALIZED_TAGS[norm + "s"]
    return None

def _extract_tags_from_text(text: str) -> list[str]:
    normalized_text = _normalize_tag(text)
    found: list[str] = []
    for norm_tag, canonical in NORMALIZED_TAGS.items():
        if norm_tag and norm_tag in normalized_text and canonical not in found:
            found.append(canonical)
    return found

def _normalize_tag(tag: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")

NORMALIZED_TAGS = {_normalize_tag(tag): tag for tag in ALL_TAGS}
TAG_ALIASES = {
    "bar-graph": "bar-graphs",
    "bar-chart": "bar-graphs",
    "graph": "bar-graphs",
    "translate": "coordinates",
    "translation": "coordinates",
    "reflections": "reflections",
    "reflect": "reflections",
    "day-of-week": "calendar",
    "calendar-problem": "calendar",
    "die": "probability",
    "dice": "probability",
    "ratio": "ratios",
    "ratios": "ratios",
    "multiplying": "multiplication",
    "divide": "division",
}

def _resolve_tag(tag: str) -> str | None:
    norm = _normalize_tag(tag)
    if norm in TAG_ALIASES:
        norm = _normalize_tag(TAG_ALIASES[norm])
    if norm in NORMALIZED_TAGS:
        return NORMALIZED_TAGS[norm]
    if norm.endswith("s") and norm[:-1] in NORMALIZED_TAGS:
        return NORMALIZED_TAGS[norm[:-1]]
    if norm + "s" in NORMALIZED_TAGS:
        return NORMALIZED_TAGS[norm + "s"]
    return None

def _extract_tags_from_text(text: str) -> list[str]:
    normalized_text = _normalize_tag(text)
    found: list[str] = []
    for norm_tag, canonical in NORMALIZED_TAGS.items():
        if norm_tag and norm_tag in normalized_text and canonical not in found:
            found.append(canonical)
    return found

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:30b"
DATA_PATH = Path(__file__).parent.parent / "data" / "problems.json"

# In-memory problem store
problems_db: list[dict] = []


# Pydantic models for API
class AnalyzeRequest(BaseModel):
    latex: str


class TagWithConfidence(BaseModel):
    name: str
    confidence: float


class AnalyzeResponse(BaseModel):
    tags: list[TagWithConfidence]


class HintRequest(BaseModel):
    problem_id: str
    conversation: list[dict] = []
    message: str


class HintResponse(BaseModel):
    response: str


class ProblemResponse(BaseModel):
    id: str
    source: str
    grade: int
    year: int
    problem_number: int
    statement: str
    choices: list[str]
    tags: list[str]
    url: str
    images: list[str] = []  # Base64 data URIs for problem images
    # answer and solution are excluded from list view


class ProblemDetailResponse(ProblemResponse):
    answer: Optional[str] = None
    solution: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load problems on startup."""
    global problems_db
    if DATA_PATH.exists():
        with open(DATA_PATH) as f:
            problems_db = json.load(f)
        print(f"Loaded {len(problems_db)} problems from {DATA_PATH}")
    else:
        print(f"Warning: No problems file found at {DATA_PATH}")

    yield


app = FastAPI(
    title="Math Olympic Question Search API",
    description="API for searching and getting hints for math competition problems",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/tags")
async def get_tags() -> dict:
    """Get all available tags organized by category with problem counts."""
    # Count problems per tag
    tag_counts: dict[str, int] = {}
    for problem in problems_db:
        for tag in problem.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return {"tags": TAG_WHITELIST, "all_tags": ALL_TAGS, "tag_counts": tag_counts}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_latex(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a LaTeX expression and suggest concept tags."""
    if not request.latex.strip():
        raise HTTPException(status_code=400, detail="LaTeX expression is required")

    system_prompt = """You are a math education expert. Analyze the given math expression or problem and identify relevant mathematical concepts.

Return ONLY valid JSON in this exact format:
{"tags": [{"name": "tag_name", "confidence": 0.95}, {"name": "tag_name2", "confidence": 0.80}]}

You MUST ONLY use tags from this whitelist:
""" + ", ".join(ALL_TAGS) + """

Rules:
1. Assign confidence scores between 0.0 and 1.0
2. Return 1-5 most relevant tags
3. Higher confidence = more certain the concept is needed
4. Only return valid JSON, no other text"""

    prompt = f"""Analyze this math expression and identify the mathematical concepts involved:

{request.latex}

Return JSON with tags and confidence scores."""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 200
                    }
                },
                timeout=60.0
            )
            response.raise_for_status()

            result = response.json()
            response_text = result.get("response", "").strip()
            reasoning_text = result.get("thinking", "")

            # Parse JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                data = json.loads(json_str)
                tags_data = data.get("tags", [])

                # Validate and convert tags
                tags: list[TagWithConfidence] = []
                for t in tags_data:
                    name = None
                    conf = 0.5
                    if isinstance(t, dict):
                        name = t.get("name")
                        if "confidence" in t:
                            try:
                                conf = float(t.get("confidence", 0.5))
                            except Exception:
                                conf = 0.5
                    elif isinstance(t, str):
                        name = t
                    resolved = _resolve_tag(name) if name else None
                    if resolved:
                        tags.append(
                            TagWithConfidence(
                                name=resolved,
                                confidence=min(1.0, max(0.0, conf))
                            )
                        )

                # Sort by confidence
                tags.sort(key=lambda x: x.confidence, reverse=True)
                if tags:
                    return AnalyzeResponse(tags=tags)

            # Fallback: scan response/reasoning/prompt text for tag keywords
            fallback_tags = _extract_tags_from_text(response_text or reasoning_text or request.latex)
            if fallback_tags:
                return AnalyzeResponse(
                    tags=[TagWithConfidence(name=t, confidence=0.4) for t in fallback_tags]
                )

            return AnalyzeResponse(tags=[])

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing expression: {str(e)}"
        )


@app.get("/api/problems", response_model=list[ProblemResponse])
async def get_problems(
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    grade: Optional[int] = Query(None, description="Filter by grade (7 or 8)"),
    year: Optional[int] = Query(None, description="Filter by year")
) -> list[ProblemResponse]:
    """Get problems, optionally filtered by tags (intersection)."""
    result = problems_db

    # Filter by tags (union - must have ANY selected tag)
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            result = [
                p for p in result
                if any(tag in p.get("tags", []) for tag in tag_list)
            ]

    # Filter by grade
    if grade is not None:
        result = [p for p in result if p.get("grade") == grade]

    # Filter by year
    if year is not None:
        result = [p for p in result if p.get("year") == year]

    return [
        ProblemResponse(
            id=p["id"],
            source=p["source"],
            grade=p["grade"],
            year=p["year"],
            problem_number=p["problem_number"],
            statement=p["statement"],
            choices=p["choices"],
            tags=p.get("tags", []),
            url=p["url"]
        )
        for p in result
    ]


@app.get("/api/problems/{problem_id}", response_model=ProblemDetailResponse)
async def get_problem(problem_id: str) -> ProblemDetailResponse:
    """Get a single problem with full details including answer and solution."""
    for p in problems_db:
        if p["id"] == problem_id:
            return ProblemDetailResponse(
                id=p["id"],
                source=p["source"],
                grade=p["grade"],
                year=p["year"],
                problem_number=p["problem_number"],
                statement=p["statement"],
                choices=p["choices"],
                tags=p.get("tags", []),
                url=p["url"],
                answer=p.get("answer"),
                solution=p.get("solution")
            )

    raise HTTPException(status_code=404, detail="Problem not found")


@app.post("/api/hint", response_model=HintResponse)
async def get_hint(request: HintRequest) -> HintResponse:
    """Get a hint for a problem using Ollama (never reveals the answer)."""
    # Find the problem
    problem = None
    for p in problems_db:
        if p["id"] == request.problem_id:
            problem = p
            break

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Build conversation context
    choices_text = "\n".join([f"{chr(65+i)}) {c}" for i, c in enumerate(problem["choices"])])

    system_prompt = """You are a helpful math tutor. Your job is to guide students to understand and solve math problems WITHOUT revealing the answer directly.

CRITICAL RULES:
1. NEVER reveal the correct answer letter (A, B, C, D, or E)
2. NEVER say which specific choice is correct
3. Guide the student step by step with hints and questions
4. Encourage them to think through the problem
5. If they're stuck, give progressively more specific hints
6. Explain concepts but let them reach the answer themselves
7. If they ask "what's the answer?" or similar, politely decline and offer another hint instead

You can:
- Explain relevant formulas or concepts
- Break down the problem into smaller steps
- Ask guiding questions
- Point out what to focus on
- Verify their reasoning (without confirming the final answer)"""

    # Build messages for context
    problem_context = f"""The student is working on this problem:

Problem: {problem['statement']}

Answer choices:
{choices_text}

Help them WITHOUT revealing which answer is correct."""

    # Build conversation history
    messages_text = ""
    for msg in request.conversation[-10:]:  # Last 10 messages for context
        role = msg.get("role", "user")
        content = msg.get("content", "")
        messages_text += f"\n{role.capitalize()}: {content}"

    messages_text += f"\nStudent: {request.message}"

    prompt = f"""{problem_context}

Conversation so far:{messages_text}

Provide a helpful hint (remember: NEVER reveal the answer):"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500
                    }
                },
                timeout=90.0
            )
            response.raise_for_status()

            result = response.json()
            hint_text = result.get("response", "").strip()

            # Clean up response
            if hint_text.startswith("Tutor:"):
                hint_text = hint_text[6:].strip()
            if hint_text.startswith("Assistant:"):
                hint_text = hint_text[10:].strip()

            return HintResponse(response=hint_text)

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating hint: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "problems_loaded": len(problems_db),
        "ollama_url": OLLAMA_URL,
        "model": MODEL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
