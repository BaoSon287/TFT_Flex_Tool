from dataclasses import dataclass
from typing import List


@dataclass
class Champion:
    name: str
    cost: int
    traits: List[str]
    roles: List[str]   # ["tank", "damage", "support"]
    locked: bool
