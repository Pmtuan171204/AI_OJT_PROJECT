"""Validate the canonical dataset without creating duplicate CSV files."""
from pathlib import Path
from .loader import load_data

def prepare_dataset(repo):
    directory = Path(repo).resolve() / "data"
    _, warnings = load_data(directory)
    return directory, warnings
