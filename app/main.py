from fastapi import FastAPI

from app.database import init_db
from app.models import TaskType
from app.synthetic_generator import build_generation_prompt

app = FastAPI(title="Model Auto Trainer", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/synthetic/prompt")
def synthetic_prompt(task_type: TaskType, seed_text: str, count: int = 10) -> dict:
    prompt = build_generation_prompt(task_type=task_type, seed_text=seed_text, count=count)
    return {"prompt": prompt}
