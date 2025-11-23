"""Tagging pipeline for math problems."""
from .tagger import tag_all_problems, tag_problem, ALL_TAGS, TAG_WHITELIST

__all__ = ["tag_all_problems", "tag_problem", "ALL_TAGS", "TAG_WHITELIST"]
