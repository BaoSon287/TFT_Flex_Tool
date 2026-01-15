from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.app.api import router as api_router


# ===== APP =====
app = FastAPI(
    title="TFT Solver API",
    description="Bronze & Ryze team solver for TFT",
    version="1.0.0",
)


# ===== CORS (CHO FRONTEND) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # production thì đổi domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== API ROUTER =====
app.include_router(api_router)


# ===== STATIC FRONTEND =====
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIR, html=True),
        name="frontend",
    )


# ===== HEALTH CHECK =====
@app.get("/health")
def health():
    return {"status": "ok"}
