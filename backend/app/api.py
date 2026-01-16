from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import json
import os

from backend.solver import bronze, ryze

app = FastAPI()


# ===== MODEL =====
class SolveRequest(BaseModel):
    max_team: int = 8
    time_limit: float = 20
    forced: List[str] = []
    banned: List[str] = []
    emblems: Dict[str, int] = {}


# ===== ROOT =====
@app.get("/")
def root():
    return {"status": "API is running"}


# ===== DEFAULT CONFIG (GIỐNG PYQT) =====
@app.get("/config/defaults")
def get_defaults():
    return {
        "forced": ["Ryze", "Ahri"],
        "banned": [
            "Aatrox",
            "Aphelios",
            "Zoe",
            "Leona",
            "Diana",
            "Aurelion Sol"
        ]
    }


# ===== LOAD TRAITS =====
@app.get("/data/traits")
def get_traits():
    path = os.path.join("backend", "data", "traits.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ===== SOLVER =====
@app.post("/solve/bronze")
def solve_bronze(req: SolveRequest):
    return bronze.solve(
        max_team=req.max_team,
        time_limit=req.time_limit,
        forced=req.forced,
        banned=req.banned,
        emblems=req.emblems
    )


@app.post("/solve/ryze")
def solve_ryze(req: SolveRequest):
    return ryze.solve(
        max_team=req.max_team,
        time_limit=req.time_limit,
        forced=req.forced,
        banned=req.banned,
        emblems=req.emblems
    )
