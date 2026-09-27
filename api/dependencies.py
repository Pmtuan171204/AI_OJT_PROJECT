import os
from pathlib import Path
from ojt_ai.rules.eligibility import load_rules

ROOT = Path(__file__).resolve().parents[1]
def get_data_directory():
    path = Path(os.environ.get("OJT_DATA_DIR", "data"))
    return path if path.is_absolute() else ROOT/path

def get_rules():
    return load_rules(ROOT/"configs/thresholds.yaml")
