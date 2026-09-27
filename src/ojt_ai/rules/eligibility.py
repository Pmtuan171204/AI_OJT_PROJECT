"""Deterministic OJT policy and class allocation."""
from dataclasses import dataclass
import json

@dataclass(frozen=True)
class Rules:
    min_credits: int = 70
    max_failed: int = 2
    class_min: int = 18
    class_target: int = 20
    class_max: int = 22


def allocate_classes(count, rules=Rules()):
    """Maximize placed students, then prefer sizes close to target."""
    candidates = []
    for classes in range(1, count // rules.class_min + 1):
        placed = min(count, classes * rules.class_max)
        base, extra = divmod(placed, classes)
        sizes = [base + 1] * extra + [base] * (classes - extra)
        deviation = sum(abs(size - rules.class_target) for size in sizes)
        candidates.append((count - placed, deviation, classes, sizes))
    if not candidates:
        return [], count
    waiting, _, _, sizes = min(candidates)
    return sizes, waiting



def load_rules(path):
    """Config files use the JSON subset of YAML; no YAML dependency required."""
    with open(path, encoding="utf-8") as stream:
        values = json.load(stream)
    rules = Rules(**values)
    if any(type(value) is not int for value in values.values()):
        raise ValueError("Thresholds must be integers")
    if not (0 < rules.class_min <= rules.class_target <= rules.class_max):
        raise ValueError("Invalid class size thresholds")
    if rules.min_credits < 0 or rules.max_failed < 0:
        raise ValueError("OJT thresholds cannot be negative")
    return rules
