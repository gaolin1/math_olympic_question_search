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
import base64
from pathlib import Path
from typing import Optional

import numpy as np
import cv2
import requests
from bs4 import BeautifulSoup, Tag

# Support running as both module and script
try:
    from .models import Problem
except ImportError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))
    from models import Problem


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
        self._ocr_engine = None

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

    def _fetch_with_requests(self, url: str) -> Optional[str]:
        """Primary fetch using requests with a browsery User-Agent."""
        try:
            import requests

            resp = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                },
                timeout=20,
            )
            if resp.status_code == 200 and self._is_valid_html(resp.text):
                return resp.text
            print(f"requests fetch failed ({resp.status_code}) for {url}")
            return None
        except Exception as e:
            print(f"requests fetch error for {url}: {e}")
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

            # Try lightweight HTTP first; fall back to headless browser only if needed
            html = self._fetch_with_requests(url)
            if not html:
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

            html = self._fetch_with_requests(url)
            if not html:
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
        base_url = CONTEST_URL.format(year=year, grade=grade)
        problem_sections = self._extract_problem_sections(content, base_url)

        for prob_num, (statement, choices, images) in problem_sections.items():
            problem_id = Problem.create_id(year, grade, prob_num)

            problem = Problem(
                id=problem_id,
                source="gauss",
                grade=grade,
                year=year,
                problem_number=prob_num,
                statement=statement,
                choices=choices,
                images=images,
                url=base_url,
            )
            problems.append(problem)

        return sorted(problems, key=lambda p: p.problem_number)

    def _clean_text(self, text: str) -> str:
        """Normalize whitespace and fix common encoding artifacts."""
        def _fix_encoding(s: str) -> str:
            try:
                return s.encode("latin1").decode("utf-8")
            except Exception:
                return s

        text = _fix_encoding(text)
        text = re.sub(r"Hide/Reveal Description.*", "", text, flags=re.IGNORECASE)
        text = text.replace("â", " ")
        return re.sub(r"\s+", " ", text).strip()

    def _ensure_ocr(self):
        """Lazily initialize the Mineru OCR engine."""
        if self._ocr_engine is None:
            try:
                from mineru.model.ocr.pytorch_paddle import PytorchPaddleOCR  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "Mineru OCR is required for image parsing. Install with pip install mineru"
                ) from exc

            self._ocr_engine = PytorchPaddleOCR()

    def _extract_image_as_base64(self, img_tag: Tag, base_url: str = "") -> Optional[str]:
        """Extract an image from an <img> tag and return as base64 data URI.

        Args:
            img_tag: BeautifulSoup img tag
            base_url: Base URL for resolving relative image paths

        Returns:
            Base64 data URI string (e.g., "data:image/png;base64,...") or None if extraction fails
        """
        src = img_tag.get("src", "")

        # Already a data URI - return as-is
        if src.startswith("data:image"):
            return src

        # No source
        if not src:
            return None

        # Resolve relative URLs
        if not src.startswith(("http://", "https://")):
            if base_url:
                from urllib.parse import urljoin
                src = urljoin(base_url, src)
            else:
                return None

        # Fetch the image
        try:
            resp = requests.get(
                src,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=15
            )
            if resp.status_code != 200:
                return None

            # Determine content type
            content_type = resp.headers.get("Content-Type", "image/png")
            if ";" in content_type:
                content_type = content_type.split(";")[0].strip()

            # Encode as base64
            b64_data = base64.b64encode(resp.content).decode("utf-8")
            return f"data:{content_type};base64,{b64_data}"
        except Exception as e:
            print(f"  Warning: Failed to fetch image {src}: {e}")
            return None

    def _ocr_image(self, img_tag: Tag) -> str:
        """Run OCR on an <img> tag using Mineru; fall back to alt text if OCR fails."""
        src = img_tag.get("src", "")
        data: bytes | None = None

        if src.startswith("data:image"):
            try:
                b64 = src.split(",", 1)[1]
                data = base64.b64decode(b64)
            except Exception:
                data = None
        elif src:
            try:
                resp = requests.get(src, timeout=15)
                if resp.status_code == 200:
                    data = resp.content
            except Exception:
                data = None

        if not data:
            return self._clean_text(img_tag.get("alt", ""))

        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return self._clean_text(img_tag.get("alt", ""))

        try:
            self._ensure_ocr()
            ocr_res = self._ocr_engine.ocr(img, det=True, rec=True)
            texts = []
            for page in ocr_res:
                for entry in page:
                    if len(entry) >= 2 and isinstance(entry[1], tuple):
                        txt, conf = entry[1][0], entry[1][1]
                        if txt:
                            texts.append((conf, txt))
            if texts:
                best = max(texts, key=lambda t: t[0])[1]
                return self._clean_text(best)
        except Exception:
            pass

        return self._clean_text(img_tag.get("alt", ""))

    def _extract_problem_sections(self, content: Tag, base_url: str = "") -> dict[int, tuple[str, list[str], list[str]]]:
        """Extract individual problems from the contest content.

        The 2025 HTML uses numbered <ol type="1"> lists where each question is
        represented by a top-level <li> that contains the statement and a
        nested list of five answer options. We walk the top-level items only
        (recursive=False) and pull choices from the nested <li> tags.

        Returns:
            Dict mapping problem_number to (statement, choices, images) tuple.
            Images are base64 data URIs.
        """
        problems: dict[int, tuple[str, list[str], list[str]]] = {}
        ol_lists = content.find_all("ol", attrs={"type": "1"})
        problem_number = 1

        # Drop hidden long descriptions that pollute statements/choices
        for desc in content.find_all(id=re.compile(r"^longdesc", re.IGNORECASE)):
            desc.decompose()

        for ol in ol_lists:
            items = ol.find_all("li", recursive=False)
            for item in items:
                # Collect images from this problem section
                images: list[str] = []
                for img_tag in item.find_all("img"):
                    img_data = self._extract_image_as_base64(img_tag, base_url)
                    if img_data:
                        images.append(img_data)

                # Prefer only the direct paragraph text for the statement to avoid pulling choices
                direct_paras = item.find_all("p", recursive=False)
                if direct_paras:
                    statement_raw = " ".join(self._clean_text(p.get_text(" ", strip=True)) for p in direct_paras)
                else:
                    statement_raw = self._clean_text(item.get_text(" ", strip=True))

                nested_ols = item.find_all("ol")
                choice_tags = []
                if nested_ols:
                    # Prefer the last nested list (skips earlier descriptive lists)
                    choice_tags = nested_ols[-1].find_all("li", recursive=False)
                if not choice_tags:
                    choice_tags = item.find_all("li")

                choices = []
                for li in choice_tags:
                    txt = self._clean_text(li.get_text(" ", strip=True))
                    if not txt:
                        img = li.find("img")
                        if img:
                            txt = self._ocr_image(img)
                    choices.append(txt)
                choices = choices[:5]

                # Ensure exactly 5 choices
                while len(choices) < 5:
                    choices.append("")

                problems[problem_number] = (statement_raw, choices, images)
                problem_number += 1

        return problems

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
