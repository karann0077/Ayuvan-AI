"""Safe concept lookup helper, NOT a clinical natural-language safety screen.
Raw text must go to a separately validated extractor; negation must be handled there.
"""
from pathlib import Path
import yaml

CONCEPTS = yaml.safe_load((Path(__file__).resolve().parents[2] / "clinical" / "concepts" / "symptoms.yaml").read_text())

def list_synonyms(code: str) -> list[str]:
    return CONCEPTS.get(code, {}).get("synonyms", [])
