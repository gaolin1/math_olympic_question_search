"""Scraper for CEMC Gauss Competition problems from University of Waterloo.

Usage:
    # Try to download and cache HTML, then parse to problems.json
    python -m scraper.gauss_scraper --year 2025 --cache ./cache --output ./data

    # If download fails (site blocks your IP), manually save HTML files to cache dir:
    # - 2025Gauss7Contest.html
    # - 2025Gauss8Contest.html
    # - 2025GaussSolution.html
    # Then run again with same command - it will use cached files.
"""
import asyncio
import json
import re
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, Tag

from .models import Problem


# CEMC URL patterns
CONTEST_URL = "https://cemc.uwaterloo.ca/sites/default/files/documents/{year}/{year}Gauss{grade}Contest.html"
SOLUTION_URL = "https://cemc.uwaterloo.ca/sites/default/files/documents/{year}/{year}GaussSolution.html"


class GaussScraper:
    """Scraper for Gauss competition problems with automatic HTML caching."""

    def __init__(self, cache_dir: Path, output_dir: Path = Path(".")):
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, year: int, grade: int, is_solution: bool = False) -> Path:
        """Get the cache file path for a contest or solution."""
        if is_solution:
            return self.cache_dir / f"{year}GaussSolution.html"
        return self.cache_dir / f"{year}Gauss{grade}Contest.html"

    def _is_valid_html(self, html: str) -> bool:
        """Check if HTML content is valid (not an error page)."""
        if not html or len(html) < 500:
            return False
        if "Access denied" in html:
            return False
        return True

    async def _fetch_with_crawl4ai(self, url: str) -> Optional[str]:
        """Fetch a URL using crawl4ai."""
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

            browser_config = BrowserConfig(
                headless=True,
                ignore_https_errors=True,
                extra_args=["--disable-blink-features=AutomationControlled"],
            )

            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(wait_until="networkidle"),
                )
                if result.success and self._is_valid_html(result.html):
                    return result.html
                return None
        except ImportError:
            print("crawl4ai not installed. Run: pip install crawl4ai")
            return None
        except Exception as e:
            print(f"crawl4ai error: {e}")
            return None

    async def fetch_and_cache(self, year: int) -> dict[str, bool]:
        """Fetch contest pages and cache them. Returns status for each file."""
        status = {}

        # Fetch Grade 7 and Grade 8 contests
        for grade in [7, 8]:
            cache_path = self._get_cache_path(year, grade)
            key = f"grade_{grade}"

            if cache_path.exists() and self._is_valid_html(cache_path.read_text()):
                print(f"✓ Grade {grade} contest already cached: {cache_path}")
                status[key] = True
                continue

            url = CONTEST_URL.format(year=year, grade=grade)
            print(f"↓ Fetching Grade {grade} contest: {url}")

            html = await self._fetch_with_crawl4ai(url)
            if html:
                cache_path.write_text(html, encoding="utf-8")
                print(f"  ✓ Cached to {cache_path}")
                status[key] = True
            else:
                print(f"  ✗ Failed to fetch (site may be blocking). Save HTML manually to: {cache_path}")
                status[key] = False

        # Fetch solutions
        cache_path = self._get_cache_path(year, 0, is_solution=True)
        if cache_path.exists() and self._is_valid_html(cache_path.read_text()):
            print(f"✓ Solutions already cached: {cache_path}")
            status["solutions"] = True
        else:
            url = SOLUTION_URL.format(year=year)
            print(f"↓ Fetching solutions: {url}")

            html = await self._fetch_with_crawl4ai(url)
            if html:
                cache_path.write_text(html, encoding="utf-8")
                print(f"  ✓ Cached to {cache_path}")
                status["solutions"] = True
            else:
                print(f"  ✗ Failed to fetch. Save HTML manually to: {cache_path}")
                status["solutions"] = False

        return status

    def parse_from_cache(self, year: int) -> list[Problem]:
        """Parse problems from cached HTML files."""
        all_problems = []

        for grade in [7, 8]:
            cache_path = self._get_cache_path(year, grade)
            if not cache_path.exists():
                print(f"✗ Missing cache file: {cache_path}")
                continue

            html = cache_path.read_text(encoding="utf-8")
            if not self._is_valid_html(html):
                print(f"✗ Invalid HTML in cache: {cache_path}")
                continue

            print(f"◆ Parsing Grade {grade} contest from cache...")
            problems = self._parse_contest_page(html, year, grade)
            print(f"  Found {len(problems)} problems")
            all_problems.extend(problems)

        # Apply solutions
        solution_path = self._get_cache_path(year, 0, is_solution=True)
        if solution_path.exists():
            html = solution_path.read_text(encoding="utf-8")
            if self._is_valid_html(html):
                print(f"◆ Parsing solutions from cache...")
                solutions = self._parse_solution_page(html)
                applied = 0
                for problem in all_problems:
                    key = (problem.grade, problem.problem_number)
                    if key in solutions:
                        answer, solution = solutions[key]
                        if answer:
                            problem.answer = answer
                            applied += 1
                        if solution:
                            problem.solution = solution
                print(f"  Applied {applied} answers")

        return all_problems

    def _parse_contest_page(self, html: str, year: int, grade: int) -> list[Problem]:
        """Parse a Gauss contest page and extract problems."""
        soup = BeautifulSoup(html, "lxml")
        problems = []

        content = soup.find("body") or soup
        problem_sections = self._extract_problem_sections(content)

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

        return sorted(problems, key=lambda p: p.problem_number)

    def _extract_problem_sections(self, content: Tag) -> dict[int, tuple[str, list[str]]]:
        """Extract individual problems from the contest content."""
        problems = {}
        text = content.get_text(separator="\n", strip=True)

        # Pattern: number followed by period, then problem text
        problem_pattern = re.compile(
            r"(?:^|\n)\s*(\d{1,2})\.\s*(.+?)(?=(?:\n\s*\d{1,2}\.\s)|\Z)", re.DOTALL
        )

        matches = problem_pattern.findall(text)

        for num_str, problem_text in matches:
            num = int(num_str)
            if 1 <= num <= 25:
                statement, choices = self._extract_choices(problem_text)
                problems[num] = (statement.strip(), choices)

        return problems

    def _extract_choices(self, text: str) -> tuple[str, list[str]]:
        """Extract answer choices from problem text."""
        choices = []

        # Pattern for choices: (A) ... (B) ... etc.
        choice_pattern = re.compile(r"\(([A-E])\)\s*(.+?)(?=\([A-E]\)|$)", re.DOTALL)
        matches = choice_pattern.findall(text)

        if matches:
            first_choice_match = re.search(r"\(A\)", text)
            if first_choice_match:
                statement = text[: first_choice_match.start()].strip()
                for letter, choice_text in matches:
                    choices.append(f"({letter}) {choice_text.strip()}")
            else:
                statement = text
        else:
            statement = text

        # Pad to 5 choices if needed
        while len(choices) < 5:
            choices.append("")

        return statement, choices[:5]

    def _parse_solution_page(self, html: str) -> dict[tuple[int, int], tuple[str, str]]:
        """Parse solutions page and return mapping of (grade, problem_num) -> (answer, solution)."""
        soup = BeautifulSoup(html, "lxml")
        solutions = {}

        content = soup.find("body") or soup
        text = content.get_text(separator="\n", strip=True)

        # Look for answer patterns like "1. A" or "1. B"
        answer_pattern = re.compile(r"(\d{1,2})\.\s*([A-E])(?:\s|$|\n)")
        answer_matches = answer_pattern.findall(text)

        current_grade = 7

        for num_str, answer in answer_matches:
            num = int(num_str)
            if 1 <= num <= 25:
                # If we see problem 1 again, switch to grade 8
                if num == 1 and solutions.get((7, 1)):
                    current_grade = 8
                solutions[(current_grade, num)] = (answer, "")

        return solutions

    def save_problems(self, problems: list[Problem], filename: str = "problems.json") -> Path:
        """Save problems to JSON file."""
        output_path = self.output_dir / filename
        problems_data = [p.model_dump() for p in problems]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(problems_data, f, indent=2, ensure_ascii=False)

        print(f"● Saved {len(problems)} problems to {output_path}")
        return output_path

    async def run(self, year: int) -> list[Problem]:
        """Full workflow: fetch/cache HTML, parse, return problems."""
        print(f"\n{'='*60}")
        print(f"Gauss {year} Scraper")
        print(f"{'='*60}\n")

        # Step 1: Fetch and cache
        print("Step 1: Fetch and cache HTML files\n")
        await self.fetch_and_cache(year)

        # Step 2: Parse from cache
        print("\nStep 2: Parse problems from cache\n")
        problems = self.parse_from_cache(year)

        if not problems:
            print("\n✗ No problems parsed. Please check:")
            print(f"  1. Cache directory: {self.cache_dir}")
            print(f"  2. Expected files:")
            print(f"     - {year}Gauss7Contest.html")
            print(f"     - {year}Gauss8Contest.html")
            print(f"     - {year}GaussSolution.html")
            print("\n  If the website blocked downloads, manually save the HTML files")
            print("  from your browser to the cache directory and run again.")

        return problems


def print_urls(year: int, cache_dir: Path):
    """Print URLs for manual download."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Gauss {year} - URLs for Manual Download")
    print(f"{'='*60}\n")
    print("Open each URL in your browser and save as HTML:\n")

    files = [
        (CONTEST_URL.format(year=year, grade=7), f"{year}Gauss7Contest.html"),
        (CONTEST_URL.format(year=year, grade=8), f"{year}Gauss8Contest.html"),
        (SOLUTION_URL.format(year=year), f"{year}GaussSolution.html"),
    ]

    for url, filename in files:
        save_path = cache_dir / filename
        print(f"  URL:  {url}")
        print(f"  Save: {save_path}\n")

    print(f"After saving all files, run:")
    print(f"  python -m scraper.gauss_scraper --year {year} --cache {cache_dir}\n")


def main():
    """Main entry point for scraping."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape Gauss competition problems from CEMC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show URLs for manual download
  python -m scraper.gauss_scraper --year 2025 --urls

  # After saving HTML files, parse them
  python -m scraper.gauss_scraper --year 2025 --cache ./cache --output ./data
        """,
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Year to scrape (default: 2025)",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path("./cache"),
        help="Directory to cache HTML files (default: ./cache)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./data"),
        help="Output directory for problems.json (default: ./data)",
    )
    parser.add_argument(
        "--urls",
        action="store_true",
        help="Just print URLs for manual download (no scraping)",
    )
    args = parser.parse_args()

    # If --urls flag, just print URLs and exit
    if args.urls:
        print_urls(args.year, args.cache)
        return

    scraper = GaussScraper(cache_dir=args.cache, output_dir=args.output)
    problems = asyncio.run(scraper.run(args.year))

    if problems:
        scraper.save_problems(problems)
        print(f"\n✓ Success! Scraped {len(problems)} problems.")
    else:
        print("\n✗ No problems scraped. See instructions above.")
        exit(1)


if __name__ == "__main__":
    main()
