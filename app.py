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

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# ===== HELPER: Find image with multiple extensions =====
def find_image_path(folder, name):
    """
    Tìm file ảnh với nhiều extension: .png, .jpg, .jpeg, .webp
    Trả về đường dẫn URL hoặc None
    """
    static_dir = os.path.join(BASE_DIR, "static", "images", folder)
    extensions = [".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG"]
    
    for ext in extensions:
        file_path = os.path.join(static_dir, f"{name}{ext}")
        if os.path.exists(file_path):
            return f"/static/images/{folder}/{name}{ext}"
    
    return None  # Không tìm thấy


# ===== LOAD DATA =====
def load_champions_data():
    path = os.path.join(DATA_DIR, "champions.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    result = []
    for c in raw:
        image_path = find_image_path("champions", c["name"])
        result.append({
            "name": c["name"],
            "cost": c["cost"],
            "traits": c["traits"],
            "roles": c.get("roles", []),
            "locked": c.get("locked", False),
            "image": image_path
        })

    return result



def load_traits_data():
    path = os.path.join(DATA_DIR, "traits.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    # Add image path to each trait
    result = {}
    for k, v in data.items():
        image_path = find_image_path("emblems", k)
        result[k] = {
            **v,
            "image": image_path  # Có thể là None nếu không tìm thấy
        }
    
    return result


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
    champions = load_champions_data()
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
    "Đồ Tể",
    "Xạ Thủ"
}

@app.route("/api/traits", methods=["GET"])
def get_traits():
    try:
        traits = load_traits_data()

        # ✅ CHỈ TRẢ NHỮNG TRAIT CÓ ẤN THỰC SỰ
        filtered_traits = {
            k: v
            for k, v in traits.items()
            if k in VALID_EMBLEMS
        }

        return jsonify({
            "success": True,
            "data": filtered_traits
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

        forced = set(data.get("forced", []))

        user_banned = set(data.get("banned", []))
        default_banned = set(DEFAULT_BANNED_CHAMPIONS)

        # 🚨 CHỈ check xung đột với ban do user chọn
        conflict = forced & user_banned

        if conflict:
            return jsonify({
                "success": False,
                "error": f"Champion đang bị cấm, hãy gỡ khỏi Ban trước: {', '.join(conflict)}"
            }), 400

        # ✅ Sau khi validate mới gộp ban
        banned = default_banned | user_banned

        # ✅ forced override banned (ban mặc định)
        banned -= forced


        emblems = {
            k: int(v)
            for k, v in data.get("emblems", {}).items()
            if k in VALID_EMBLEMS and int(v) > 0
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
