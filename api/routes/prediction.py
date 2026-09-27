from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from api.dependencies import get_data_directory, get_rules
from ojt_ai.data.loader import load_data
from ojt_ai.data.validator import DataError
from ojt_ai.services.risk_service import analyze
from ojt_ai.rules.eligibility import Rules

router = APIRouter()
class PredictionRequest(BaseModel):
    evaluation_term: str = Field(min_length=1)
    target_term: str = Field(min_length=1)

@router.post("/prediction")
def predict(request: PredictionRequest, directory: Path = Depends(get_data_directory), rules: Rules = Depends(get_rules)):
    try:
        tables, warnings = load_data(directory)
        result = analyze(tables, request.evaluation_term, request.target_term, rules)
        return {"mode": "rules", **result, "warnings": warnings}
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Prepared dataset unavailable. Run preprocessing first.")
    except DataError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
