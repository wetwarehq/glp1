"""Load the glp1_clinic OSCE taskset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
VIGNETTES = ROOT / "vignettes.jsonl"
SYSTEMS = ROOT / "systems_review.json"
FRAME = ROOT / "frame.toml"
TASK = ROOT / "TASK.md"


def load_systems() -> dict[str, Any]:
    return json.loads(SYSTEMS.read_text(encoding="utf-8"))


def load_vignettes() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with VIGNETTES.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def by_id(vignette_id: str) -> dict[str, Any]:
    for v in load_vignettes():
        if v["id"] == vignette_id:
            return v
    raise KeyError(vignette_id)


def core_item_ids() -> list[str]:
    return list(load_systems()["core_every_station"])


def all_item_ids() -> list[str]:
    ids: list[str] = []
    for domain in load_systems()["domains"]:
        for item in domain["items"]:
            ids.append(item["id"])
    return ids


def catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": v["id"],
            "station": v["station"],
            "title": v["title"],
            "drug": v["drug"],
            "usage": v["usage"],
            "critical_findings": v["critical_findings"],
        }
        for v in load_vignettes()
    ]


if __name__ == "__main__":
    print(json.dumps({"n": len(load_vignettes()), "catalog": catalog()}, indent=2))
