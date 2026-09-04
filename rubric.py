"""Examiner. Trace is copied, then scored. Fail-closed table is fail_closed.json."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from taskset import by_id, core_item_ids, load_fail_closed, load_systems, namespace

STOP = {
    "this", "that", "with", "from", "have", "does", "were", "they", "them",
    "then", "than", "into", "only", "also", "does", "not", "and", "the",
    "for", "are", "was", "but", "not", "you", "your",
}


def contract() -> dict[str, Any]:
    return load_fail_closed()


def dispositions() -> set[str]:
    return set(contract().get("dispositions") or [])


def fail_rules() -> dict[str, dict[str, Any]]:
    return {f["id"]: f for f in contract().get("findings") or []}


def weights() -> dict[str, float]:
    return {k: float(v) for k, v in (contract().get("scoring") or {}).items()}


def load_trace(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"kind": "unparseable", "raw": line})
    return events


def asked_items(events: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for e in events:
        if e.get("kind") in {"ask", "asked"} and e.get("item") and e.get("ok") is not False:
            out.add(str(e["item"]))
    return out


def last_note(events: list[dict[str, Any]]) -> dict[str, Any]:
    note: dict[str, Any] = {}
    for e in events:
        if e.get("kind") in {"note", "submit"} and isinstance(e.get("note"), dict):
            note = e["note"]
    return note


def _norm(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())


def _tokens(s: Any) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", str(s).lower()) if len(w) >= 3 and w not in STOP}


def term_match(got: Any, gold: Any) -> bool:
    g = _tokens(gold)
    t = _tokens(got)
    if not g or not t:
        return False
    return g <= t or (len(t) == 1 and t <= g)


def coverage_score(asked: set[str], vignette: dict[str, Any]) -> tuple[float, list[str]]:
    req = set(vignette.get("required_asks") or [])
    core = set(core_item_ids())
    req_hit = len(req & asked) / max(1, len(req))
    core_hit = len(core & asked) / max(1, len(core))
    score = 0.7 * req_hit + 0.3 * core_hit
    missed = sorted((req | core) - asked)
    return score, missed


def critical_score(asked: set[str], note: dict[str, Any], vignette: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    """Elicit = the finding's listed questions, not the whole required_asks list."""
    findings = list(vignette.get("critical_findings") or [])
    rules = fail_rules()
    if not findings:
        return 1.0, [], []
    notes: list[str] = []
    reasons: list[str] = []
    fracs: list[float] = []
    blob = _norm(json.dumps(note))
    for f in findings:
        rule = rules.get(f, {})
        elicit = list(rule.get("elicit") or [])
        if not elicit:
            elicit = [i for i in (vignette.get("required_asks") or []) if i in (vignette.get("hidden") or {})]
        hit = len(set(elicit) & asked) / max(1, len(elicit))
        fracs.append(hit)
        if hit < 1.0:
            notes.append(f)
            if f in rules:
                reasons.append(f"missed elicit for {f}: {elicit}")
        # naming: gold AE terms or finding tokens in the note
        named = False
        for a in note.get("aes") or []:
            if isinstance(a, dict) and a.get("term"):
                named = True
                break
        if _norm(f)[:12] in blob:
            named = True
        if named:
            fracs[-1] = min(1.0, fracs[-1] + 0.0)
    return sum(fracs) / len(fracs), notes, reasons


def ae_score(note: dict[str, Any], vignette: dict[str, Any]) -> tuple[float, list[str]]:
    gold_aes = (vignette.get("gold") or {}).get("aes") or []
    got = note.get("aes") or []
    if not gold_aes:
        return 1.0, []
    notes = []
    hits = 0.0
    for g in gold_aes:
        match = None
        for a in got:
            if isinstance(a, dict) and term_match(a.get("term"), g.get("term")):
                match = a
                break
        if match is None:
            notes.append(f"missed AE {g.get('term')}")
            continue
        part = 0.4
        if int(match.get("grade") or 0) == int(g.get("grade") or 0):
            part += 0.2
        elif abs(int(match.get("grade") or 0) - int(g.get("grade") or 0)) == 1:
            part += 0.1
        if bool(match.get("serious")) == bool(g.get("serious")):
            part += 0.2
        if str(match.get("relatedness") or "") == str(g.get("relatedness") or ""):
            part += 0.2
        hits += part
    return hits / max(1, len(gold_aes)), notes


def disposition_score(note: dict[str, Any], vignette: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    gold = vignette.get("gold") or {}
    want = str(gold.get("disposition") or "")
    got = str(note.get("disposition") or "").lower().strip()
    notes: list[str] = []
    reasons: list[str] = []
    findings = vignette.get("critical_findings") or []
    rules = fail_rules()
    verbs = dispositions()

    if got not in verbs:
        notes.append("disposition missing or not in verb set")
        if findings:
            reasons.append("disposition missing")
        return 0.0, notes, reasons

    for f in findings:
        rule = rules.get(f)
        if not rule:
            continue
        need = set(rule.get("need_disp") or [])
        if need and got not in need:
            reasons.append(f"fail-closed: {f} needs {sorted(need)}, got {got}")
            notes.append(reasons[-1])

    if reasons:
        return 0.0, notes, reasons

    if got == want:
        return 1.0, notes, []
    family = {
        "hold": {"stop", "reduce", "refer"},
        "stop": {"hold", "refer"},
        "reduce": {"hold"},
        "refer": {"hold", "stop", "ed"},
        "ed": set(),
        "continue": set(),
    }
    if got in family.get(want, set()):
        notes.append(f"near disposition {got} vs {want}")
        return 0.6, notes, []
    notes.append(f"disposition {got} vs gold {want}")
    return 0.0, notes, []


def composition_score(note: dict[str, Any], vignette: dict[str, Any], asked: set[str]) -> tuple[float, list[str], list[str]]:
    gold_c = (vignette.get("gold") or {}).get("composition") or {}
    got_c = note.get("composition") or {}
    notes: list[str] = []
    reasons: list[str] = []
    parts = [
        1.0 if "composition.protein" in asked else 0.0,
        1.0 if "composition.resistance" in asked else 0.0,
    ]
    want_q = gold_c.get("weight_quality")
    got_q = got_c.get("weight_quality")
    if want_q:
        if got_q == want_q:
            parts.append(1.0)
        elif got_q:
            parts.append(0.4)
            notes.append(f"weight_quality {got_q} vs {want_q}")
        else:
            parts.append(0.0)
            notes.append("no weight_quality")
    else:
        parts.append(1.0)

    rules = fail_rules()
    for f in vignette.get("critical_findings") or []:
        rule = rules.get(f) or {}
        elicit = list(rule.get("elicit") or [])
        if "composition.protein" in elicit or "composition.resistance" in elicit:
            if elicit and not all(i in asked for i in elicit):
                reasons.append(f"missed composition elicit for {f}")
        need_q = list(rule.get("need_weight_quality") or [])
        if need_q and (got_q or "") not in need_q:
            reasons.append(f"fail-closed: {f} needs weight_quality in {need_q}, got {got_q or '∅'}")
    return sum(parts) / len(parts), notes, reasons


def contract_score(note: dict[str, Any], vignette: dict[str, Any]) -> tuple[float, list[str]]:
    gold = vignette.get("gold") or {}
    parts: list[float] = []
    notes: list[str] = []
    want_ol = bool(gold.get("off_label_disclosed"))
    got_ol = bool(note.get("off_label_disclosed"))
    if want_ol and not got_ol:
        parts.append(0.0)
        notes.append("off-label not disclosed")
    else:
        parts.append(1.0)

    want_i = str(gold.get("indication") or "")
    got_i = str(note.get("indication") or "")
    if want_i:
        if _norm(got_i) and (_norm(got_i) == _norm(want_i) or _norm(want_i) in _norm(got_i) or _norm(got_i) in _norm(want_i)):
            parts.append(1.0)
        else:
            parts.append(0.0)
            notes.append(f"indication {got_i or '∅'} vs {want_i}")
    else:
        parts.append(1.0)

    want_s = str((vignette.get("drug") or {}).get("source") or "")
    got_s = str((note.get("exposure") or {}).get("source") or "")
    if want_s:
        if got_s == want_s:
            parts.append(1.0)
        else:
            parts.append(0.0)
            notes.append(f"source {got_s or '∅'} vs {want_s}")

    blob = " ".join(_tokens(json.dumps(note)))
    must = list(gold.get("must_address") or [])
    if must:
        hits = 0
        for item in must:
            keys = [w for w in re.findall(r"[a-z0-9]+", item.lower()) if len(w) >= 4 and w not in STOP]
            if not keys:
                hits += 1
                continue
            n = sum(1 for k in keys if k in blob)
            if n >= max(1, (len(keys) + 1) // 2):
                hits += 1
            else:
                notes.append(f"unaddressed: {item}")
        parts.append(hits / len(must))
    return sum(parts) / max(1, len(parts)), notes


def safety_net_score(note: dict[str, Any]) -> float:
    text = str(note.get("safety_net") or "")
    if len(text) < 12:
        return 0.0
    keys = ("ed", "emergency", "pain", "back", "urine", "vision", "suicid", "jaundice", "fever")
    return 1.0 if any(k in text.lower() for k in keys) else 0.4


def idiot_index(note: dict[str, Any], events: list[dict[str, Any]], vignette: dict[str, Any]) -> tuple[float, list[str]]:
    flags: list[str] = []
    gold = vignette.get("gold") or {}
    got = str(note.get("disposition") or "").lower()
    orders = [e.get("test") for e in events if e.get("kind") == "order"]
    text_blob = json.dumps(note).lower()
    got_q = str((note.get("composition") or {}).get("weight_quality") or "")
    want_q = str((gold.get("composition") or {}).get("weight_quality") or "")

    if want_q == "sarcopenic_risk" and got_q == "lean_preserved":
        flags.append("treating muscle loss as success")

    for move in vignette.get("idiot_moves") or []:
        m = str(move.get("match") or "")
        why = str(move.get("why") or m)
        if m == "stop" and got == "stop" and gold.get("disposition") == "continue":
            flags.append(why)
        elif m == "ed" and got == "ed" and gold.get("disposition") == "continue":
            flags.append(why)
        elif m == "continue" and got == "continue" and gold.get("disposition") in {"ed", "hold", "stop"}:
            flags.append(why)
        elif m == "reduce" and got == "reduce" and gold.get("disposition") == "ed":
            flags.append(why)
        elif m == "increase_dose" and ("12.5" in text_blob or "increase" in text_blob or (note.get("disposition") == "continue" and "uptitrat" in text_blob)):
            flags.append(why)
        elif m == "continue_no_ix" and got == "continue" and not (note.get("investigations") or orders):
            flags.append(why)
        elif m == "call_it_nausea" and any(
            _norm(a.get("term")) in {"nausea", "vomiting"} for a in (note.get("aes") or []) if isinstance(a, dict)
        ) and not any("biliar" in _norm(a.get("term")) or "chole" in _norm(a.get("term")) for a in (note.get("aes") or []) if isinstance(a, dict)):
            flags.append(why)
        elif m == "antiemetic_home" and got not in {"ed"} and "ondansetron" in text_blob:
            flags.append(why)
        elif m == "prokinetic_continue" and got == "continue":
            flags.append(why)
        elif m == "continue_ignore_si" and got == "continue":
            flags.append(why)
        elif m == "stop_and_discharge" and got == "stop" and len(str(note.get("safety_net") or "")) < 12:
            flags.append(why)
        elif m == "call_it_efficacy" and "reward" in text_blob and got == "continue":
            flags.append(why)
        elif m == "optometrist_routine" and ("optometrist" in text_blob or "specsavers" in text_blob) and got != "ed":
            flags.append(why)
        elif m == "call_it_dry_eye" and "dry eye" in text_blob:
            flags.append(why)
        elif m == "convert_to_brand_today" and ("wegovy" in text_blob or "start brand" in text_blob) and got in {"continue", "reduce"}:
            flags.append(why)
        elif m == "call_it_gi_diarrhoea" and got == "continue":
            flags.append(why)
        elif m == "shotgun_labs":
            if len(orders) >= 6 or len(note.get("investigations") or []) >= 6:
                flags.append(why)

    asked = asked_items(events)
    class_prefix = tuple(d["id"] + "." for d in load_systems()["domains"])
    if asked and not any(a.startswith(class_prefix) for a in asked):
        flags.append("generic ROS, no class-specific item")

    n = min(1.0, len(flags) / 3.0)
    return n, flags


def score_trace(trace_path: Path, vignette_id: str) -> dict[str, Any]:
    v = by_id(vignette_id)
    events = load_trace(trace_path)
    asked = asked_items(events)
    note = last_note(events)

    cov, cov_miss = coverage_score(asked, v)
    crit, crit_miss, crit_reasons = critical_score(asked, note, v)
    ae, ae_notes = ae_score(note, v)
    disp, disp_notes, disp_reasons = disposition_score(note, v)
    comp, comp_notes, comp_reasons = composition_score(note, v, asked)
    contract_s, contract_notes = contract_score(note, v)
    net = safety_net_score(note)
    idiot, idiot_flags = idiot_index(note, events, v)

    cfg = contract()
    w = weights()
    pass_mark = float(cfg.get("pass_mark") or 0.70)
    distinction_mark = float(cfg.get("distinction") or 0.85)
    idiot_w = float(cfg.get("idiot_penalty_weight") or 0.50)
    cap = float(cfg.get("fail_closed_cap") or 0.30)

    fail_reasons = crit_reasons + disp_reasons + comp_reasons
    fail_closed = bool(fail_reasons)
    domains = {
        "coverage": round(cov, 4),
        "critical_detection": round(crit, 4),
        "ae_classification": round(ae, 4),
        "disposition": round(disp, 4),
        "longevity_composition": round(comp, 4),
        "contract": round(contract_s, 4),
        "safety_net": round(net, 4),
    }
    weighted = sum(w.get(k, 0.0) * domains[k] for k in domains)
    final = weighted * (1.0 - idiot_w * idiot)
    if fail_closed:
        final = min(final, cap)

    passed = (not fail_closed) and final >= pass_mark
    distinction = passed and final >= distinction_mark

    result = {
        "namespace": namespace(),
        "product": "clinic",
        "vignette": vignette_id,
        "station": v.get("station"),
        "title": v.get("title"),
        "asked": sorted(asked),
        "note": note,
        "domains": domains,
        "idiot_index": round(idiot, 4),
        "idiot_flags": idiot_flags,
        "fail_closed": fail_closed,
        "fail_closed_reason": fail_reasons,
        "notes": cov_miss[:12] + crit_miss + ae_notes + disp_notes + comp_notes + contract_notes,
        "score": round(final, 4),
        "pass": passed,
        "distinction": distinction,
        "n_events": len(events),
    }
    return result


def write_score(result: dict[str, Any], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--trace", required=True)
    p.add_argument("--vignette", required=True)
    p.add_argument("--out", default="")
    args = p.parse_args()
    res = score_trace(Path(args.trace), args.vignette)
    if args.out:
        write_score(res, Path(args.out))
    print(json.dumps(res, indent=2))
