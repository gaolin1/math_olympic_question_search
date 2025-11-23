"""Data models for Math Olympic problems."""
from typing import Optional
from pydantic import BaseModel


class Problem(BaseModel):
    """Model for a competition problem."""
    id: str  # e.g., "gauss-2025-g7-15"
    source: str = "gauss"
    grade: int  # 7 or 8
    year: int  # e.g., 2025
    problem_number: int  # 1-25
    statement: str  # Problem text (may contain LaTeX)
    choices: list[str]  # Answer options A-E
    answer: Optional[str] = None  # Correct answer letter
    solution: Optional[str] = None  # Solution explanation
    tags: list[str] = []  # Concept tags
    url: str  # Source URL

    @classmethod
    def create_id(cls, year: int, grade: int, problem_number: int) -> str:
        """Generate a unique problem ID."""
        return f"gauss-{year}-g{grade}-{problem_number}"


class ProblemSet(BaseModel):
    """Collection of problems."""
    problems: list[Problem] = []
