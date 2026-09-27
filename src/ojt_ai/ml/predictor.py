"""ML is intentionally unavailable; use risk_service for rule-based results."""
class ModelNotReadyError(RuntimeError):
    pass

class Predictor:
    def predict(self, features):
        raise ModelNotReadyError("No trained ML model is available. Rule-based eligibility is provided separately.")
