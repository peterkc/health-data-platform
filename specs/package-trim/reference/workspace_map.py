"""Target workspace map model — `reference/target-map.json` validates against this.

Design contract only (create-time reviewer floor, SK-0008); not shipped code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Layer = Literal["packages", "verticals/home-health", "apps"]
Depth = Literal["DEEP", "MIN", "SKEL", "COMPOSED"]


@dataclass(frozen=True)
class Member:
    name: str
    layer: Layer
    absorbs: list[str] = field(default_factory=list)
    deps: list[str] = field(default_factory=list)
    depth: Depth = "SKEL"


@dataclass(frozen=True)
class TargetMap:
    members: list[Member]

    def __post_init__(self) -> None:
        if len(self.members) != 8:
            raise ValueError(f"target map must have exactly 8 members, got {len(self.members)}")


def load(path: str) -> TargetMap:
    """Parse + validate a target-map JSON file."""
    import json

    raw = json.load(open(path))
    return TargetMap(members=[Member(**m) for m in raw["members"]])


if __name__ == "__main__":
    import sys

    load(sys.argv[1] if len(sys.argv) > 1 else "target-map.json")
    print("ok")
