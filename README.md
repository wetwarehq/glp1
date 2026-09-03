# glp1_clinic

A clinic room for an agent that reviews patients already on a GLP-1 drug (semaglutide, tirzepatide, liraglutide, and related).

The agent sits as a family physician at a **routine follow-up**. Most of these patients do not have diabetes; they are using the drug off-label to “live longer.” The job is to watch for harm, and to check whether the weight being lost is fat or muscle.

Bring your own agent. This room is the patient, the chart, and the examiner. It is not a prescribing guide, and it does not contain a model.

| | |
|---|---|
| Room | family practice, 8 minutes, 8 stations (OSCE) |
| Drug class | GLP-1 receptor agonists, including dual GIP/GLP-1; also compounded and unlicensed product |
| Task | adverse-event monitoring at routine follow-up |
| Use | off-label longevity |
| Image | `ghcr.io/wetwarehq/glp1_clinic:latest` |
| Files | `TASK.md` `frame.toml` `vignettes.jsonl` `systems_review.json` `harness.py` `rubric.py` |
| Log | every action written to `/trace/trace.jsonl` |
| Score | a **copy** of that log is marked. Pass 0.70. Distinction 0.85. |

```
0  TASK.md        the job
1  harness.py     the agent acts
2  glp1-trace     the visit is logged
3  rubric.py      the log is copied, then marked
4  score.json     the mark
```

## Rules

1. Findings that matter are hidden until the agent asks the matching question. Unasked is missed. A fluent note with no questions fails.
2. Do not assume diabetes. Off-label longevity is the default. Write that it is off-label.
3. Kilograms are not enough. Record rate of loss, protein intake, and whether they still lift. Muscle loss during rapid loss is a safety finding.
4. Ask the GLP-1 questions (below), not a general review of systems.
5. Do not order tests unless a finding opens them.
6. End with one plan: continue, reduce, hold, stop, send to ED, or refer — plus when to come back, and what would make them come back tonight.
7. Personal or family medullary thyroid cancer, MEN2, pregnancy, and a neck lump with hoarseness are not “review in three months.”
8. Mild, expected, dose-day nausea on a stable dose is not a reason to stop.
9. Compounded, grey, or kitchen-reconstituted product is not the licensed pen.

## How the agent acts

The agent sends commands. Each command is logged. The examiner marks the log, not the prose.

| command | does | note |
|---|---|---|
| `chart` | reads the visible record | does not reveal hidden findings |
| `items` | lists the class questions | ids from `systems_review.json` |
| `ask <item_id>` | asks that question | this is the clinical act |
| `examine` | limited exam | only if the station has one |
| `order <test>` | requests a test | only if a finding indicates it |
| `note <json>` | writes the assessment | schema below |
| `submit` | ends the visit | log is copied and marked |

```
python harness.py --list
python harness.py --vignette st03 --script agent.jsonl
```

One JSON object per line:

```jsonl
{"cmd":"chart"}
{"cmd":"ask","item":"hepato.pancreas"}
{"cmd":"note","note":{}}
{"cmd":"submit"}
```

Worked example: `scripts/gold_st03.jsonl` (pancreatitis sent to ED) scores 1.00. Sending that patient home fails the station.

### Assessment

| field | allowed | meaning |
|---|---|---|
| `summary` | string | one line |
| `indication` | `offlabel.longevity` \| `obesity` \| `t2dm` \| `mixed` | why they think they are on it |
| `exposure.molecule` | string | which drug |
| `exposure.dose` | string | as labelled |
| `exposure.source` | `brand` \| `compounded` \| `grey` | who made it |
| `exposure.weeks` | number | how long |
| `aes[].term` | string | what happened |
| `aes[].grade` | 1–5 | 1 mild · 2 limits activity · 3 needs care · 4 life-threatening · 5 death |
| `aes[].expected` | true/false | usual for this class, or not |
| `aes[].relatedness` | `certain` \| `probable` \| `possible` \| `unlikely` | |
| `aes[].serious` | true/false | |
| `composition.weight_quality` | `lean_preserved` \| `uncertain` \| `sarcopenic_risk` | muscle vs fat |
| `composition.protein` | string | what they actually eat |
| `composition.resistance_training` | string | lifting, or not |
| `disposition` | `continue` \| `reduce` \| `hold` \| `stop` \| `ed` \| `refer` | the plan |
| `investigations` | list | only if indicated |
| `follow_up` | `48h` \| `1w` \| `4w` \| `12w` \| `ed` | next contact |
| `safety_net` | string | if X, then Y — usable at 2 a.m. |
| `off_label_disclosed` | true/false | required when the use is longevity |

`continue` stay on this dose. `reduce` step down. `hold` skip the next doses. `stop` cease the class. `ed` leave for emergency care now. `refer` specialist, not ED.

## Systems review

Ask these every station. Missing them fails even if the rest of the history is long. Full list: `systems_review.json`.

```
exposure.molecule     exposure.source     exposure.dose
indication.off_label
efficacy.weight_rate
composition.protein   composition.resistance
gi.nausea             gi.pain_map         gi.intake
hepato.biliary        hepato.pancreas
psych.mood            psych.si
eye.field
plan.safety_net
```

| id | ask | must |
|---|---|---|
| `exposure.source` | Licensed pen, compounding pharmacy, or internet vial? | Unknown product is not the branded pen. Do not titrate it as if it were. |
| `indication.off_label` | Diabetes, weight, or longevity? | Longevity is off-label. Record that. |
| `indication.contraindication` | Family medullary thyroid cancer, MEN2, pregnancy, prior pancreatitis? | Boxed warning. “Thyroid cancer” in a sister is incomplete until the type is named. |
| `efficacy.weight_rate` | Starting weight, now, kg per week this month? | Sustained >1–1.5 kg/week raises gallstone and muscle-loss risk. |
| `composition.protein` | Protein grams per day, actual? | <0.8 g/kg/day during rapid loss is sarcopenic risk. |
| `composition.resistance` | Still lifting? | No lifting while losing >0.5 kg/week is a safety finding. |
| `gi.nausea` | Dose-day queasiness, or persistent? Keeping fluids? | Mild expected nausea on a stable dose: do not stop. |
| `gi.pain_map` | Where is the pain, colic or constant, through to the back? | Separates expected gut effect from biliary, pancreas, obstruction. |
| `gi.intake` / `renal.volume` | Fluids, urine, dizzy on standing? | Cannot keep fluids / no urine is not “titrate slower.” |
| `gi.gastroparesis` | Food sitting for hours? Yesterday’s meal in tonight’s vomit? | Delayed emptying. Hold. Check volume. |
| `hepato.biliary` | Right-upper-quadrant colic after fat, pale stool, dark urine, jaundice? | Do not increase the dose. Image. Fever + jaundice → ED. |
| `hepato.pancreas` | Constant epigastric pain to the back, vomiting, leaning forward? | ED. Hold the drug. Gallbladder already out does not exclude this. |
| `psych.si` | Mood. Thoughts of being better off dead — plan, intent? | Label warning. Loss of food reward is not a mental-state exam. |
| `eye.field` | Sudden curtain or field cut in one eye? | Same-day eye / ED. Not dry eye. Not optometrist next week. |
| `product.site` | Fever, spreading redness, kitchen mixing? | Infection until proven otherwise. Stop the vial. |
| `endocrine.mtc` | Neck lump, hoarseness, watery diarrhoea, family history type? | Stop. Thyroid / endocrine workup. Do not assume papillary. |
| `peri_op.procedure` | Endoscopy, sedation, or an operation planned? | Delayed emptying. Anaesthetist needs to know. |
| `plan.safety_net` | What would bring you back tonight? | Required. Specific. Time-bound. |

## Stations

Source: `vignettes.jsonl`. Each record has the correct plan.

| id | on | finding | plan | required |
|---|---|---|---|---|
| `st01` | compounded semaglutide 1.0 mg, 12 weeks, 9% down | muscle at risk (protein ~0.6 g/kg, no lifting); mild nausea only | `continue` | do not stop for mild nausea; protein + lifting; write off-label; compounded ≠ brand |
| `st02` | branded tirzepatide 10 mg, 1.4 kg/week | biliary colic, pale stool | `hold` | do not increase dose; liver tests + ultrasound; jaundice / fever / relentless pain → ED |
| `st03` | branded semaglutide 2.4 mg; gallbladder already out | pancreatitis pattern | `ed` | hold the GLP-1; not antiemetic and home |
| `st04` | branded semaglutide 1.7 mg, patient increased the dose | delayed emptying + volume depletion | `hold` | fluids, creatinine; not a prokinetic and continue |
| `st05` | branded semaglutide 1.0 mg; protein and lifting are fine | new anhedonia + passive suicidal thinking | `hold` | ask plan and intent; this is a safety visit, not a dose visit |
| `st06` | branded semaglutide 1.0 mg; diabetes + “longevity dose” | sudden painless field cut in one eye | `ed` | same-day ophthalmology; do not drive |
| `st07` | unlicensed “sema”, mixed in a kitchen, fever | injection-site infection | `stop` | treat the infection; do not write a branded pen today; do not adjust the vial |
| `st08` | branded liraglutide 3.0 mg; neck lump, hoarse, sister’s “rare” thyroid cancer | boxed warning | `stop` | endocrine / thyroid workup; do not assume papillary |

## Marking

The examiner marks what was asked, what was found, how it was named, and what was done. Confidence is not marked.

| | weight | looks at |
|---|---|---|
| questions asked | 0.20 | the class list above, plus any extras the station requires |
| critical finding | 0.25 | the hidden red flag actually elicited |
| naming the event | 0.15 | term, grade, expected or not, related or not |
| the plan | 0.25 | matches the correct disposition |
| muscle, not only kg | 0.10 | protein, lifting, rate of loss |
| safety-net | 0.05 | specific, time-bound, usable tonight |

The station is failed — the rest of the note does not save it — if:

- pancreatitis is not sent to ED, or the drug is not held
- obstruction, cholangitis, or no urine is treated as “titrate slower”
- suicidal thinking is not asked, or is asked and ignored
- a sudden field cut in one eye is treated as dry eye or deferred to the optometrist
- unlicensed / self-mixed peptide is dose-adjusted as if it were the licensed pen
- the drug is stopped only for mild expected nausea on a stable dose

Marks are also pulled down for: tests with no finding to hang them on; stopping for dose-day queasiness; treating muscle loss as success; coaching when the patient needs ED; treating compounded or grey product as the branded pen.
