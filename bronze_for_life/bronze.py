import json
import time
from models.champion import Champion
from models.trait import Trait
from utils import resource_path
IGNORED_TRAIT = "Targon"
TOP_K = 5

MIN_TANK = 2
MIN_CARRY = 2
MIN_COST = 4


# ===== LOAD DATA =====
def load_champions(banned, path=None):
    if path is None:
        path = resource_path("data/champions.json")

    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    res = []
    for c in raw:
        if c["name"] in banned:
            continue
        res.append(
            Champion(
                name=c["name"],
                cost=c["cost"],
                traits=c["traits"],
                roles=c.get("roles", []),
                locked=c.get("locked", False)
            )
        )
    return res


def load_traits(path=None):
    if path is None:
        path = resource_path("data/traits.json")

    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {
        k: Trait(k, v["thresholds"], v["type"])
        for k, v in raw.items()
    }


# ===== HEURISTICS =====
def champion_value(champ, traits):
    return sum(1 / min(traits[t].thresholds) for t in champ.traits)


def upper_bound(trait_counts, traits, remain):
    cnt = 0
    for t, tr in traits.items():
        if t == IGNORED_TRAIT:
            continue
        cur = trait_counts.get(t, 0)
        need = min(tr.thresholds)
        if cur < need and need - cur <= remain:
            cnt += 1
    return cnt


# ===== SOLVER =====
def solve(max_team, time_limit, forced, banned, emblems):
    traits = load_traits()
    champions = load_champions(banned)

    champions.sort(
        key=lambda c: champion_value(c, traits),
        reverse=True
    )

    forced_champs = [c for c in champions if c.name in forced]
    remain = [c for c in champions if c.name not in forced]

    trait_counts = dict(emblems)
    team = []
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

    # ===== ROLE COUNT =====
    def count_roles(team):
        tank = 0
        carry = 0
        for c in team:
            if c.cost >= MIN_COST:
                if "tank" in c.roles:
                    tank += 1
                if "carry" in c.roles:
                    carry += 1
        return tank, carry

    # ===== VALID TEAM =====
    def valid_team(team):
        tank, carry = count_roles(team)
        return tank >= MIN_TANK and carry >= MIN_CARRY

    # ===== SAVE RESULT =====
    def save(team, score):
        best.append({
            "score": score,
            "cost": sum(c.cost for c in team),
            "team": team.copy()
        })
        best.sort(key=lambda x: (x["score"], x["cost"]), reverse=True)
        del best[TOP_K:]

    # ===== DFS =====
    def dfs(i, active_cnt):
        if time.time() - start > time_limit:
            return

        remain_slot = max_team - len(team)
        best_score = best[0]["score"] if best else 0

        # --- trait bound ---
        if active_cnt + upper_bound(trait_counts, traits, remain_slot) < best_score:
            return

        # --- role bound ---
        tank, carry = count_roles(team)
        if tank + remain_slot < MIN_TANK or carry + remain_slot < MIN_CARRY:
            return

        # --- save only valid team ---
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

        # rollback
        for t in updated:
            trait_counts[t] -= 1
            if trait_counts[t] == 0:
                del trait_counts[t]
        team.pop()

        # ===== SKIP =====
        dfs(i + 1, active_cnt)

    dfs(0, active)
    return best
