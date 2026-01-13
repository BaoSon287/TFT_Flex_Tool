import json
import time
from models.champion import Champion
from models.trait import Trait
from utils import resource_path

# ===== TRAIT RULE =====
TARGON_TRAIT = "Targon"
IGNORED_TRAITS = {"Darkin"}

TOP_K = 5

MIN_TANK = 2
MIN_CARRY = 2
MIN_COST = 4

ORIGIN_WEIGHT = 3
CLASS_WEIGHT = 1


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


# ===== TRAIT NEED =====
def trait_need(trait_name, trait_obj):
    if trait_name in IGNORED_TRAITS:
        return float("inf")   # ❌ không bao giờ kích
    if trait_name == TARGON_TRAIT:
        return 1              # ✅ Targon mốc 1
    return min(trait_obj.thresholds)


# ===== HEURISTICS =====
def champion_value(champ, traits):
    val = 0
    for t in champ.traits:
        if t in IGNORED_TRAITS:
            continue
        need = trait_need(t, traits[t])
        weight = ORIGIN_WEIGHT if traits[t].type == "origin" else CLASS_WEIGHT
        val += weight / need
    return val


def upper_bound(trait_counts, traits, remain):
    cnt = 0
    for t, tr in traits.items():
        if t in IGNORED_TRAITS:
            continue
        cur = trait_counts.get(t, 0)
        need = trait_need(t, tr)
        if cur < need and need - cur <= remain:
            cnt += ORIGIN_WEIGHT if tr.type == "origin" else CLASS_WEIGHT
    return cnt


# ===== ROLE CHECK =====
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


def valid_team(team):
    tank, carry = count_roles(team)
    return tank >= MIN_TANK and carry >= MIN_CARRY


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
                    ORIGIN_WEIGHT
                    if traits[t].type == "origin"
                    else CLASS_WEIGHT
                )

    # ===== SAVE =====
    def save():
        best.append({
            "score": active_score,
            "cost": sum(c.cost for c in team),
            "team": team.copy()
        })
        best.sort(key=lambda x: (x["score"], x["cost"]), reverse=True)
        del best[TOP_K:]

    # ===== DFS =====
    def dfs(i):
        nonlocal active_score

        if time.time() - start > time_limit:
            return

        remain_slot = max_team - len(team)
        best_score = best[0]["score"] if best else 0

        # bound by trait potential
        if active_score + upper_bound(trait_counts, traits, remain_slot) < best_score:
            return

        # bound by role
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
                    ORIGIN_WEIGHT
                    if traits[t].type == "origin"
                    else CLASS_WEIGHT
                )
            updated.append(t)

        active_score += added
        dfs(i + 1)

        # rollback
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
