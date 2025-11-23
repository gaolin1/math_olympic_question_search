from pathlib import Path

from backend.scraper.gauss_scraper import GaussScraper


def test_gauss_scraper_parses_grade7_cache():
    cache_dir = Path("backend/cache")
    html = (cache_dir / "2025Gauss7Contest.html").read_text(encoding="utf-8")
    scraper = GaussScraper(cache_dir=cache_dir)

    problems = scraper._parse_contest_page(html, year=2025, grade=7)

    assert len(problems) == 25

    p4 = next(p for p in problems if p.problem_number == 4)
    assert p4.choices == [
        "one circle",
        "two circles",
        "three circles",
        "four circles",
        "eight circles",
    ]

    p24 = next(p for p in problems if p.problem_number == 24)
    assert p24.choices == ["\\(A\\)", "\\(B\\)", "\\(C\\)", "\\(D\\)", "\\(E\\)"]
    assert "Hide/Reveal" not in p24.statement
