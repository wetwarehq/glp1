"""Clinician packet. The history the agent took, handed over for review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taskset import core_item_ids, load_fail_closed, load_systems, namespace


def _item_ask(item_id: str) -> str:
    for domain in load_systems()["domains"]:
        for item in domain["items"]:
            if item["id"] == item_id:
                return str(item["ask"])
    return item_id


def build_handoff(
    vignette: dict[str, Any],
    events: list[dict[str, Any]],
    result: dict[str, Any],
) -> dict[str, Any]:
    contract = load_fail_closed()
    asked_events = [
        e
        for e in events
        if e.get("kind") in {"ask", "asked"} and e.get("ok") is not False and e.get("item")
    ]
    history = []
    seen: set[str] = set()
    for e in asked_events:
        item = str(e["item"])
        if item in seen:
            continue
        seen.add(item)
        history.append(
            {
                "item": item,
                "ask_text": e.get("ask_text") or _item_ask(item),
                "finding_text": e.get("finding_text") or e.get("finding") or "",
                "revealed": bool(e.get("revealed")),
                "ts": e.get("ts"),
            }
        )
    core = core_item_ids()
    required = list(vignette.get("required_asks") or [])
    clock_event = next((e for e in reversed(events) if e.get("kind") == "clock"), {})
    duration = int(vignette.get("duration_min") or clock_event.get("duration_min") or contract.get("clock_minutes") or 8)
    exam_event = next((e for e in reversed(events) if e.get("kind") == "examine"), None)
    return {
        "product": "clinic",
        "namespace": namespace(),
        "disclaimer": contract["disclaimer"],
        "station": {
            "id": vignette.get("id"),
            "n": vignette.get("station"),
            "title": vignette.get("title"),
            "drug": vignette.get("drug"),
            "usage": vignette.get("usage"),
        },
        "stem": vignette.get("stem"),
        "clock": {
            "duration_min": duration,
            "elapsed_sec": clock_event.get("elapsed_sec"),
            "overtime": bool(clock_event.get("overtime")),
        },
        "history": history,
        "exam": (
            {
                "done": True,
                "finding_text": exam_event.get("finding_text") or exam_event.get("finding") or "",
                "ts": exam_event.get("ts"),
            }
            if exam_event
            else {"done": False, "finding_text": ""}
        ),
        "unasked_core": [i for i in core if i not in seen],
        "unasked_required": [i for i in required if i not in seen],
        "note": result.get("note") or {},
        "disposition": (result.get("note") or {}).get("disposition"),
        "score": {
            "value": result.get("score"),
            "pass": result.get("pass"),
            "distinction": result.get("distinction"),
            "fail_closed": result.get("fail_closed"),
            "fail_closed_reason": result.get("fail_closed_reason") or [],
            "domains": result.get("domains") or {},
            "idiot_flags": result.get("idiot_flags") or [],
        },
    }


def write_handoff(packet: dict[str, Any], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(packet, indent=2), encoding="utf-8")
