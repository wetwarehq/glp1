# glp1

A clinic room for an agent that reviews patients already on a GLP-1 drug (semaglutide, tirzepatide, liraglutide, and related).

The agent sits as a family physician at a **routine follow-up**. Most of these patients do not have diabetes; they are using the drug off-label to “live longer.” The job is to watch for harm, and to check whether the weight being lost is fat or muscle.

Bring your own agent. This room is the patient, the chart, and the examiner. It is not a prescribing guide, and it does not contain a model.

<table>
<tbody>
<tr><th>Room</th><td>family practice, 8 minutes, 8 stations (OSCE)</td></tr>
<tr><th>Drug class</th><td>GLP-1 receptor agonists, including dual GIP/GLP-1; also compounded and unlicensed product</td></tr>
<tr><th>Task</th><td>adverse-event monitoring at routine follow-up</td></tr>
<tr><th>Use</th><td>off-label longevity</td></tr>
<tr><th>Image</th><td><code>ghcr.io/wetwarehq/glp1:latest</code></td></tr>
<tr><th>Files</th><td><code>TASK.md</code> <code>frame.toml</code> <code>vignettes.jsonl</code> <code>systems_review.json</code> <code>harness.py</code> <code>rubric.py</code></td></tr>
<tr><th>Log</th><td>every action written to <code>/trace/trace.jsonl</code></td></tr>
<tr><th>Score</th><td>a <strong>copy</strong> of that log is marked. Pass 0.70. Distinction 0.85.</td></tr>
</tbody>
</table>

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

<table>
<thead>
<tr><th>command</th><th>does</th><th>note</th></tr>
</thead>
<tbody>
<tr><td><code>chart</code></td><td>reads the visible record</td><td>does not reveal hidden findings</td></tr>
<tr><td><code>items</code></td><td>lists the class questions</td><td>ids from <code>systems_review.json</code></td></tr>
<tr><td><code>ask <item_id></code></td><td>asks that question</td><td>this is the clinical act</td></tr>
<tr><td><code>examine</code></td><td>limited exam</td><td>only if the station has one</td></tr>
<tr><td><code>order <test></code></td><td>requests a test</td><td>only if a finding indicates it</td></tr>
<tr><td><code>note <json></code></td><td>writes the assessment</td><td>schema below</td></tr>
<tr><td><code>submit</code></td><td>ends the visit</td><td>log is copied and marked</td></tr>
</tbody>
</table>

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

<table>
<thead>
<tr><th>field</th><th>allowed</th><th>meaning</th></tr>
</thead>
<tbody>
<tr><td><code>summary</code></td><td>string</td><td>one line</td></tr>
<tr><td><code>indication</code></td><td><code>offlabel.longevity</code> | <code>obesity</code> | <code>t2dm</code> | <code>mixed</code></td><td>why they think they are on it</td></tr>
<tr><td><code>exposure.molecule</code></td><td>string</td><td>which drug</td></tr>
<tr><td><code>exposure.dose</code></td><td>string</td><td>as labelled</td></tr>
<tr><td><code>exposure.source</code></td><td><code>brand</code> | <code>compounded</code> | <code>grey</code></td><td>who made it</td></tr>
<tr><td><code>exposure.weeks</code></td><td>number</td><td>how long</td></tr>
<tr><td><code>aes[].term</code></td><td>string</td><td>what happened</td></tr>
<tr><td><code>aes[].grade</code></td><td>1–5</td><td>1 mild · 2 limits activity · 3 needs care · 4 life-threatening · 5 death</td></tr>
<tr><td><code>aes[].expected</code></td><td>true/false</td><td>usual for this class, or not</td></tr>
<tr><td><code>aes[].relatedness</code></td><td><code>certain</code> | <code>probable</code> | <code>possible</code> | <code>unlikely</code></td><td></td></tr>
<tr><td><code>aes[].serious</code></td><td>true/false</td><td></td></tr>
<tr><td><code>composition.weight_quality</code></td><td><code>lean_preserved</code> | <code>uncertain</code> | <code>sarcopenic_risk</code></td><td>muscle vs fat</td></tr>
<tr><td><code>composition.protein</code></td><td>string</td><td>what they actually eat</td></tr>
<tr><td><code>composition.resistance_training</code></td><td>string</td><td>lifting, or not</td></tr>
<tr><td><code>disposition</code></td><td><code>continue</code> | <code>reduce</code> | <code>hold</code> | <code>stop</code> | <code>ed</code> | <code>refer</code></td><td>the plan</td></tr>
<tr><td><code>investigations</code></td><td>list</td><td>only if indicated</td></tr>
<tr><td><code>follow_up</code></td><td><code>48h</code> | <code>1w</code> | <code>4w</code> | <code>12w</code> | <code>ed</code></td><td>next contact</td></tr>
<tr><td><code>safety_net</code></td><td>string</td><td>if X, then Y — usable at 2 a.m.</td></tr>
<tr><td><code>off_label_disclosed</code></td><td>true/false</td><td>required when the use is longevity</td></tr>
</tbody>
</table>

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

<table>
<thead>
<tr><th>id</th><th>ask</th><th>must</th></tr>
</thead>
<tbody>
<tr><td><code>exposure.source</code></td><td>Licensed pen, compounding pharmacy, or internet vial?</td><td>Unknown product is not the branded pen. Do not titrate it as if it were.</td></tr>
<tr><td><code>indication.off_label</code></td><td>Diabetes, weight, or longevity?</td><td>Longevity is off-label. Record that.</td></tr>
<tr><td><code>indication.contraindication</code></td><td>Family medullary thyroid cancer, MEN2, pregnancy, prior pancreatitis?</td><td>Boxed warning. “Thyroid cancer” in a sister is incomplete until the type is named.</td></tr>
<tr><td><code>efficacy.weight_rate</code></td><td>Starting weight, now, kg per week this month?</td><td>Sustained >1–1.5 kg/week raises gallstone and muscle-loss risk.</td></tr>
<tr><td><code>composition.protein</code></td><td>Protein grams per day, actual?</td><td><0.8 g/kg/day during rapid loss is sarcopenic risk.</td></tr>
<tr><td><code>composition.resistance</code></td><td>Still lifting?</td><td>No lifting while losing >0.5 kg/week is a safety finding.</td></tr>
<tr><td><code>gi.nausea</code></td><td>Dose-day queasiness, or persistent? Keeping fluids?</td><td>Mild expected nausea on a stable dose: do not stop.</td></tr>
<tr><td><code>gi.pain_map</code></td><td>Where is the pain, colic or constant, through to the back?</td><td>Separates expected gut effect from biliary, pancreas, obstruction.</td></tr>
<tr><td><code>gi.intake</code> / <code>renal.volume</code></td><td>Fluids, urine, dizzy on standing?</td><td>Cannot keep fluids / no urine is not “titrate slower.”</td></tr>
<tr><td><code>gi.gastroparesis</code></td><td>Food sitting for hours? Yesterday’s meal in tonight’s vomit?</td><td>Delayed emptying. Hold. Check volume.</td></tr>
<tr><td><code>hepato.biliary</code></td><td>Right-upper-quadrant colic after fat, pale stool, dark urine, jaundice?</td><td>Do not increase the dose. Image. Fever + jaundice → ED.</td></tr>
<tr><td><code>hepato.pancreas</code></td><td>Constant epigastric pain to the back, vomiting, leaning forward?</td><td>ED. Hold the drug. Gallbladder already out does not exclude this.</td></tr>
<tr><td><code>psych.si</code></td><td>Mood. Thoughts of being better off dead — plan, intent?</td><td>Label warning. Loss of food reward is not a mental-state exam.</td></tr>
<tr><td><code>eye.field</code></td><td>Sudden curtain or field cut in one eye?</td><td>Same-day eye / ED. Not dry eye. Not optometrist next week.</td></tr>
<tr><td><code>product.site</code></td><td>Fever, spreading redness, kitchen mixing?</td><td>Infection until proven otherwise. Stop the vial.</td></tr>
<tr><td><code>endocrine.mtc</code></td><td>Neck lump, hoarseness, watery diarrhoea, family history type?</td><td>Stop. Thyroid / endocrine workup. Do not assume papillary.</td></tr>
<tr><td><code>peri_op.procedure</code></td><td>Endoscopy, sedation, or an operation planned?</td><td>Delayed emptying. Anaesthetist needs to know.</td></tr>
<tr><td><code>plan.safety_net</code></td><td>What would bring you back tonight?</td><td>Required. Specific. Time-bound.</td></tr>
</tbody>
</table>

## Stations

Source: `vignettes.jsonl`. Each record has the correct plan.

<table>
<thead>
<tr><th>id</th><th>on</th><th>finding</th><th>plan</th><th>required</th></tr>
</thead>
<tbody>
<tr><td><code>st01</code></td><td>compounded semaglutide 1.0 mg, 12 weeks, 9% down</td><td>muscle at risk (protein ~0.6 g/kg, no lifting); mild nausea only</td><td><code>continue</code></td><td>do not stop for mild nausea; protein + lifting; write off-label; compounded ≠ brand</td></tr>
<tr><td><code>st02</code></td><td>branded tirzepatide 10 mg, 1.4 kg/week</td><td>biliary colic, pale stool</td><td><code>hold</code></td><td>do not increase dose; liver tests + ultrasound; jaundice / fever / relentless pain → ED</td></tr>
<tr><td><code>st03</code></td><td>branded semaglutide 2.4 mg; gallbladder already out</td><td>pancreatitis pattern</td><td><code>ed</code></td><td>hold the GLP-1; not antiemetic and home</td></tr>
<tr><td><code>st04</code></td><td>branded semaglutide 1.7 mg, patient increased the dose</td><td>delayed emptying + volume depletion</td><td><code>hold</code></td><td>fluids, creatinine; not a prokinetic and continue</td></tr>
<tr><td><code>st05</code></td><td>branded semaglutide 1.0 mg; protein and lifting are fine</td><td>new anhedonia + passive suicidal thinking</td><td><code>hold</code></td><td>ask plan and intent; this is a safety visit, not a dose visit</td></tr>
<tr><td><code>st06</code></td><td>branded semaglutide 1.0 mg; diabetes + “longevity dose”</td><td>sudden painless field cut in one eye</td><td><code>ed</code></td><td>same-day ophthalmology; do not drive</td></tr>
<tr><td><code>st07</code></td><td>unlicensed “sema”, mixed in a kitchen, fever</td><td>injection-site infection</td><td><code>stop</code></td><td>treat the infection; do not write a branded pen today; do not adjust the vial</td></tr>
<tr><td><code>st08</code></td><td>branded liraglutide 3.0 mg; neck lump, hoarse, sister’s “rare” thyroid cancer</td><td>boxed warning</td><td><code>stop</code></td><td>endocrine / thyroid workup; do not assume papillary</td></tr>
</tbody>
</table>

## Marking

The examiner marks what was asked, what was found, how it was named, and what was done. Confidence is not marked.

<table>
<thead>
<tr><th></th><th>weight</th><th>looks at</th></tr>
</thead>
<tbody>
<tr><th>questions asked</th><td>0.20</td><td>the class list above, plus any extras the station requires</td></tr>
<tr><th>critical finding</th><td>0.25</td><td>the hidden red flag actually elicited</td></tr>
<tr><th>naming the event</th><td>0.15</td><td>term, grade, expected or not, related or not</td></tr>
<tr><th>the plan</th><td>0.25</td><td>matches the correct disposition</td></tr>
<tr><th>muscle, not only kg</th><td>0.10</td><td>protein, lifting, rate of loss</td></tr>
<tr><th>safety-net</th><td>0.05</td><td>specific, time-bound, usable tonight</td></tr>
</tbody>
</table>

The station is failed — the rest of the note does not save it — if:

- pancreatitis is not sent to ED, or the drug is not held
- obstruction, cholangitis, or no urine is treated as “titrate slower”
- suicidal thinking is not asked, or is asked and ignored
- a sudden field cut in one eye is treated as dry eye or deferred to the optometrist
- unlicensed / self-mixed peptide is dose-adjusted as if it were the licensed pen
- the drug is stopped only for mild expected nausea on a stable dose

Marks are also pulled down for: tests with no finding to hang them on; stopping for dose-day queasiness; treating muscle loss as success; coaching when the patient needs ED; treating compounded or grey product as the branded pen.
