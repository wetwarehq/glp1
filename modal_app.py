"""Optional Modal runner. Image is still ghcr.io/wetwarehq/glp1."""

from __future__ import annotations

import modal

app = modal.App("glp1")

image = (
    modal.Image.from_registry("ghcr.io/wetwarehq/glp1:latest")
    if False
    else modal.Image.debian_slim(python_version="3.12")
    .apt_install("curl", "build-essential")
    .run_commands("curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y")
    .add_local_dir(".", remote_path="/clinic", ignore=["runtime/target", ".git"])
    .run_commands(
        "export PATH=$HOME/.cargo/bin:$PATH && cd /clinic/runtime && cargo build --release && cp target/release/glp1-trace /usr/local/bin/glp1-trace"
    )
)


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
