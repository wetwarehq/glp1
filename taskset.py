"""Load the glp1 OSCE taskset. Namespace is frame.toml, then NAMESPACE, then systems_review.json."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
VIGNETTES = ROOT / "vignettes.jsonl"
SYSTEMS = ROOT / "systems_review.json"
FRAME = ROOT / "frame.toml"
TASK = ROOT / "TASK.md"


def _frame_value(key: str) -> str:
    if not FRAME.exists():
        return ""
    prefix = f"{key}"
    for raw in FRAME.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line.startswith(prefix):
            continue
        if "=" not in line:
            continue
        lhs, rhs = line.split("=", 1)
        if lhs.strip() != key:
            continue
        return rhs.strip().strip('"').strip("'")
    return ""


def namespace() -> str:
    """Single binding: frame.toml, env NAMESPACE, and systems_review.json must agree."""
    frame = _frame_value("namespace")
    env = os.environ.get("NAMESPACE", "").strip()
    systems = ""
    if SYSTEMS.exists():
        systems = str(load_systems().get("namespace") or "").strip()
    present = {k: v for k, v in (("frame", frame), ("env", env), ("systems", systems)) if v}
    if len(set(present.values())) > 1:
        raise RuntimeError(f"namespace drift: {present}")
    return frame or env or systems or "glp1"


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
    print(json.dumps({"namespace": namespace(), "n": len(load_vignettes()), "catalog": catalog()}, indent=2))
