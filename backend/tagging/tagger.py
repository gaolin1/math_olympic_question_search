"""Tagging pipeline using Ollama to tag math problems with concept tags."""
import json
import httpx
import asyncio
from pathlib import Path
from typing import Optional

# Tag whitelist organized by category
TAG_WHITELIST = {
    "Number Theory": [
        "divisibility", "primes", "factors", "gcd-lcm", "remainders",
        "exponents", "powers-and-patterns", "digits", "parity"
    ],
    "Arithmetic & Algebra": [
        "fractions", "ratios", "percentages", "expressions", "equations",
        "substitution", "patterns", "sequences", "inequalities", "polynomials"
    ],
    "Geometry": [
        "triangles", "angles", "similarity", "circles", "coordinates",
        "distance", "area", "perimeter", "3d-geometry", "transformations"
    ],
    "Combinatorics & Probability": [
        "counting", "arrangements", "casework", "probability", "paths"
    ],
    "Word Problems & Applications": [
        "rates", "averages", "money", "tables-and-graphs"
    ],
    "Problem-Solving Strategies": [
        "logic", "working-backwards", "guess-check", "symmetry", "invariants", "extremal"
    ]
}

# Flatten all tags for validation
ALL_TAGS = [tag for tags in TAG_WHITELIST.values() for tag in tags]

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
            valid_tags = [t for t in tags if t in ALL_TAGS]
            return valid_tags

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
                problem["tags"] = tags
                print(f"  {problem['id']}: {tags}")

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
    global MODEL
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
