#!/usr/bin/env python3
"""Agent acts on the clinic room. Every action is traced. Submit writes the handoff."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from taskset import all_item_ids, by_id, item_by_id, load_fail_closed, load_systems, namespace, assert_contract
from verifier import verify

ROOT = Path(__file__).resolve().parent
TRACER_CANDIDATES = [
    ROOT / "runtime" / "target" / "release" / "glp1-trace",
    ROOT / "runtime" / "target" / "debug" / "glp1-trace",
    Path("/usr/local/bin/glp1-trace"),
]


def now_ms() -> int:
    return int(time.time() * 1000)


def find_tracer() -> Path | None:
    env = os.environ.get("GLP1_TRACER")
    if env and Path(env).exists():
        return Path(env)
    for p in TRACER_CANDIDATES:
        if p.exists():
            return p
    return None


def _ns_env() -> dict[str, str]:
    env = os.environ.copy()
    env["NAMESPACE"] = namespace()
    return env


class Tracer:
    """One schema: JSON object per line, ts always present. Rust or Python."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.bin = find_tracer()
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.bin:
            subprocess.check_call([str(self.bin), "init", str(path)], env=_ns_env())
        else:
            path.write_text(
                json.dumps({"ts": now_ms(), "kind": "init", "namespace": namespace()}) + "\n",
                encoding="utf-8",
            )

    def append(self, event: dict[str, Any]) -> None:
        if "ts" not in event:
            event = {"ts": now_ms(), **event}
        payload = json.dumps(event, separators=(",", ":"))
        if self.bin:
            subprocess.check_call([str(self.bin), "append", str(self.path), payload], env=_ns_env())
        else:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(payload + "\n")

    def copy(self, dest_dir: Path) -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "trace.jsonl"
        if self.bin:
            subprocess.check_call(
                [str(self.bin), "copy", str(self.path), str(dest_dir)],
                stdout=subprocess.DEVNULL,
                env=_ns_env(),
            )
        else:
            dest.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
        return dest


class Room:
    def __init__(self, vignette_id: str, trace_path: Path) -> None:
        self.v = by_id(vignette_id)
        assert_contract()
        self.systems = load_systems()
        self.tracer = Tracer(trace_path)
        self.asked: set[str] = set()
        self.orders: list[str] = []
        self.note: dict[str, Any] = {}
        self.submitted = False
        self.t0 = time.monotonic()
        self.duration_min = int(self.v.get("duration_min") or load_fail_closed().get("clock_minutes") or 8)
        self.tracer.append(
            {
                "kind": "open",
                "vignette": self.v["id"],
                "station": self.v["station"],
                "title": self.v["title"],
                "duration_min": self.duration_min,
            }
        )

    def door(self) -> str:
        d = self.v["drug"]
        return (
            f"STATION {self.v['station']:02d}  {self.v['title']}\n"
            f"Time: {self.duration_min} min\n"
            f"Drug class: GLP-1 RA · usage {self.v['usage']}\n"
            f"Exposure on door: {d.get('inn')} {d.get('dose')} ({d.get('source')}, {d.get('weeks')}w)\n\n"
            f"{self.v['stem']}\n"
        )

    def chart(self) -> dict[str, Any]:
        self.tracer.append({"kind": "chart"})
        return self.v["chart"]

    def items(self) -> list[dict[str, str]]:
        rows = []
        for domain in self.systems["domains"]:
            for item in domain["items"]:
                rows.append(
                    {
                        "id": item["id"],
                        "ask": item["ask"],
                        "domain": domain["label"],
                        "core": bool(item.get("core")),
                    }
                )
        self.tracer.append({"kind": "items", "n": len(rows)})
        return rows

    def ask(self, item_id: str) -> dict[str, Any]:
        spec = item_by_id(item_id)
        if spec is None and item_id not in all_item_ids():
            self.tracer.append({"kind": "ask", "item": item_id, "ok": False, "error": "unknown_item"})
            return {"ok": False, "error": f"unknown item {item_id}"}
        hidden = self.v.get("hidden") or {}
        self.asked.add(item_id)
        if item_id in hidden:
            finding = hidden[item_id]
            revealed = True
        else:
            finding = "No additional finding on this item. Negative in this station."
            revealed = False
        ask_text = (spec or {}).get("ask") or item_id
        event = {
            "kind": "ask",
            "item": item_id,
            "ask_text": ask_text,
            "finding_text": finding,
            "revealed": revealed,
            "ok": True,
        }
        self.tracer.append(event)
        return event

    def examine(self) -> dict[str, Any]:
        finding = (self.v.get("hidden") or {}).get("examine")
        text = finding or "No extra exam findings beyond the chart vitals."
        self.tracer.append({"kind": "examine", "ok": bool(finding), "finding_text": text})
        return {"ok": True, "finding": text, "finding_text": text}

    def order(self, test_id: str) -> dict[str, Any]:
        allowed = set((self.v.get("gold") or {}).get("investigations") or [])
        self.orders.append(test_id)
        indicated = test_id in allowed
        self.tracer.append({"kind": "order", "test": test_id, "indicated": indicated, "ok": True})
        return {
            "ok": True,
            "test": test_id,
            "indicated": indicated,
            "result": (
                "Ordered. Result pending — disposition first."
                if indicated
                else "Logged, not indicated on this stem. The examiner will mark it."
            ),
        }

    def write_note(self, note: dict[str, Any]) -> dict[str, Any]:
        self.note = note
        self.tracer.append({"kind": "note", "note": note})
        return {"ok": True}

    def submit(self, score_dir: Path) -> dict[str, Any]:
        if self.submitted:
            return {"ok": False, "error": "already submitted"}
        self.submitted = True
        elapsed = time.monotonic() - self.t0
        self.tracer.append(
            {
                "kind": "clock",
                "duration_min": self.duration_min,
                "elapsed_sec": round(elapsed, 3),
                "overtime": elapsed > self.duration_min * 60,
            }
        )
        self.tracer.append({"kind": "submit", "note": self.note})
        copied = self.tracer.copy(score_dir)
        return verify(copied, self.v["id"], score_dir)


def _print(obj: Any) -> None:
    if isinstance(obj, str):
        sys.stdout.write(obj if obj.endswith("\n") else obj + "\n")
    else:
        sys.stdout.write(json.dumps(obj, indent=2) + "\n")
    sys.stdout.flush()


def run_repl(vignette_id: str, trace_path: Path, score_dir: Path) -> int:
    room = Room(vignette_id, trace_path)
    _print(room.door())
    _print("Commands: chart | items | ask <id> | examine | order <test> | note <json> | submit | quit")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            parts = shlex.split(line)
        except ValueError as e:
            _print({"ok": False, "error": str(e)})
            continue
        cmd = parts[0].lower()
        try:
            if cmd in {"quit", "exit"}:
                return 0
            if cmd == "chart":
                _print(room.chart())
            elif cmd == "items":
                _print(room.items())
            elif cmd == "ask":
                if len(parts) < 2:
                    _print({"ok": False, "error": "ask <item_id>"})
                else:
                    _print(room.ask(parts[1]))
            elif cmd == "examine":
                _print(room.examine())
            elif cmd == "order":
                if len(parts) < 2:
                    _print({"ok": False, "error": "order <test_id>"})
                else:
                    _print(room.order(" ".join(parts[1:])))
            elif cmd == "note":
                raw = line.split(None, 1)[1] if " " in line else "{}"
                _print(room.write_note(json.loads(raw)))
            elif cmd == "submit":
                result = room.submit(score_dir)
                _print(result)
                return 0 if result.get("pass") else 1
            else:
                _print({"ok": False, "error": f"unknown command {cmd}"})
        except Exception as e:  # noqa: BLE001 — room must not die mid-station
            _print({"ok": False, "error": str(e)})
    return 0


def run_script(vignette_id: str, script: Path, trace_path: Path, score_dir: Path) -> int:
    """Deterministic agent script: one JSON object per line with {cmd,...}."""
    room = Room(vignette_id, trace_path)
    for raw in script.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        step = json.loads(raw)
        cmd = step.get("cmd")
        if cmd == "chart":
            room.chart()
        elif cmd == "items":
            room.items()
        elif cmd == "ask":
            room.ask(step["item"])
        elif cmd == "examine":
            room.examine()
        elif cmd == "order":
            room.order(step["test"])
        elif cmd == "note":
            room.write_note(step["note"])
        elif cmd == "submit":
            result = room.submit(score_dir)
            _print(result)
            return 0 if result.get("pass") else 1
    result = room.submit(score_dir)
    _print(result)
    return 0 if result.get("pass") else 1


def main(argv: list[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(description="glp1 clinic harness")
    p.add_argument("--vignette", default="st01")
    p.add_argument("--trace", default=os.environ.get("TRACE_PATH", "/tmp/glp1/trace.jsonl"))
    p.add_argument("--score-dir", default=os.environ.get("SCORE_DIR", "/tmp/glp1/score"))
    p.add_argument("--script", default="", help="JSONL command script (agent actions)")
    p.add_argument("--list", action="store_true")
    args = p.parse_args(argv)
    if args.list:
        from taskset import catalog

        _print(catalog())
        return 0
    trace_path = Path(args.trace)
    score_dir = Path(args.score_dir)
    if args.script:
        return run_script(args.vignette, Path(args.script), trace_path, score_dir)
    if sys.stdin.isatty() and not args.script:
        _print(Room(args.vignette, trace_path).door())
    return run_repl(args.vignette, trace_path, score_dir)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

