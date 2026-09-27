import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ojt_ai.ml.evaluator import evaluate

if __name__ == "__main__":
    try:
        evaluate()
    except NotImplementedError as exc:
        raise SystemExit(str(exc))
