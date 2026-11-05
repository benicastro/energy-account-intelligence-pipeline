"""Utilities for standardizing account data."""


def normalize_company_name(name: str | None) -> str | None:
    """Normalize whitespace in a company name.

    Preserve capitalization, punctuation, and legal suffixes.
    Return None for missing or blank names.
    """
    if name is None:
        return None

    normalized = " ".join(name.split())

    return normalized or None
