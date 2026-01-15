from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict

from backend.solver import bronze, ryze


router = APIRouter(tags=["Solver"])


# ===== REQUEST MODEL (DÙNG CHUNG) =====
class SolveRequest(BaseModel):
    max_team: int = 8
    time_limit: float = 1.0
    forced: List[str] = []
    banned: List[str] = []
    emblems: Dict[str, int] = {}


# ===== BRONZE =====
@router.post("/solve/bronze")
def solve_bronze(req: SolveRequest):
    return bronze.solve(
        max_team=req.max_team,
        time_limit=req.time_limit,
        forced=req.forced,
        banned=req.banned,
        emblems=req.emblems,
    )


# ===== RYZE =====
@router.post("/solve/ryze")
def solve_ryze(req: SolveRequest):
    return ryze.solve(
        max_team=req.max_team,
        time_limit=req.time_limit,
        forced=req.forced,
        banned=req.banned,
        emblems=req.emblems,
    )
