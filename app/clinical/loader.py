"""Shared loader for the immutable, versioned pathway assets."""

from functools import lru_cache
from pathlib import Path

from .registry import Registry

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def registry() -> Registry:
    return Registry(ROOT / "clinical" / "pathways")
