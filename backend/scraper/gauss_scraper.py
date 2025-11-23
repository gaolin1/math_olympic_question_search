"""Scraper for CEMC Gauss Competition problems from University of Waterloo."""
import json
import re
import time
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup, Tag

from .models import Problem, ProblemSet


# Browser-like headers to avoid 403 errors
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# CEMC URL patterns
CONTEST_URL = "https://cemc.uwaterloo.ca/sites/default/files/documents/{year}/{year}Gauss{grade}Contest.html"
SOLUTION_URL = "https://cemc.uwaterloo.ca/sites/default/files/documents/{year}/{year}GaussSolution.html"


class GaussScraper:
    """Scraper for Gauss competition problems."""

    def __init__(self, output_dir: Path = Path(".")):
        self.output_dir = output_dir
        self.client = httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30.0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with retry logic."""
        for attempt in range(3):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None

    def parse_contest_page(self, html: str, year: int, grade: int) -> list[Problem]:
        """Parse a Gauss contest page and extract problems."""
        soup = BeautifulSoup(html, "lxml")
        problems = []

        # Find all problem containers - CEMC uses various structures
        # Try to find problems by looking for numbered patterns
        content = soup.find("body") or soup

        # Extract text and find problem patterns
        # Problems typically start with a number followed by a period
        problem_sections = self._extract_problem_sections(content, year, grade)

        for prob_num, (statement, choices) in problem_sections.items():
            problem_id = Problem.create_id(year, grade, prob_num)
            url = CONTEST_URL.format(year=year, grade=grade)

            problem = Problem(
                id=problem_id,
                source="gauss",
                grade=grade,
                year=year,
                problem_number=prob_num,
                statement=statement,
                choices=choices,
                url=url,
            )
            problems.append(problem)

        return problems

    def _extract_problem_sections(
        self, content: Tag, year: int, grade: int
    ) -> dict[int, tuple[str, list[str]]]:
        """Extract individual problems from the contest content."""
        problems = {}

        # Get all text content
        text = content.get_text(separator="\n", strip=True)

        # Split by problem numbers (1. through 25.)
        # Pattern: start of line or after newline, number 1-25, followed by period
        problem_pattern = re.compile(r"(?:^|\n)\s*(\d{1,2})\.\s*(.+?)(?=(?:\n\s*\d{1,2}\.\s)|\Z)", re.DOTALL)

        matches = problem_pattern.findall(text)

        for num_str, problem_text in matches:
            num = int(num_str)
            if 1 <= num <= 25:
                # Extract choices (A) through (E)
                statement, choices = self._extract_choices(problem_text)
                problems[num] = (statement.strip(), choices)

        return problems

    def _extract_choices(self, text: str) -> tuple[str, list[str]]:
        """Extract answer choices from problem text."""
        choices = []

        # Pattern for choices: (A) ... (B) ... etc.
        choice_pattern = re.compile(
            r"\(([A-E])\)\s*(.+?)(?=\([A-E]\)|$)", re.DOTALL
        )
        matches = choice_pattern.findall(text)

        if matches:
            # Find where choices start
            first_choice_match = re.search(r"\(A\)", text)
            if first_choice_match:
                statement = text[: first_choice_match.start()].strip()
                for letter, choice_text in matches:
                    choices.append(f"({letter}) {choice_text.strip()}")
            else:
                statement = text
        else:
            statement = text

        # Ensure we have exactly 5 choices, pad if needed
        while len(choices) < 5:
            choices.append("")

        return statement, choices[:5]

    def parse_solution_page(self, html: str) -> dict[tuple[int, int], tuple[str, str]]:
        """Parse solutions page and return mapping of (grade, problem_num) -> (answer, solution)."""
        soup = BeautifulSoup(html, "lxml")
        solutions = {}

        content = soup.find("body") or soup
        text = content.get_text(separator="\n", strip=True)

        # Solutions typically follow pattern: problem number, then answer, then explanation
        # The solution page often has sections for Grade 7 and Grade 8

        # Try to find answer key sections first
        # Pattern: 1. A, 2. B, 3. C, etc. or in table format

        # Look for answer patterns
        answer_pattern = re.compile(r"(\d{1,2})\.\s*([A-E])(?:\s|$|\n)")
        answer_matches = answer_pattern.findall(text)

        current_grade = 7  # Default, will try to detect grade switches

        for num_str, answer in answer_matches:
            num = int(num_str)
            if 1 <= num <= 25:
                # If we see problem 1 again, might be switching to grade 8
                if num == 1 and solutions.get((7, 1)):
                    current_grade = 8
                solutions[(current_grade, num)] = (answer, "")

        # Try to extract detailed solutions as well
        solution_pattern = re.compile(
            r"(?:Problem|Question)?\s*(\d{1,2})[.\s]*(.+?)(?=(?:Problem|Question)?\s*\d{1,2}[.\s]|\Z)",
            re.DOTALL | re.IGNORECASE,
        )

        # This is a simplified extraction - real pages may need more specific parsing
        for grade in [7, 8]:
            for num in range(1, 26):
                if (grade, num) not in solutions:
                    solutions[(grade, num)] = ("", "")

        return solutions

    def scrape_year(self, year: int) -> list[Problem]:
        """Scrape all problems for a given year (both Grade 7 and Grade 8)."""
        all_problems = []

        for grade in [7, 8]:
            url = CONTEST_URL.format(year=year, grade=grade)
            print(f"Fetching Grade {grade} contest: {url}")

            html = self.fetch_page(url)
            if html:
                problems = self.parse_contest_page(html, year, grade)
                print(f"  Found {len(problems)} problems")
                all_problems.extend(problems)
            else:
                print(f"  Failed to fetch Grade {grade} contest")

            time.sleep(1)  # Be polite

        # Fetch solutions
        solution_url = SOLUTION_URL.format(year=year)
        print(f"Fetching solutions: {solution_url}")

        solution_html = self.fetch_page(solution_url)
        if solution_html:
            solutions = self.parse_solution_page(solution_html)

            # Match solutions to problems
            for problem in all_problems:
                key = (problem.grade, problem.problem_number)
                if key in solutions:
                    answer, solution = solutions[key]
                    problem.answer = answer if answer else None
                    problem.solution = solution if solution else None

            print(f"  Applied solutions to problems")
        else:
            print(f"  Failed to fetch solutions")

        return all_problems

    def save_problems(self, problems: list[Problem], filename: str = "problems.json"):
        """Save problems to JSON file."""
        output_path = self.output_dir / filename

        # Convert to list of dicts
        problems_data = [p.model_dump() for p in problems]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(problems_data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(problems)} problems to {output_path}")
        return output_path


    def load_from_local_files(
        self, year: int, contest_dir: Path
    ) -> list[Problem]:
        """Load problems from locally saved HTML files.

        Expected files in contest_dir:
        - {year}Gauss7Contest.html
        - {year}Gauss8Contest.html
        - {year}GaussSolution.html
        """
        all_problems = []

        for grade in [7, 8]:
            filename = f"{year}Gauss{grade}Contest.html"
            filepath = contest_dir / filename

            if filepath.exists():
                print(f"Loading Grade {grade} contest from: {filepath}")
                html = filepath.read_text(encoding="utf-8")
                problems = self.parse_contest_page(html, year, grade)
                print(f"  Found {len(problems)} problems")
                all_problems.extend(problems)
            else:
                print(f"  File not found: {filepath}")

        # Load solutions
        solution_filename = f"{year}GaussSolution.html"
        solution_path = contest_dir / solution_filename

        if solution_path.exists():
            print(f"Loading solutions from: {solution_path}")
            solution_html = solution_path.read_text(encoding="utf-8")
            solutions = self.parse_solution_page(solution_html)

            for problem in all_problems:
                key = (problem.grade, problem.problem_number)
                if key in solutions:
                    answer, solution = solutions[key]
                    problem.answer = answer if answer else None
                    problem.solution = solution if solution else None

            print(f"  Applied solutions to problems")
        else:
            print(f"  Solutions file not found: {solution_path}")

        return all_problems


def main():
    """Main entry point for scraping."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Gauss competition problems")
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Year to scrape (default: 2025)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("."),
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "--local",
        type=Path,
        default=None,
        help="Load from local HTML files in this directory instead of scraping",
    )
    args = parser.parse_args()

    with GaussScraper(output_dir=args.output) as scraper:
        if args.local:
            problems = scraper.load_from_local_files(args.year, args.local)
        else:
            problems = scraper.scrape_year(args.year)

        if problems:
            scraper.save_problems(problems)
        else:
            print("No problems found. If scraping failed, try using --local with saved HTML files.")
            print("Note: CEMC website may block automated requests. Download HTML files manually and use --local.")


if __name__ == "__main__":
    main()
