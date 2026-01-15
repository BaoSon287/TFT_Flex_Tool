import json
import time
from typing import List, Dict

from backend.models.champion import Champion
from backend.models.trait import Trait
from backend.solver.utils import resource_path


# ===== CONFIG =====
TOP_K = 5

MIN_TANK = 2
MIN_CARRY = 2
MIN_COST = 4

IGNORED_TRAIT = "Targon"   # ⚠️ bắt buộc phải có


# ===== LOAD DATA =====
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
        name: Trait(
            name=name,
            thresholds=data["thresholds"],
            type=data["type"],
        )
        for name, data in raw.items()
    }


# ===== HEURISTICS =====
def champion_value(champ: Champion, traits: Dict[str, Trait]) -> float:
    """Ưu tiên tướng dễ kích hoạt tộc"""
    score = 0.0
    for t in champ.traits:
        if t in traits:
            score += 1 / min(traits[t].thresholds)
    return score


def upper_bound(trait_counts, traits, remain):
    """Ước lượng số trait tối đa còn có thể kích"""
    cnt = 0
    for t, tr in traits.items():
        if t == IGNORED_TRAIT:
            continue

        cur = trait_counts.get(t, 0)
        need = min(tr.thresholds)

        if cur < need and need - cur <= remain:
            cnt += 1
    return cnt


# ===== ROLE COUNT =====
def count_roles(team: List[Champion]):
    tank = 0
    carry = 0

    for c in team:
        if c.cost >= MIN_COST:
            if "tank" in c.roles:
                tank += 1
            if "carry" in c.roles:
                carry += 1

    return tank, carry


def valid_team(team: List[Champion]) -> bool:
    tank, carry = count_roles(team)
    return tank >= MIN_TANK and carry >= MIN_CARRY


# ===== SERIALIZE (API FRIENDLY) =====
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


# ===== SOLVER (API ENTRY) =====
def solve(
    max_team: int,
    time_limit: float,
    forced: List[str],
    banned: List[str],
    emblems: Dict[str, int],
):
    traits = load_traits()
    champions = load_champions(banned)

    # sort theo độ dễ kích trait
    champions.sort(
        key=lambda c: champion_value(c, traits),
        reverse=True,
    )

    forced_champs = [c for c in champions if c.name in forced]
    remain = [c for c in champions if c.name not in forced]

    trait_counts = dict(emblems)
    team: List[Champion] = []
    active = 0
    best = []

    start = time.time()

    # ===== INIT FORCED =====
    for c in forced_champs:
        team.append(c)
        for t in c.traits:
            before = trait_counts.get(t, 0)
            trait_counts[t] = before + 1

            if (
                t != IGNORED_TRAIT
                and before < min(traits[t].thresholds) <= trait_counts[t]
            ):
                active += 1

    # ===== SAVE RESULT =====
    def save(team, score):
        best.append(
            {
                "score": score,
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

    # ===== DFS SEARCH =====
    def dfs(i, active_cnt):
        if time.time() - start > time_limit:
            return

        remain_slot = max_team - len(team)
        best_score = best[0]["score"] if best else 0

        # prune theo trait
        if active_cnt + upper_bound(trait_counts, traits, remain_slot) < best_score:
            return

        # prune theo role
        tank, carry = count_roles(team)
        if tank + remain_slot < MIN_TANK or carry + remain_slot < MIN_CARRY:
            return

        if valid_team(team):
            save(team, active_cnt)

        if i >= len(remain) or remain_slot == 0:
            return

        c = remain[i]

        # ===== TAKE =====
        team.append(c)
        added = 0
        updated = []

        for t in c.traits:
            before = trait_counts.get(t, 0)
            trait_counts[t] = before + 1

            if (
                t != IGNORED_TRAIT
                and before < min(traits[t].thresholds) <= trait_counts[t]
            ):
                added += 1

            updated.append(t)

        dfs(i + 1, active_cnt + added)

        # ===== ROLLBACK =====
        for t in updated:
            trait_counts[t] -= 1
            if trait_counts[t] == 0:
                del trait_counts[t]

        team.pop()

        # ===== SKIP =====
        dfs(i + 1, active_cnt)

    dfs(0, active)
    return best
