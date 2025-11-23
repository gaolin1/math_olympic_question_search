"""Tagging pipeline using Ollama to tag math problems with concept tags."""
import json
import httpx
import asyncio
import re
from pathlib import Path
from typing import Optional

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
    "Statistics": [
        "mean", "median", "mode", "statistics"
    ],
    "Problem-Solving Strategies": [
        "logic", "working-backwards", "guess-check", "symmetry", "invariants", "extremal"
    ]
}

# Flatten all tags for validation
ALL_TAGS = [tag for tags in TAG_WHITELIST.values() for tag in tags]

def _normalize_tag(tag: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", tag.lower())
    return normalized.strip("-")

NORMALIZED_TAGS = {_normalize_tag(tag): tag for tag in ALL_TAGS}
TAG_ALIASES = {
    "percent": "percentages",
    "percentage": "percentages",
    "probabilities": "probability",
    "geometry": "angles",
    "algebra": "expressions",
    "number-theory": "divisibility",
    "tables-and-graph": "tables-and-graphs",
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
        if not norm_tag:
            continue
        if norm_tag in normalized_text and canonical not in found:
            found.append(canonical)
    return found


# Heuristic tags for problems the model leaves empty
def _heuristic_tags_for_problem(problem: dict) -> list[str]:
    text = (problem.get("statement", "") + " " + " ".join(problem.get("choices", []))).lower()
    tags: list[str] = []

    def add(tag: str):
        if tag in ALL_TAGS and tag not in tags:
            tags.append(tag)

    if "graph" in text or "bar chart" in text or "bar graph" in text:
        add("bar-graphs")
    if "day of the week" in text or "monday" in text or "tuesday" in text or "wednesday" in text:
        add("calendar")
    if "coordinates" in text or "(" in text and "," in text and ")" in text:
        add("coordinates")
    if "reflected in the x-axis" in text or "reflected in the y-axis" in text or "reflection" in text:
        add("reflections")
    if "for every" in text or "per bowl" in text or "per dog" in text or "per student" in text:
        add("ratios")
    if "die" in text or "dice" in text or "rolled" in text:
        add("probability")
    if "mode" in text or "median" in text or "mean" in text:
        add("statistics")
    if "/" in text and "=" in text:
        add("fractions")
        add("equations")
    if "prime" in text or "odd number" in text or "even number" in text or "composite" in text or "perfect square" in text:
        add("number-theory")
    if "same number of" in text or "each child received the same" in text or "equally among" in text:
        add("division")
        add("fractions")
    if "checklist" in text or "check off" in text:
        add("logic")

    return tags

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:30b"

SYSTEM_PROMPT = """You are a math education expert. Your task is to analyze math problems and assign relevant concept tags.

You MUST ONLY use tags from this exact whitelist:

Number Theory: divisibility, primes, factors, gcd-lcm, remainders, exponents, powers-and-patterns, digits, parity

Arithmetic & Algebra: fractions, ratios, percentages, expressions, equations, substitution, patterns, sequences, inequalities, polynomials

Geometry: triangles, angles, similarity, circles, coordinates, distance, area, perimeter, 3d-geometry, transformations

Combinatorics & Probability: counting, arrangements, casework, probability, paths

Word Problems & Applications: rates, averages, money, tables-and-graphs

Problem-Solving Strategies: logic, working-backwards, guess-check, symmetry, invariants, extremal

Rules:
1. Return ONLY valid JSON in this exact format: {"tags": ["tag1", "tag2"]}
2. Use 1-4 tags per problem
3. Only use tags from the whitelist above
4. Choose tags based on the mathematical concepts needed to solve the problem
5. Do not explain or add any text outside the JSON"""


async def tag_problem(client: httpx.AsyncClient, problem: dict) -> list[str]:
    """Send a problem to Ollama and get back tags."""
    statement = problem.get("statement", "")
    choices = problem.get("choices", [])
    choices_text = "\n".join([f"  {chr(65+i)}) {c}" for i, c in enumerate(choices)])

    prompt = f"""Analyze this math problem and return appropriate concept tags as JSON.

Problem: {statement}

Answer choices:
{choices_text}

Return ONLY valid JSON: {{"tags": ["tag1", "tag2"]}}"""

    try:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "system": SYSTEM_PROMPT,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 100
                }
            },
            timeout=60.0
        )
        response.raise_for_status()

        result = response.json()
        response_text = result.get("response", "").strip()
        reasoning_text = result.get("thinking", "")

        # Try to parse JSON from response
        # Handle case where model wraps JSON in markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # Find JSON object in response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            data = json.loads(json_str)
            tags = data.get("tags", [])

            # Filter to only valid tags
            valid_tags: list[str] = []
            for t in tags:
                resolved = _resolve_tag(t)
                if resolved and resolved not in valid_tags:
                    valid_tags.append(resolved)
            if valid_tags:
                return valid_tags

        fallback_text = response_text or reasoning_text
        if fallback_text:
            return _extract_tags_from_text(fallback_text)

        return []

    except Exception as e:
        print(f"  Error tagging problem {problem.get('id', 'unknown')}: {e}")
        return []


async def tag_all_problems(
    problems_path: Path,
    output_path: Optional[Path] = None,
    batch_size: int = 5
) -> list[dict]:
    """Tag all problems in the problems.json file."""

    # Load problems
    with open(problems_path) as f:
        problems = json.load(f)

    print(f"Loaded {len(problems)} problems")
    print(f"Using model: {MODEL}")
    print(f"Ollama URL: {OLLAMA_URL}")
    print()

    # Process in batches
    async with httpx.AsyncClient() as client:
        for i in range(0, len(problems), batch_size):
            batch = problems[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(problems) + batch_size - 1)//batch_size}")

            # Process batch concurrently
            tasks = [tag_problem(client, p) for p in batch]
            results = await asyncio.gather(*tasks)

            # Update problems with tags
            for j, tags in enumerate(results):
                problem = problems[i + j]
                # Apply model tags first
                applied_tags = tags or []
                # If still empty, try heuristics on the problem text
                if not applied_tags:
                    applied_tags = _heuristic_tags_for_problem(problem)
                problem["tags"] = applied_tags
                print(f"  {problem['id']}: {applied_tags}")

    # Save results
    output = output_path or problems_path
    with open(output, "w") as f:
        json.dump(problems, f, indent=2)

    print(f"\nSaved {len(problems)} tagged problems to {output}")

    # Print summary
    tag_counts: dict[str, int] = {}
    for p in problems:
        for tag in p.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    print("\nTag distribution:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        print(f"  {tag}: {count}")

    return problems


def main():
    """Run the tagging pipeline."""
    import argparse

    global MODEL

    parser = argparse.ArgumentParser(description="Tag math problems using Ollama")
    parser.add_argument(
        "--input", "-i",
        default="backend/data/problems.json",
        help="Input problems JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file (defaults to overwriting input)"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=5,
        help="Number of problems to process concurrently"
    )
    parser.add_argument(
        "--model", "-m",
        default=MODEL,
        help=f"Ollama model to use (default: {MODEL})"
    )

    args = parser.parse_args()

    # Update model if specified
    MODEL = args.model

    # Resolve paths
    base_path = Path(__file__).parent.parent.parent
    input_path = base_path / args.input
    output_path = base_path / args.output if args.output else None

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return

    # Run tagging
    asyncio.run(tag_all_problems(input_path, output_path, args.batch_size))


if __name__ == "__main__":
    main()
