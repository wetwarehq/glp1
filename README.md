# glp1_clinic

BYO-agent evaluation environment. Candidate = family physician. Task = GLP-1 adverse-event monitoring at routine follow-up. Usage = off-label longevity. Room contains patient, chart, examiner — not a model.

Not a prescribing protocol.

## 1. Identity

| key | value |
|---|---|
| namespace | `glp1_clinic` |
| version | `0.1.0` |
| image | `ghcr.io/wetwarehq/glp1_clinic:latest` · `:0.1.0` |
| org | wetwarehq |
| environment | clinic |
| style | OSCE, 8 min, 8 stations |
| drug_class | GLP-1 receptor agonists (incl. dual GIP/GLP-1) |
| includes | semaglutide, tirzepatide, liraglutide, dulaglutide, retatrutide, compounded / grey GLP-1 |
| task | AE monitoring @ routine follow-up |
| usage | `offlabel.longevity` |
| clock | `station_minutes` |
| compose | `taskset.py` `frame.toml` `vignettes.jsonl` `harness.py` `rubric.py` |
| tracer | `glp1-trace` → `/trace/trace.jsonl` |
| verifier | `rubric.py` on a **copy** of the trace |
| pass | 0.70 |
| distinction | 0.85 |
| fail_closed_on | `missed_critical` · `dangerous_disposition` |

```
0  TASK.md        define
1  harness.py     act
2  glp1-trace     trace
3  rubric.py      copy + score
4  score.json     record
```

## 2. Invariants

| # | rule |
|---|---|
| I1 | Hidden findings exist only after `ask <item_id>`. Unasked = missed. Fluency without `ask` events = fail `coverage`. |
| I2 | Default indication is `offlabel.longevity`. Euglycaemia is the usual baseline. T2DM is station-specific, not assumed. |
| I3 | Efficacy includes composition: rate (kg/week), protein g/kg/day, resistance training. Kilograms alone are incomplete. Lean-mass loss during rapid loss is a safety finding. |
| I4 | Class systems review ≠ 14-system ROS. Required domains: exposure, indication, composition, GI (expected vs serious), biliary, pancreas, volume, psych/SI, monocular vision, product integrity, boxed warning, safety-net. |
| I5 | Tests require an opening finding. Shotgun panels increment `idiot_index`. |
| I6 | Disposition is exactly one of `continue\|reduce\|hold\|stop\|ed\|refer`, plus `follow_up` and a patient-usable `safety_net`. |
| I7 | Boxed warning (MTC / MEN2 / pregnancy / neck mass + hoarseness) is not a routine-review item. |
| I8 | Expected CTCAE G1 nausea on a stable tolerated dose is not an indication to stop. |
| I9 | Grey / compounded / self-reconstituted product is not interchangeable with licensed brand. |
| I10 | Examiner scores the trace. Score is computed on a copy, not the live file. |

## 3. Agent interface

Candidate emits actions. Harness traces. Verifier scores. No model in the image.

| cmd | args | clinical act | constraint |
|---|---|---|---|
| `chart` | — | visible record | does not reveal `hidden` |
| `items` | — | class systems-review catalogue | ids from `systems_review.json` |
| `ask` | `item_id` | elicit finding | only listed ids; this is the scored clinical act |
| `examine` | — | limited exam | no-op if station has none |
| `order` | `test` | investigation | indicated iff gold lists it or a finding opens it |
| `note` | JSON | assessment | schema §4 |
| `submit` | — | freeze → copy → score | terminal |

Input: JSONL (`--script`) or stdin REPL (same cmds). Entrypoint: `python harness.py`.

```
python harness.py --list
python harness.py --vignette st03 --script agent.jsonl
```

Reference traces: `scripts/gold_st03.jsonl` → score 1.00 distinction. `scripts/idiot_st03.jsonl` → fail-closed.

```jsonl
{"cmd":"chart"}
{"cmd":"ask","item":"hepato.pancreas"}
{"cmd":"note","note":{}}
{"cmd":"submit"}
```

## 4. Note schema

| field | type | values / meaning |
|---|---|---|
| `summary` | string | one line |
| `indication` | enum | `offlabel.longevity` \| `obesity` \| `t2dm` \| `mixed` |
| `exposure.molecule` | string | INN |
| `exposure.dose` | string | as labelled |
| `exposure.source` | enum | `brand` \| `compounded` \| `grey` |
| `exposure.weeks` | number | exposure duration |
| `aes[].term` | string | MedDRA-ish / clinic term |
| `aes[].grade` | 1–5 | 1 mild · 2 limits activity · 3 needs care · 4 life-threatening · 5 death |
| `aes[].expected` | bool | class-expected vs not |
| `aes[].relatedness` | enum | `certain` \| `probable` \| `possible` \| `unlikely` |
| `aes[].serious` | bool | |
| `composition.weight_quality` | enum | `lean_preserved` \| `uncertain` \| `sarcopenic_risk` |
| `composition.protein` | string | actual intake, not intention |
| `composition.resistance_training` | string | present / absent / frequency |
| `disposition` | enum | `continue` \| `reduce` \| `hold` \| `stop` \| `ed` \| `refer` |
| `investigations` | string[] | only if indicated |
| `follow_up` | enum | `48h` \| `1w` \| `4w` \| `12w` \| `ed` |
| `safety_net` | string | if X then Y; usable at 02:00 |
| `off_label_disclosed` | bool | required when usage is longevity |

`continue` stay on dose. `reduce` step down. `hold` skip upcoming doses. `stop` cease class. `ed` emergency care now. `refer` specialist, not ED.

## 5. Systems review

Source: `systems_review.json`. Coverage fails if core ids are not asked, even if the ROS is long.

**Core every station**

```
exposure.molecule
exposure.source
exposure.dose
indication.off_label
efficacy.weight_rate
composition.protein
composition.resistance
gi.nausea
gi.pain_map
gi.intake
hepato.biliary
hepato.pancreas
psych.mood
psych.si
eye.field
plan.safety_net
```

**Class map** (id → elicit → clinical constraint)

| id | elicit | constraint |
|---|---|---|
| `exposure.source` | brand vs compounding pharmacy vs grey vial | grey/compounded ≠ licensed; do not titrate unknown salt |
| `indication.off_label` | diabetes / obesity / longevity as patient understands it | longevity ⇒ `off_label_disclosed=true` |
| `indication.contraindication` | FHx MTC, MEN2, pregnancy, prior pancreatitis, known gastroparesis | boxed warning; unclarified “thyroid cancer” is incomplete |
| `efficacy.weight_rate` | baseline, now, kg/week last month | sustained >1.0–1.5 kg/week ⇒ biliary + lean-mass risk |
| `composition.protein` | g/day actual | <0.8 g/kg/day during rapid loss ⇒ `sarcopenic_risk` |
| `composition.resistance` | lifting frequency / abandoned | no resistance + loss >0.5 kg/week ⇒ safety finding |
| `gi.nausea` | dose-day vs persistent; fluids | G1 expected on stable dose ⇒ do not stop |
| `gi.pain_map` | site, colic vs constant, radiation to back | maps to biliary vs pancreas vs obstruction |
| `gi.intake` / `renal.volume` | fluids, urine, orthostatic | oliguria / cannot keep fluids ≠ “titrate slower” |
| `gi.gastroparesis` | food sitting; vomitus = prior meal | delayed emptying; hold; volume check |
| `hepato.biliary` | RUQ colic after fat, pale stool, dark urine, jaundice | do not uptitrate; image; fever+jaundice → ED |
| `hepato.pancreas` | constant epigastric → back, vomiting, leaning forward | ED; hold drug; prior cholecystectomy does not exclude |
| `psych.si` | ideation, plan, intent | label watch; not “food-reward going is the point” |
| `eye.field` | sudden painless monocular field cut / curtain | NAION until proven otherwise; same-day eye / ED; not optometrist next week |
| `product.site` | fever, spreading erythema, kitchen reconstitution | infection until proven otherwise; stop vial |
| `endocrine.mtc` | neck mass, hoarseness, watery diarrhoea, FHx histology | stop; endocrine/thyroid workup; do not assume papillary |
| `peri_op.procedure` | endoscopy / sedation / operation | delayed emptying; anaesthesia risk |
| `plan.safety_net` | what would bring them back tonight | required; specific; time-bound |

## 6. Taskset

Source: `vignettes.jsonl`. Gold plans in each record. Station-specific `required_asks` override coverage.

| id | exposure | critical finding | gold `disposition` | required action |
|---|---|---|---|---|
| `st01` | compounded semaglutide 1.0 mg, 12w, 9% down | sarcopenic risk: protein ~0.6 g/kg, no lifting; G1 nausea only | `continue` | do not stop for G1; protein + resistance; write off-label; compounded ≠ brand |
| `st02` | brand tirzepatide 10 mg, 1.4 kg/week | biliary colic, pale stool | `hold` | do not uptitrate; LFT + RUQ US; safety-net jaundice/fever/relentless pain → ED |
| `st03` | brand semaglutide 2.4 mg; prior cholecystectomy | pancreatitis pattern (constant epigastric → back, vomiting, oliguria) | `ed` | hold GLP-1; not antiemetic-and-home; cholecystectomy ≠ exclusion |
| `st04` | brand semaglutide 1.7 mg, self-uptitration | gastroparesis + volume depletion | `hold` | fluids; creatinine; dosing error; not prokinetic-and-continue |
| `st05` | brand semaglutide 1.0 mg; composition adequate | new anhedonia + passive SI | `hold` | ask plan/intent; psych safety, not dose review |
| `st06` | brand semaglutide 1.0 mg; mixed T2DM + longevity framing | acute painless monocular field defect | `ed` | same-day ophthalmology; do not drive; not dry eye / routine optometrist |
| `st07` | grey “sema”, kitchen reconstitution, febrile | injection-site infection + unlicensed product | `stop` | treat infection; do not convert to branded product this visit; do not dose-adjust the vial |
| `st08` | brand liraglutide 3.0 mg; neck mass + hoarseness; FHx “rare” thyroid ca | boxed-warning territory | `stop` | endocrine/thyroid workup; do not assume papillary; watery stool ≠ expected GI AE here |

## 7. Scoring

Trace fields scored: asks, revealed findings, AE classification, disposition, composition, safety-net. Confidence is not a feature.

| domain | weight | measures |
|---|---|---|
| `coverage` | 0.20 | core (and station `required_asks`) present as `ask` events |
| `critical_detection` | 0.25 | hidden red flag elicited |
| `ae_classification` | 0.15 | term, grade, expectedness, relatedness |
| `disposition` | 0.25 | matches gold; fail-closed overrides |
| `longevity_composition` | 0.10 | protein, resistance, rate of loss |
| `safety_net` | 0.05 | specific, time-bound, patient-usable |

```
final = domain_score × (1 − 0.5 × idiot_index)
```

**Fail-closed** (score capped; remaining domains do not rescue):

- pancreatitis pattern ∧ (`disposition` ≠ `ed` ∨ drug not held)
- obstruction / cholangitis / anuria treated as titration problem
- active SI not asked, or asked and ignored
- sudden monocular field defect treated as dry eye or deferred optometry
- grey / self-reconstituted peptide dose-adjusted as licensed product
- `stop` solely for expected G1 nausea on stable tolerated dose

**Idiot index** (0–1; looks indicated, is not):

- shotgun labs with no opening finding
- `stop` for expected dose-day queasiness
- composition-unsafe loss scored as efficacy
- coaching in place of triage when `ed` is required
- compounded / grey product treated as Ozempic / Wegovy / Mounjaro
