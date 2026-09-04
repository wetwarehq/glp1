"""Modal runner. Default image is ghcr.io/wetwarehq/glp1:latest."""

from __future__ import annotations

import modal

app = modal.App("glp1")

image = modal.Image.from_registry("ghcr.io/wetwarehq/glp1:latest")


@app.function(image=image, timeout=180)
def run_station(vignette: str = "st01", script: str = "scripts/gold_st01.jsonl") -> dict:
    import json
    import subprocess
    import sys

    sys.path.insert(0, "/clinic")
    result = subprocess.run(
        ["python", "/clinic/harness.py", "--vignette", vignette, "--script", f"/clinic/{script}",
         "--trace", "/tmp/trace.jsonl", "--score-dir", "/tmp/score"],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except Exception:
        payload = {"stdout": result.stdout, "stderr": result.stderr, "code": result.returncode}
    return payload


@app.local_entrypoint()
def main(vignette: str = "st01"):
    print(run_station.remote(vignette=vignette))
