from dataclasses import dataclass

@dataclass(frozen=True)
class Prediction:
    student_id: str
    probability: float
    model_version: str

    def __post_init__(self):
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be in [0, 1]")
