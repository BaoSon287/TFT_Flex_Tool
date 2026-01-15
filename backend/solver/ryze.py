import json
import time
from typing import List, Dict

from backend.models.champion import Champion
from backend.models.trait import Trait
from backend.solver.utils import resource_path


# ================= CONFIG =================
TOP_K = 5

MIN_TANK = 2
MIN_CARRY = 2
MIN_COST = 4

TARGON_TRAIT = "Targon"
IGNORED_TRAITS = {"Darkin"}

ORIGIN_WEIGHT = 3
CLASS_WEIGHT = 1


# ================= LOAD DATA =================
def load_champions(banned: List[str], path: str | None = None) -> List[Champion]:
    if path is None:
        path = resource_path("data/champions.json")

    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    champions = []
    for c in raw:
        if c["name"] in banned:
            continue

        champions.append(
            Champion(
                name=c["name"],
                cost=c["cost"],
                traits=c["traits"],
                roles=c.get("roles", []),
                locked=c.get("locked", False),
            )
        )
    return champions


def load_traits(path: str | None = None) -> Dict[str, Trait]:
    if path is None:
        path = resource_path("data/traits.json")

    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    return {
        name: Trait(name, data["thresholds"], data["type"])
        for name, data in raw.items()
    }


# ================= TRAIT LOGIC =================
def trait_need(trait_name: str, trait: Trait) -> int | float:
    if trait_name in IGNORED_TRAITS:
        return float("inf")
    if trait_name == TARGON_TRAIT:
        return 1
    return min(trait.thresholds)


# ================= HEURISTICS =================
def champion_value(champ: Champion, traits: Dict[str, Trait]) -> float:
    score = 0.0
    for t in champ.traits:
        if t in IGNORED_TRAITS or t not in traits:
            continue

        need = trait_need(t, traits[t])
        weight = ORIGIN_WEIGHT if traits[t].type == "origin" else CLASS_WEIGHT
        score += weight / need
    return score


def upper_bound(trait_counts, traits, remain):
    score = 0
    for t, tr in traits.items():
        if t in IGNORED_TRAITS:
            continue

        cur = trait_counts.get(t, 0)
        need = trait_need(t, tr)

        if cur < need and need - cur <= remain:
            score += ORIGIN_WEIGHT if tr.type == "origin" else CLASS_WEIGHT
    return score


# ================= ROLE CHECK =================
def count_roles(team: List[Champion]):
    tank = carry = 0
    for c in team:
        if c.cost >= MIN_COST:
            tank += "tank" in c.roles
            carry += "carry" in c.roles
    return tank, carry


def valid_team(team: List[Champion]) -> bool:
    tank, carry = count_roles(team)
    return tank >= MIN_TANK and carry >= MIN_CARRY


# ================= SERIALIZE =================
def serialize_team(team: List[Champion]):
    return [
        {
            "name": c.name,
            "cost": c.cost,
            "traits": c.traits,
            "roles": c.roles,
            "locked": getattr(c, "locked", False),
        }
        for c in team
    ]


# ================= SOLVER =================
def solve(
    max_team: int,
    time_limit: float,
    forced: List[str],
    banned: List[str],
    emblems: Dict[str, int],
):
    traits = load_traits()
    champions = load_champions(banned)

    champions.sort(
        key=lambda c: champion_value(c, traits),
        reverse=True,
    )

    forced_champs = [c for c in champions if c.name in forced]
    remain = [c for c in champions if c.name not in forced]

    trait_counts = dict(emblems)
    team: List[Champion] = []
    active_score = 0
    best = []

    start = time.time()

    # ===== INIT FORCED =====
    for c in forced_champs:
        team.append(c)
        for t in c.traits:
            if t in IGNORED_TRAITS:
                continue

            before = trait_counts.get(t, 0)
            trait_counts[t] = before + 1
            need = trait_need(t, traits[t])

            if before < need <= trait_counts[t]:
                active_score += (
                    ORIGIN_WEIGHT if traits[t].type == "origin" else CLASS_WEIGHT
                )

    # ===== SAVE =====
    def save():
        best.append(
            {
                "score": active_score,
                "total_cost": sum(c.cost for c in team),
                "team_size": len(team),
                "team": serialize_team(team),
            }
        )
        best.sort(
            key=lambda x: (x["score"], x["total_cost"]),
            reverse=True,
        )
        del best[TOP_K:]

    # ===== DFS =====
    def dfs(i):
        nonlocal active_score

        if time.time() - start > time_limit:
            return

        remain_slot = max_team - len(team)
        best_score = best[0]["score"] if best else 0

        if active_score + upper_bound(trait_counts, traits, remain_slot) < best_score:
            return

        tank, carry = count_roles(team)
        if tank + remain_slot < MIN_TANK or carry + remain_slot < MIN_CARRY:
            return

        if valid_team(team):
            save()

        if i >= len(remain) or remain_slot == 0:
            return

        c = remain[i]

        # ===== TAKE =====
        team.append(c)
        added = 0
        updated = []

        for t in c.traits:
            if t in IGNORED_TRAITS:
                continue

            before = trait_counts.get(t, 0)
            trait_counts[t] = before + 1
            need = trait_need(t, traits[t])

            if before < need <= trait_counts[t]:
                added += (
                    ORIGIN_WEIGHT if traits[t].type == "origin" else CLASS_WEIGHT
                )
            updated.append(t)

        active_score += added
        dfs(i + 1)

        # ===== ROLLBACK =====
        active_score -= added
        for t in updated:
            trait_counts[t] -= 1
            if trait_counts[t] == 0:
                del trait_counts[t]
        team.pop()

        # ===== SKIP =====
        dfs(i + 1)

    dfs(0)
    return best
