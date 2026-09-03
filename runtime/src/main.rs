//! Trace the clinic room.
//! Every harness action is appended as one NDJSON event.
//!
//!   glp1-trace init  <trace.jsonl>
//!   glp1-trace append <trace.jsonl> <json-event>
//!   glp1-trace dump   <trace.jsonl>
//!   glp1-trace copy   <trace.jsonl> <score-dir>

use std::env;
use std::fs::{self, OpenOptions};
use std::io::{self, Write};
use std::path::Path;
use std::process;
use std::time::{SystemTime, UNIX_EPOCH};

fn now_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0)
}

fn die(msg: &str) -> ! {
    eprintln!("glp1-trace: {msg}");
    process::exit(2);
}

fn init(path: &Path) {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).unwrap_or_else(|e| die(&e.to_string()));
    }
    let header = format!(
        "{{\"ts\":{},\"kind\":\"init\",\"namespace\":\"glp1\"}}\n",
        now_ms()
    );
    fs::write(path, header).unwrap_or_else(|e| die(&e.to_string()));
}

fn append(path: &Path, payload: &str) {
    let payload = payload.trim();
    if payload.is_empty() {
        die("empty event");
    }
    // Must be a JSON object. We do not parse deeply — the verifier does.
    if !payload.starts_with('{') || !payload.ends_with('}') {
        die("event must be a JSON object");
    }
    let mut f = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .unwrap_or_else(|e| die(&e.to_string()));
    // Inject ts if the caller omitted it.
    let line = if payload.contains("\"ts\"") {
        format!("{payload}\n")
    } else {
        format!("{{\"ts\":{},{}\n", now_ms(), &payload[1..])
    };
    f.write_all(line.as_bytes())
        .and_then(|_| f.flush())
        .unwrap_or_else(|e| die(&e.to_string()));
}

fn dump(path: &Path) {
    let body = fs::read_to_string(path).unwrap_or_else(|e| die(&e.to_string()));
    io::stdout()
        .write_all(body.as_bytes())
        .unwrap_or_else(|e| die(&e.to_string()));
}

fn copy_trace(src: &Path, dest_dir: &Path) {
    fs::create_dir_all(dest_dir).unwrap_or_else(|e| die(&e.to_string()));
    let dest = dest_dir.join("trace.jsonl");
    fs::copy(src, &dest).unwrap_or_else(|e| die(&e.to_string()));
    eprintln!("{}", dest.display());
}

fn main() {
    let mut args = env::args().skip(1);
    let cmd = args.next().unwrap_or_else(|| die("usage: init|append|dump|copy"));
    match cmd.as_str() {
        "init" => {
            let path = args.next().unwrap_or_else(|| die("init <path>"));
            init(Path::new(&path));
        }
        "append" => {
            let path = args.next().unwrap_or_else(|| die("append <path> <json>"));
            let json = args.next().unwrap_or_else(|| die("append <path> <json>"));
            append(Path::new(&path), &json);
        }
        "dump" => {
            let path = args.next().unwrap_or_else(|| die("dump <path>"));
            dump(Path::new(&path));
        }
        "copy" => {
            let src = args.next().unwrap_or_else(|| die("copy <src> <dir>"));
            let dest = args.next().unwrap_or_else(|| die("copy <src> <dir>"));
            copy_trace(Path::new(&src), Path::new(&dest));
        }
        other => die(&format!("unknown command {other}")),
    }
}
