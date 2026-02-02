import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json

# Import solvers
from bronze import solve as solve_bronze
from ryze import solve as solve_ryze

# ===== DEFAULT giống PyQt =====
DEFAULT_BANNED_CHAMPIONS = [
    "Aatrox",
    "Aphelios",
    "Zoe",
    "Leona",
    "Diana",
    "T-Hex",
    "Yone",
    "Baron Nashor",
    "Zaahen",
    "Brock",
    "Galio",
    "Aurelion Sol",
    "Tahm Kench",
    "Gwen",
    "Kalista",
    "Thresh",
    "Veigar",
]

DEFAULT_FORCED_CHAMPIONS = []

app = Flask(__name__)
CORS(app)

# ===== LOAD DATA =====
def load_champions_data(banned=None):
    if banned is None:
        banned = []

    path = os.path.join(DATA_DIR, "champions.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    banned_lc = {b.lower() for b in banned}
    return [
        {
            "name": c["name"],
            "cost": c["cost"],
            "traits": c["traits"],
            "roles": c.get("roles", []),
            "locked": c.get("locked", False)
        }
        for c in raw
        if c["name"].lower() not in banned_lc
    ]



def load_traits_data():
    path = os.path.join(DATA_DIR, "traits.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ===== ROUTES =====
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/api/defaults", methods=["GET"])
def get_defaults():
    return jsonify({
        "banned": DEFAULT_BANNED_CHAMPIONS,
        "forced": []
    })
@app.route("/api/champions", methods=["GET"])
def get_champions():
    champions = load_champions_data(
        banned=DEFAULT_BANNED_CHAMPIONS
    )
    return jsonify({
        "success": True,
        "data": champions,
        "default_banned": DEFAULT_BANNED_CHAMPIONS
    })



VALID_EMBLEMS = {
    "Bilgewater",
    "Chinh Phạt",
    "Cảnh Vệ",
    "Cực Tốc",
    "Demacia",
    "Dũng Sĩ",
    "Freljord",
    "Hư Không",
    "Ionia",
    "Ixtal",
    "Nhiễu Loạn",
    "Noxus",
    "Pháp Sư",
    "Piltover",
    "Thuật Sĩ",
    "Viễn Kích",
    "Vệ Quân",
    "Yordle",
    "Zaun",
    "Đấu Sĩ",
    "Đồ Tể"
}

@app.route("/api/traits", methods=["GET"])
def get_traits():
    try:
        traits = load_traits_data()

        # 🔥 CHỈ GIỮ CÁC ẤN HỢP LỆ
        filtered = {
            k: v
            for k, v in traits.items()
            if k in VALID_EMBLEMS
        }

        return jsonify({
            "success": True,
            "data": filtered
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



@app.route("/api/solve", methods=["POST"])
def solve():
    try:
        data = request.json or {}

        solver_type = data.get("solver", "ryze").lower()
        max_team = data.get("max_team", 8)
        time_limit = data.get("time_limit", 20)

        forced = data.get("forced", DEFAULT_FORCED_CHAMPIONS)
        banned = set(DEFAULT_BANNED_CHAMPIONS)
        banned.update(data.get("banned", []))

        emblems = {
            k: int(v)
            for k, v in data.get("emblems", {}).items()
            if int(v) > 0
        }

        solver = solve_bronze if solver_type == "bronze" else solve_ryze

        result = solver(
            max_team=max_team,
            time_limit=time_limit,
            forced=list(forced),
            banned=list(banned),
            emblems=emblems
        )

        formatted = []
        for item in result:
            formatted.append({
                "score": item["score"],
                "cost": item["cost"],
                "team": [c.name for c in item["team"]],
                "team_size": len(item["team"])
            })

        return jsonify({"success": True, "data": formatted})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
