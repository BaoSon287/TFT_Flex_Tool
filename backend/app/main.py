from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import app as api_app

app = FastAPI(title="TFT Team Solver")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount toàn bộ api
app.mount("", api_app)
