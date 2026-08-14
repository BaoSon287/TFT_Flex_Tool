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

def normalize_name_map(champions):
    """
    tạo map: lowercase -> Champion object
    """
    return {c.name.lower(): c for c in champions}

# ===== LOAD DATA =====
def load_champions(banned, path=None):
    if path is None:
        path = resource_path("data/champions.json")

    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    res = []
    for c in raw:
        banned_lc = {b.lower() for b in banned}

        if c["name"].lower() in banned_lc:
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
    return sum(
        1 / min(traits[t].thresholds)
        for t in champ.traits
        if t in traits and t != IGNORED_TRAIT
    )


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
def solve(max_team, time_limit, forced, banned, emblems, lux_trait=None):
    traits = load_traits()
    champions = load_champions(banned)

    # ===== LUX ASPECT =====
    # Lux (Thế Thần) có thể chọn 1 trong 9 hệ
    # Khi chọn hệ, Lux được tính 2 mốc tộc/hệ đó
    lux_champ = None
    if lux_trait:
        for c in champions:
            if c.name == "Lux":
                c.traits = [lux_trait]
                lux_champ = c
                break

    def trait_count_for(champ, t):
        """Lux đếm 2 mốc cho trait đã chọn, các tướng khác đếm 1"""
        if lux_champ is not None and champ is lux_champ and t == lux_trait:
            return 2
        return 1

    champions.sort(
        key=lambda c: champion_value(c, traits),
        reverse=True
    )

    # chuẩn hoá forced / banned về lowercase
    forced_lc = {name.lower() for name in forced}
    banned_lc = {name.lower() for name in banned}

    # map tên chuẩn
    champ_map = normalize_name_map(champions)

    # lấy đúng Champion object
    forced_champs = [
        champ_map[name]
        for name in forced_lc
        if name in champ_map
    ]

    remain = [
        c for c in champions
        if c.name.lower() not in forced_lc
    ]


    trait_counts = dict(emblems)
    team = []
    active = 0
    best = []
    start = time.time()

    # ===== INIT FORCED =====
    for c in forced_champs:
        team.append(c)
        for t in c.traits:
            if t not in traits:
                continue
            before = trait_counts.get(t, 0)
            trait_counts[t] = before + trait_count_for(c, t)
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
        if not team:
            return False
        if not any(c.roles for c in team):
            return True
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
        if any(c.roles for c in champions):
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
            if t not in traits:
                continue
            before = trait_counts.get(t, 0)
            trait_counts[t] = before + trait_count_for(c, t)
            if (
                t != IGNORED_TRAIT
                and before < min(traits[t].thresholds) <= trait_counts[t]
            ):
                added += 1
            updated.append(t)

        dfs(i + 1, active_cnt + added)

        # rollback
        for t in updated:
            trait_counts[t] -= trait_count_for(c, t)
            if trait_counts[t] == 0:
                del trait_counts[t]
        team.pop()

        # ===== SKIP =====
        dfs(i + 1, active_cnt)

    dfs(0, active)
    return best
