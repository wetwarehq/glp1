# TASK — glp1_clinic

**Room.** Outpatient clinic. Routine follow-up. Drug class: GLP-1 receptor agonists (including dual GIP/GLP-1). Use: off-label longevity.

**Job.** Adverse-event monitoring plus efficacy, at the level of an OSCE station — not a wellness chat, not a primary-care general ROS.

**You are the candidate.** The stem is on the door. Chart is visible. Hidden findings exist only if you ask the right class-specific item. Write a note. Submit. The examiner scores the trace, not your confidence.

---

## What this is not

- Not T2DM clinic by default. Some stations have diabetes; most are euglycaemic longevity users.
- Not "weight-loss coaching." Kilograms without composition is an incomplete efficacy endpoint.
- Not a licence to invent a 40-item pathology panel. Tests are allowed only when a finding opens them.
- Not pharmacovigilance theatre. If the patient needs ED, you send them. If the nausea is CTCAE G1 on a stable dose, you do not stop the drug.

---

## Required behaviour every station

1. **Name the exposure.** Molecule, dose, last titration, source (brand / compounded / grey), missed doses, stacking.
2. **State the indication as the patient understands it** and that this is off-label for longevity if it is.
3. **Systems review is class-specific** (see `systems_review.json`). A generic 14-system ROS that never hits biliary, pancreas, gastroparesis, NAION, SI, or lean-mass loss will fail coverage even if long.
4. **Efficacy is weight quality.** Rate (kg/week), % total body weight, protein g/kg/day, resistance training, strength proxy. A "successful" 15% loss with no protein and no lifting is a safety finding in this usage.
5. **Grade what you find.** CTCAE-style G1–G5 for the dominant AE. Expected vs serious. Relatedness (WHO-UMC: certain / probable / possible / unlikely / unassessable).
6. **Disposition is a verb.** `continue` | `reduce` | `hold` | `stop` | `ed` | `refer`. Then one follow-up interval and a safety-net line the patient could use at 02:00.
7. **Do not treat the boxed warning as trivia.** MTC/MEN2, pregnancy, and "neck lump + hoarseness" are not "reassure and review in 3 months."

---

## Fail-closed (automatic fail, score capped)

- Pancreatitis pattern not sent to ED / drug not held.
- Bowel obstruction / bile-stone cholangitis / AKI-with-anuria treated as "titrate slower."
- Active suicidal ideation not asked, or asked and ignored.
- Sudden monocular field defect treated as dry eye / "see optometrist sometime."
- Grey-market / self-reconstituted peptide dose-adjusted as if it were licensed product.
- Stopping the drug solely for expected G1 nausea on a stable tolerated dose (idiot move, also fail-closed if it is the only action).

---

## Commands (harness)

```
chart                 visible record only
items                 class-specific systems review ids
ask <item_id>         elicit standardised-patient / chart answer
examine               limited exam if the station has one
order <test_id>       only if the station lists it
note                  write JSON assessment (see schema)
submit                freeze trace, copy, score
```

Asking is the clinical act. Unasked hidden findings are missed findings.

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

---

## Scoring (examiner)

| Domain | Weight | What it measures |
|---|---|---|
| Coverage | 0.20 | Core GLP-1 items asked, not generic ROS length |
| Critical detection | 0.25 | Hidden red flags actually elicited |
| AE classification | 0.15 | Term, grade, expectedness, relatedness |
| Disposition | 0.25 | Action matches gold; fail-closed overrides |
| Longevity composition | 0.10 | Protein, lifting, rate of loss — the off-label point |
| Safety-net | 0.05 | Specific, time-bound, patient-usable |

Idiot index (0–1) penalises: shotgun labs, stopping for G1 expected AE, celebrating muscle loss, coaching instead of triage, treating compounded grey product as Ozempic. Final = domain_score × (1 − 0.5 × idiot_index).

Pass 0.70. Distinction 0.85.

---

This environment evaluates a clinical trial agent on **interpretability**: the trace should show *which* system was asked, *what* was found, *how* it was graded, and *what* was done. A fluent paragraph with no asks is a fail.
