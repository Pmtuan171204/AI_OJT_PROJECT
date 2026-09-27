from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "prediction_mode": "rules", "ml_model_ready": False}
