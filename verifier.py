"""Trace is copied, then scored. The clinician product is handoff.json."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from handoff import build_handoff, write_handoff
from rubric import load_trace, score_trace, write_score
from taskset import by_id


def verify(trace_copy: Path, vignette_id: str, dest_dir: Path) -> dict[str, Any]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    result = score_trace(trace_copy, vignette_id)
    write_score(result, dest_dir / "score.json")
    packet = build_handoff(by_id(vignette_id), load_trace(trace_copy), result)
    write_handoff(packet, dest_dir / "handoff.json")
    result["handoff"] = str(dest_dir / "handoff.json")
    return result


if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser(description="Score a copied trace and write the clinician handoff")
    p.add_argument("--trace", required=True)
    p.add_argument("--vignette", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    res = verify(Path(args.trace), args.vignette, Path(args.out))
    print(json.dumps(res, indent=2))
