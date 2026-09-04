# TASK — glp1 clinic

**Clinic.** A virtual OSCE room. The agent takes a follow-up history, writes down what it asked, and hands that packet to a human clinician. The final medical decision remains with the clinician.

**Room.** Outpatient clinic. Routine follow-up. Drug class: GLP-1 receptor agonists (semaglutide / Ozempic / Wegovy, tirzepatide, liraglutide, compounded and grey product). Use: off-label longevity more often than diabetes.

**Job.** Adverse-event monitoring plus composition. Gut, gallbladder, pancreas, eyes, mood, and whether the weight coming off is fat or muscle.

**You are the candidate.** Stem on the door. Chart visible. Hidden findings exist only if you ask. Write a note. Submit. The verifier copies the log, scores it, and writes `handoff.json` for the clinician. Fluency without asks is a fail.

This room has no model. Bring your own compute and your own agent. Seat it:

```
python harness.py --vignette st03 --script your_agent.jsonl
```

---

## What this is not

- Not T2DM clinic by default. Some stations have diabetes; most are euglycaemic longevity users.
- Not weight-loss coaching. Kilograms without composition is an incomplete endpoint.
- Not a licence to invent a 40-item panel. Tests only when a finding opens them.
- Not pharmacovigilance theatre. If they need ED, send them. If nausea is CTCAE G1 on a stable dose, do not stop.

---

## Required behaviour every station

1. **Name the exposure.** Molecule, dose, last titration, source (brand / compounded / grey).
2. **State the indication as the patient understands it.** Off-label for longevity if it is. Write that down. Undisclosed off-label, or calling compounded/grey product a brand, fail-closes.
3. **Systems review is class-specific** (`systems_review.json`). A 14-system ROS that never hits biliary, pancreas, gastroparesis, NAION, SI, or lean-mass loss fails coverage.
4. **Efficacy is weight quality.** Rate, protein g/kg/day, resistance training. A “successful” loss with no protein and no lifting fail-closes this usage.
5. **Grade what you find.** CTCAE v6.0 G1–G5. Expected vs serious. Relatedness: certain / probable / possible / unlikely / unassessable.
6. **Disposition is a verb.** `continue` | `reduce` | `hold` | `stop` | `ed` | `refer`. Then follow-up and a safety-net the patient could use at 02:00. Safety-net is not a substitute for ED.
7. **Boxed warning is not trivia.** MTC/MEN2, pregnancy, neck lump + hoarseness: not “review in 3 months.”

Fail-closed findings live in one table: `fail_closed.json`. README, TASK, and the examiner all read that file.

---

## Commands

```
chart                 visible record only
items                 class-specific systems review ids
ask <item_id>         elicit; writes ask_text + finding_text into the history
examine               limited exam if the station has one
order <test_id>       logged with indicated true/false
note                  JSON assessment
submit                freeze, copy, score, write handoff.json
```

Clock is `duration_min` on the door (8). Recorded on submit. Overtime is noted, not an automatic fail.

---

## Note schema

```json
{
  "summary": "one line",
  "indication": "offlabel.longevity | obesity | t2dm | mixed",
  "exposure": { "molecule": "", "dose": "", "source": "brand|compounded|grey", "weeks": 0 },
  "aes": [
    { "term": "", "grade": 1, "expected": true, "relatedness": "probable", "serious": false }
  ],
  "composition": { "weight_quality": "lean_preserved|uncertain|sarcopenic_risk", "protein": "", "resistance_training": "" },
  "disposition": "continue|reduce|hold|stop|ed|refer",
  "investigations": [],
  "follow_up": "48h|1w|4w|12w|ed",
  "safety_net": "if X then Y",
  "off_label_disclosed": true
}
```

The examiner scores `off_label_disclosed`, `indication`, `exposure.source`, and gold `must_address`. If it is in the schema, it is marked.

---

## Scoring

Weights in `fail_closed.json`.

| Domain | Weight | Measures |
|---|---|---|
| Coverage | 0.15 | Core and required asks present as `ask` events |
| Critical detection | 0.25 | Finding-specific elicit IDs actually asked |
| AE classification | 0.15 | Term, grade, expectedness, relatedness |
| Disposition | 0.20 | Matches gold; fail-closed overrides |
| Longevity composition | 0.10 | Protein, lifting, weight_quality |
| Contract | 0.10 | off-label, indication, source, must_address |
| Safety-net | 0.05 | Specific, time-bound, usable tonight |

Pass 0.70. Distinction 0.85. Fail-closed caps the mark at 0.30.

This clinic evaluates **interpretability**: the handoff must show which system was asked, what was found, how it was graded, and what was done.
