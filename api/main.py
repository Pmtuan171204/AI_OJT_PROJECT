from fastapi import FastAPI
from api.routes import health, prediction

app = FastAPI(title="AI OJT Risk", version="0.2.0")
app.include_router(health.router)
app.include_router(prediction.router)
