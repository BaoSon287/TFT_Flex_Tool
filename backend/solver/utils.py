import json
import os
import sys


def resource_path(relative_path: str) -> str:
    """
    Trả về path tuyệt đối cho cả:
    - chạy source
    - chạy uvicorn
    - build exe (PyInstaller)
    """
    # PyInstaller
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        # backend/solver/utils.py -> backend/
        base_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

    return os.path.join(base_path, relative_path)


def load_json(relative_path: str):
    """
    Load JSON an toàn cho web
    Ví dụ:
        load_json("data/champions.json")
    """
    path = resource_path(relative_path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)
