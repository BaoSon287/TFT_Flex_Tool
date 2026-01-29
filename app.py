from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
import sys

# Import solvers
from bronze import solve as solve_bronze
from ryze import solve as solve_ryze
from models.champion import Champion
from models.trait import Trait

app = Flask(__name__)
CORS(app)

# ===== LOAD DATA =====
def load_champions_data(banned=None):
    if banned is None:
        banned = []
    
    try:
        with open("data/champions.json", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return []
    
    res = []
    for c in raw:
        if c["name"] not in banned:
            res.append({
                "name": c["name"],
                "cost": c["cost"],
                "traits": c["traits"],
                "roles": c.get("roles", []),
                "locked": c.get("locked", False)
            })
    return res

def load_traits_data():
    try:
        with open("data/traits.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# ===== API ROUTES =====
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/champions", methods=["GET"])
def get_champions():
    """Get all available champions"""
    try:
        champions = load_champions_data()
        return jsonify({"success": True, "data": champions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/traits", methods=["GET"])
def get_traits():
    """Get all traits"""
    try:
        traits = load_traits_data()
        return jsonify({"success": True, "data": traits})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/solve", methods=["POST"])
def solve():
    """Run the solver"""
    try:
        data = request.json
        
        solver_type = data.get("solver", "ryze").lower()
        max_team = data.get("max_team", 8)
        time_limit = data.get("time_limit", 20)
        forced = data.get("forced", [])
        banned = data.get("banned", [])
        emblems = data.get("emblems", {})
        
        # Convert string emblem keys to integers if needed
        emblems = {k: int(v) for k, v in emblems.items() if int(v) > 0}
        
        # Choose solver
        if solver_type == "bronze":
            result = solve_bronze(
                max_team=max_team,
                time_limit=time_limit,
                forced=forced,
                banned=banned,
                emblems=emblems
            )
        else:  # ryze is default
            result = solve_ryze(
                max_team=max_team,
                time_limit=time_limit,
                forced=forced,
                banned=banned,
                emblems=emblems
            )
        
        # Format result for JSON
        formatted_result = []
        for item in result:
            team_names = [c.name for c in item["team"]]
            formatted_result.append({
                "score": item["score"],
                "cost": item["cost"],
                "team": team_names,
                "team_size": len(team_names)
            })
        
        return jsonify({
            "success": True,
            "data": formatted_result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
