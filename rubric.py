"""Examiner. Trace is copied, then scored. Fail-closed on missed criticals."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from taskset import by_id, core_item_ids, load_systems, namespace

PASS_MARK = 0.70
DISTINCTION = 0.85
IDIOT_WEIGHT = 0.50

DISPOSITIONS = {"continue", "reduce", "hold", "stop", "ed", "refer"}

FAIL_CLOSED_FINDINGS = {
    "acute_pancreatitis_pattern": {"need_disp": {"ed"}, "need_hold_ok": True},
    "acute_monocular_field_defect_naion_until_proven_otherwise": {
        "need_disp": {"ed"},
        "need_hold_ok": True,
    },
    "grey_product_injection_site_infection": {"need_disp": {"stop", "ed", "refer"}},
    "possible_mtc_signal_plus_unclarified_fhx": {"need_disp": {"stop", "refer"}},
    "new_depression_with_passive_si": {"need_disp": {"hold", "stop", "ed", "refer"}},
    "gastroparesis_plus_volume_depletion": {"need_disp": {"hold", "stop", "ed"}},
    "biliary_colic_after_rapid_loss": {"need_disp": {"hold", "reduce", "stop", "refer"}},
}


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
        if e.get("kind") in {"ask", "asked"} and e.get("item"):
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


def coverage_score(asked: set[str], vignette: dict[str, Any]) -> tuple[float, list[str]]:
    required = set(vignette.get("required_asks") or []) | set(core_item_ids())
    # Core is long; station required_asks are the OSCE musts. Weight required 70%, core 30%.
    req = set(vignette.get("required_asks") or [])
    core = set(core_item_ids())
    req_hit = len(req & asked) / max(1, len(req))
    core_hit = len(core & asked) / max(1, len(core))
    score = 0.7 * req_hit + 0.3 * core_hit
    missed = sorted((req | core) - asked)
    return score, missed


def critical_score(asked: set[str], vignette: dict[str, Any]) -> tuple[float, list[str], bool]:
    """Critical findings are elicited only if the triggering items were asked."""
    hidden = vignette.get("hidden") or {}
    findings = list(vignette.get("critical_findings") or [])
    # Map finding → items that reveal it
    triggers = vignette.get("required_asks") or []
    elicited = all(t in asked for t in triggers) if triggers else True
    # More precise: a finding is elicited if at least one required_ask that lives in hidden was asked.
    # required_asks ARE the revealing questions for this station.
    if not findings:
        return 1.0, [], False
    missed = [f for f in findings if not elicited]
    # Partial: fraction of required asks (those are the reveal keys)
    frac = len(set(triggers) & asked) / max(1, len(triggers))
    fail_closed = frac < 1.0 and any(
        f in FAIL_CLOSED_FINDINGS for f in findings
    )
    # If they asked every required item, they elicited the finding.
    if frac >= 1.0:
        return 1.0, [], False
    return frac, findings, fail_closed


def ae_score(note: dict[str, Any], vignette: dict[str, Any]) -> tuple[float, list[str]]:
    gold_aes = (vignette.get("gold") or {}).get("aes") or []
    got = note.get("aes") or []
    if not gold_aes:
        return 1.0, []
    notes = []
    hits = 0.0
    got_terms = [_norm(a.get("term")) for a in got if isinstance(a, dict)]
    for g in gold_aes:
        gterm = _norm(g.get("term"))
        match = None
        for a in got:
            if not isinstance(a, dict):
                continue
            if gterm in _norm(a.get("term")) or _norm(a.get("term")) in gterm:
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


def disposition_score(note: dict[str, Any], vignette: dict[str, Any]) -> tuple[float, list[str], bool]:
    gold = vignette.get("gold") or {}
    want = str(gold.get("disposition") or "")
    got = str(note.get("disposition") or "").lower().strip()
    notes: list[str] = []
    fail_closed = False
    findings = vignette.get("critical_findings") or []

    if got not in DISPOSITIONS:
        notes.append("disposition missing or not in verb set")
        return 0.0, notes, True if findings else False

    for f in findings:
        rule = FAIL_CLOSED_FINDINGS.get(f)
        if not rule:
            continue
        if got not in set(rule["need_disp"]):
            fail_closed = True
            notes.append(f"fail-closed: {f} needs {sorted(rule['need_disp'])}, got {got}")

    if fail_closed:
        return 0.0, notes, True

    if got == want:
        return 1.0, notes, False
    # Near-miss family: hold/stop/reduce are neighbours except where fail-closed
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
        return 0.6, notes, False
    notes.append(f"disposition {got} vs gold {want}")
    return 0.0, notes, False


def composition_score(note: dict[str, Any], vignette: dict[str, Any], asked: set[str]) -> tuple[float, list[str]]:
    gold_c = (vignette.get("gold") or {}).get("composition") or {}
    got_c = note.get("composition") or {}
    notes: list[str] = []
    parts = []
    asked_protein = "composition.protein" in asked
    asked_rt = "composition.resistance" in asked
    parts.append(1.0 if asked_protein else 0.0)
    parts.append(1.0 if asked_rt else 0.0)
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
    return sum(parts) / len(parts), notes


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
        elif m == "increase_dose" and ("12.5" in text_blob or "increase" in text_blob or note.get("disposition") == "continue" and "uptitrat" in text_blob):
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

    # Generic idiot: generic ROS dump with no class items
    asked = asked_items(events)
    class_prefix = tuple(
        d["id"] + "." for d in load_systems()["domains"]
    )
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
    crit, crit_miss, crit_fail = critical_score(asked, v)
    ae, ae_notes = ae_score(note, v)
    disp, disp_notes, disp_fail = disposition_score(note, v)
    comp, comp_notes = composition_score(note, v, asked)
    net = safety_net_score(note)
    idiot, idiot_flags = idiot_index(note, events, v)

    fail_closed = bool(crit_fail or disp_fail)
    domains = {
        "coverage": round(cov, 4),
        "critical_detection": round(crit, 4),
        "ae_classification": round(ae, 4),
        "disposition": round(disp, 4),
        "longevity_composition": round(comp, 4),
        "safety_net": round(net, 4),
    }
    weighted = (
        0.20 * cov
        + 0.25 * crit
        + 0.15 * ae
        + 0.25 * disp
        + 0.10 * comp
        + 0.05 * net
    )
    final = weighted * (1.0 - IDIOT_WEIGHT * idiot)
    if fail_closed:
        final = min(final, 0.30)

    passed = (not fail_closed) and final >= PASS_MARK
    distinction = passed and final >= DISTINCTION

    result = {
        "namespace": namespace(),
        "vignette": vignette_id,
        "station": v.get("station"),
        "title": v.get("title"),
        "asked": sorted(asked),
        "note": note,
        "domains": domains,
        "idiot_index": round(idiot, 4),
        "idiot_flags": idiot_flags,
        "fail_closed": fail_closed,
        "notes": cov_miss[:12] + crit_miss + ae_notes + disp_notes + comp_notes,
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
