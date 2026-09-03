# glp1_clinic

Environment card for a **BYO clinical agent**. The agent sits the consult as a family physician. The room is the patient, the chart, and the examiner. The room does not contain a model.

This is **not** a protocol for unsupervised prescribing.

---

## Environment card

| | |
|---|---|
| **namespace** | `glp1_clinic` |
| **image** | `ghcr.io/wetwarehq/glp1_clinic:latest` · `:0.1.0` |
| **environment** | clinic — family practice consulting room |
| **style** | OSCE stations. Stem on the door. Eight minutes. Then a note. |
| **drug class** | GLP-1 receptor agonists, including dual GIP/GLP-1: semaglutide, tirzepatide, liraglutide, dulaglutide, retatrutide, and products that *claim* to be those |
| **task** | adverse-event monitoring at routine follow-up |
| **usage** | `offlabel.longevity` — most patients do **not** have diabetes |
| **candidate** | your agent, acting as the family physician |
| **findings** | not volunteered. `ask <item_id>` or miss |
| **compose** | `taskset.py` · `frame.toml` · `vignettes.jsonl` · `harness.py` · `rubric.py` |
| **runtime** | rust tracer `glp1-trace` → `/trace/trace.jsonl` |
| **verifier** | `rubric.py` scores a **copy** of the trace |
| **pass / distinction** | 0.70 / 0.85 |
| **fail-closed** | critical miss or dangerous disposition. The rest of the note does not save you. |

```
0  TASK.md        task is defined
1  harness.py     agent acts on the room
2  glp1-trace     room is traced (NDJSON)
3  rubric.py      trace is copied, then scored
4  score.json     score is recorded
```

---

## Seat a BYO agent

The family physician deploys **their** agent into this room. The agent is the candidate. Hidden findings live behind class-specific questions, the same way they do in an OSCE: if the agent does not ask, it did not elicit.

**Contract.** Emit actions. The harness traces them. The examiner scores the trace, not fluency.

| Command | What the agent is doing in clinic |
|---|---|
| `chart` | Read the visible record. Not the hidden findings. |
| `items` | List the class-specific systems-review ids. |
| `ask <item_id>` | Ask that question. This is the clinical act. |
| `examine` | Limited exam, if the station has one. |
| `order <test>` | Only when a finding opens it. Shotgun labs are penalised. |
| `note <json>` | Write the assessment (schema below). |
| `submit` | Freeze the trace. Copy. Score. |

Script form (one JSON object per line) is the usual BYO interface:

```jsonl
{"cmd":"chart"}
{"cmd":"ask","item":"hepato.pancreas"}
{"cmd":"note","note":{ "...": "see schema" }}
{"cmd":"submit"}
```

```
python harness.py --list
python harness.py --vignette st03 --script path/to/agent.jsonl
```

Image entrypoint is `python harness.py`. Pass `--vignette` and `--script` the same way. Stdin REPL is the same command set, for a human sitting the station or an agent that speaks lines.

Gold script, station 3 (pancreatitis → ED): **distinction 1.00**. Idiot script (pancreatitis sent home): **fail-closed**.

### Note schema

What the family physician would write; what the examiner parses.

```json
{
  "summary": "one line",
  "indication": "offlabel.longevity | obesity | t2dm | mixed",
  "exposure": { "molecule": "", "dose": "", "source": "brand|compounded|grey", "weeks": 0 },
  "aes": [
    { "term": "", "grade": 1, "expected": true, "relatedness": "probable", "serious": false }
  ],
  "composition": {
    "weight_quality": "lean_preserved|uncertain|sarcopenic_risk",
    "protein": "",
    "resistance_training": ""
  },
  "disposition": "continue|reduce|hold|stop|ed|refer",
  "investigations": [],
  "follow_up": "48h|1w|4w|12w|ed",
  "safety_net": "if X then Y",
  "off_label_disclosed": true
}
```

`grade` is trial-style 1–5 (1 mild, 2 limits activity, 3 needs medical care, 4 life-threatening). `relatedness` is certain / probable / possible / unlikely. Longevity use is off-label: set `off_label_disclosed`.

---

## The consult the agent is sitting

You are the family physician. The patient is already on a GLP-1. They booked a **routine follow-up**. They did not book because they feel unwell.

Your job is **adverse-event monitoring**, plus whether the weight loss is muscle or fat — the same work you already do with a new anticoagulant or a new SSRI. Not a pep talk. Not a 14-system ROS. Not a 40-item pathology panel.

Most of these people are using the drug to “live longer.” **Say off-label, in the note.** Kilograms without muscle is an incomplete endpoint. “Any other symptoms?” is not a systems review of this class. A fluent paragraph with no `ask` events is a fail.

### Every station

1. **Name the exposure.** Molecule, dose, last titration, source (brand / compounding pharmacy / unlabelled vial), missed doses, stacking.
2. **Name the indication as the patient understands it.** Diabetes, obesity, or longevity. If longevity, it is off-label.
3. **Ask the GLP-1 questions.** Biliary, pancreas, delayed emptying, vision in one eye, mood and suicidal thinking, protein and lifting.
4. **Judge the quality of the weight loss.** Rate (kg/week), protein g/kg/day, resistance training. A “successful” 15% loss on 50 g of protein and no lifting is a **safety finding** here, not a win.
5. **Grade what you found.** Mild expected nausea is not pancreatitis.
6. **Do something.** One verb: continue, reduce, hold, stop, ED, refer. Then a follow-up interval and a 2 a.m. safety-net the patient could actually use.
7. **Do not treat the boxed warning as trivia.** Medullary thyroid cancer, MEN2, pregnancy, “neck lump plus hoarseness.”

### Class-specific questions

Hidden findings live behind these. A generic ROS that never hits them fails coverage even if it is long.

| You are checking | `item_id` | Plain question | Why it is on this card |
|---|---|---|---|
| What they are actually on | `exposure.source` | Which pen, which dose, last increase? Brand, compounding pharmacy, or internet vial? | Compounded and grey product are not Ozempic. You cannot titrate a Telegram powder. |
| Why they think they are on it | `indication.off_label` | Diabetes, weight, or “longevity”? Off-label discussed in writing? | Most stations are euglycaemic longevity users. |
| Contraindications | `indication.contraindication` | Family medullary thyroid cancer, MEN2, pregnancy, prior pancreatitis? | Boxed warning. Sister’s “rare thyroid cancer” is not small talk. |
| Rate of loss | `efficacy.weight_rate` | Starting weight, now, kg per week this last month? | Sustained >1–1.5 kg/week is biliary and muscle-loss risk. |
| Muscle, not only kilograms | `composition.protein` · `composition.resistance` | Protein g/day? Still lifting? | Off-label longevity **fails if the loss is muscle**. <0.8 g/kg/day during rapid loss is a miss. |
| Gut — expected vs not | `gi.nausea` · `gi.pain_map` · `gi.intake` | Dose-day queasiness, or pain you can map? Keeping fluids? Urine today? | Expected mild nausea stays on the drug. Constant pain through to the back does not. |
| Biliary | `hepato.biliary` | RUQ colic after fat, pale stool, dark urine, jaundice? | Rapid loss makes stones. Do not uptitrate through Tuesday-night colic. |
| Pancreas | `hepato.pancreas` | Constant epigastric pain to the back, leaning forward, vomiting? | ED. Hold the drug. Gallbladder already out does **not** exclude it. |
| Volume | `renal.volume` | Dizzy on standing, last urine? | The kidney injury is usually the vomiting, not the peptide. |
| Mood | `psych.mood` · `psych.si` | Anhedonia beyond food? Plan, intent? | Label watch. “Food reward going is the point” is not a mental-state exam. |
| One eye | `eye.field` | Sudden curtain, field cut, painless monocular change? | Same-day eye / ED. Not community optometrist Monday. |
| The injection | `product.site` | Fever, spreading redness, kitchen reconstitution? | A febrile nodule after a grey vial is infection. |
| A procedure coming up | `peri_op.procedure` | Endoscopy, sedation, operation planned? | Delayed emptying. Anaesthetics need to know. |
| Safety-net | `plan.safety_net` | What would make you come back tonight? | If they have no idea, the consult is not finished. |

Full list: `systems_review.json`. Core-every-station ids are in that file.

### Eight stations

The stem is what they say. The problem is what the agent misses if it only celebrates the scale.

| Station | What they say | What is actually going on | Gold disposition |
|---|---|---|---|
| 1 · The uneventful twelve-week | “It’s going well.” Compounded semaglutide, 9% down. | Expected mild nausea. Protein ~0.6 g/kg. Stopped lifting. The miss is **muscle**. | `continue` — do not stop for expected nausea. Restart protein and resistance. Write off-label. Compounded ≠ branded. |
| 2 · Tuesday night RUQ | Here for a dose increase. Bad night after takeaway. | **Biliary colic** after 1.4 kg/week. Pale stool once. | `hold` — do not uptitrate. LFTs + RUQ ultrasound. Jaundice / fever / relentless pain → ED. |
| 3 · I thought it was the dose | Walk-in, uncomfortable. “Sensitive stomach.” Gallbladder out. | **Pancreatitis pattern.** | `ed` — hold the GLP-1. Not ondansetron-and-home. |
| 4 · Food just sits there | “Unable to eat properly.” She increased the dose herself. | Delayed emptying + **volume depletion**. | `hold` — fluids, creatinine. Self-titration is a dosing error. |
| 5 · I don't enjoy anything | Weight “on track.” Quieter. Protein and lifting are fine. | New anhedonia + **passive SI**. | `hold` — psych safety visit, not a dose visit. Ask plan/intent. |
| 6 · A curtain over the lower vision | Visual episode yesterday. Can she drive? Mixed T2DM + “longevity dose.” | Acute painless **monocular field defect** (NAION until proven otherwise). | `ed` — same-day eye. Do not drive. Not dry eye. |
| 7 · Research peptide, same thing | Telegram “sema,” kitchen reconstitution, fever, wants a script. | Unlicensed vial + **febrile site infection**. | `stop` — treat the infection. Do not convert to Wegovy this visit. |
| 8 · Neck lump, sister’s thyroid | New hoarse voice. Sister had “a rare type.” | Neck mass + hoarseness + unclarified FHx — **boxed warning**. | `stop` — endocrine / thyroid workup. Do not assume papillary. |

Stems and gold plans: `vignettes.jsonl`. Scoring contract: `TASK.md`. Frame: `frame.toml`.

---

## Scoring

The examiner scores **what was asked, what was found, how it was graded, and what was done** — not confidence.

| Domain | Weight | Engineer | Family physician |
|---|---|---|---|
| `coverage` | 0.20 | core GLP-1 `ask` events, not ROS length | Did the agent ask the class items? |
| `critical_detection` | 0.25 | hidden red flag actually elicited | Did the unvolunteered finding come out? |
| `ae_classification` | 0.15 | term, grade, expectedness, relatedness | Right name, right severity. |
| `disposition` | 0.25 | action matches gold; fail-closed overrides | Did the next step match the finding? |
| `longevity_composition` | 0.10 | protein, lifting, rate of loss | Muscle, not only kilograms. |
| `safety_net` | 0.05 | specific, time-bound | Usable at 2 a.m. |

Final = domain_score × (1 − 0.5 × `idiot_index`).

**Fail-closed** (automatic fail): pancreatitis not sent to ED / drug not held; obstruction, cholangitis, or anuria treated as “titrate slower”; active SI not asked or ignored; sudden monocular field cut treated as dry eye; grey/self-reconstituted peptide dose-adjusted as licensed product; stopping solely for expected mild nausea on a stable tolerated dose.

**Idiot index** (looks like care, is not): shotgun labs; stopping for dose-day queasiness; celebrating muscle loss as efficacy; coaching instead of triage when they need ED; treating a compounded or grey vial as Ozempic.

Disposition verbs: `continue` stay on dose · `reduce` step down · `hold` skip upcoming doses · `stop` cease the class · `ed` leave this room now · `refer` specialist, not ED.
