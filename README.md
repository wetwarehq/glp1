# GLP-1 review, as a family physician would sit it

This is an **eight-minute consulting room**.

You are the GP. The patient is already on a GLP-1 receptor agonist (semaglutide, tirzepatide, liraglutide, or something that claims to be). They booked a **routine follow-up**. Your job is **adverse-event monitoring** — the same work you already do with a new anticoagulant or a new SSRI — not a weight-loss pep talk, and not a 14-system review of systems.

Most of these patients **do not have diabetes**. They are using the drug to “live longer” or “stay sharp.” That use is **off-label**. Say so, out loud, in the note.

This repository is a scoring environment (OSCE stations) for a clinical agent. It is **not** a protocol for unsupervised prescribing.

```
ghcr.io/wetwarehq/glp1_clinic:latest
ghcr.io/wetwarehq/glp1_clinic:0.1.0
```

---

## What this visit actually is

In fellowship language this is an OSCE: stem on the door, chart on the desk, eight minutes, then a note. In clinic language it is the 12-week review you already run — except the findings that matter **are not volunteered**. If you do not ask the class-specific question, you did not elicit the finding. A fluent paragraph with no questions is a fail.

You are not in diabetes clinic by default. Kilograms without muscle is an incomplete endpoint. A 40-item pathology panel with no indication is not thoroughness.

---

## What you must do every time

Same sequence you would use for any high-stakes review.

1. **Name the exposure.** Which molecule, which dose, last time it went up, who made it (licensed brand, compounding pharmacy, or an unlabelled vial), missed doses, anything stacked with it.
2. **Name the indication as the patient understands it.** Diabetes, obesity, or longevity. If it is longevity, it is off-label. Write that down.
3. **Ask the GLP-1 questions**, not a general ROS. Biliary, pancreas, delayed emptying, vision in one eye, mood and suicidal thinking, protein and lifting. Length of the consult does not substitute for hitting those.
4. **Judge the quality of the weight loss.** Rate (kg/week), protein in g/kg/day, resistance training. A “successful” 15% loss with 50 g of protein and no lifting is a safety finding in this usage, not a win.
5. **Grade what you found.** Mild expected nausea is not pancreatitis. Use a 1–5 severity (CTCAE-style) and whether it is expected on this class. Relatedness: certain / probable / possible / unlikely.
6. **Do something.** One verb: continue, reduce, hold, stop, send to ED, or refer. Then a follow-up interval, and a 2 a.m. safety-net the patient could actually use.
7. **Do not treat the boxed warning as trivia.** Personal or family medullary thyroid cancer, MEN2, pregnancy, and “neck lump plus hoarseness” are not “reassure, review in three months.”

---

## The questions — class-specific, not a 14-system ROS

Ask these. The hidden findings live behind them.

| You are checking | Plain question | Why a GP asks it |
|---|---|---|
| What they are actually on | Which pen, which dose, last increase? Licensed brand, compounding pharmacy, or internet vial? | Compounded and grey product are not Ozempic. You cannot titrate a Telegram powder. |
| Why they think they are on it | Diabetes, weight, or “longevity”? Was off-label discussed in writing? | Most stations are euglycaemic longevity users. Say it. |
| Contraindications | Family medullary thyroid cancer, MEN2, pregnancy, prior pancreatitis, known gastroparesis? | Boxed warning. Sister’s “rare thyroid cancer” is not small talk. |
| Rate of loss | Starting weight, now, kg per week this last month? | Sustained >1–1.5 kg/week is a biliary and muscle-loss problem, not a badge. |
| Muscle, not only kilograms | Protein grams per day? Still lifting? Stairs, grip, jumpers looser in the shoulders? | Off-label longevity **fails if the loss is muscle**. <0.8 g/kg/day during rapid loss is a miss. |
| Gut — expected vs not | Dose-day queasiness, or pain you can map? Food sitting for hours? Keeping fluids? Urine today? | Expected mild nausea stays on the drug. Constant pain through to the back does not. Undigested food the next day is delayed emptying, not “titrate slower.” |
| Biliary | RUQ colic after a fatty meal, pale stool, dark urine, jaundice? | Rapid loss makes stones. Do not uptitrate through Tuesday-night colic. |
| Pancreas | Constant epigastric pain to the back, leaning forward, vomiting, cannot get comfortable? | That pattern leaves the room for ED. The drug is held. This is not a dose problem. |
| Mood | Anhedonia beyond food? Passive or active suicidal thinking? | FDA label watch. “Food reward going is the point” is not a mental-state exam. |
| One eye | Sudden curtain, field cut, new painless monocular change? | Same-day eye / ED. Not optometrist Monday. Not lubricating drops. |
| Safety-net | What would make you come back tonight? | If they have no idea what an emergency looks like, you have not finished the consult. |

A generic “any other symptoms?” that never hits those items fails coverage even if it is long.

---

## The eight patients

Each station is one consulting-room problem. The stem is what they say. The actual problem is what you will miss if you only celebrate the scale.

| Station | What they say | What is actually going on | What a GP does |
|---|---|---|---|
| 1 · The uneventful twelve-week | “It’s going well. No questions.” Compounded semaglutide, 9% down. | Expected mild (G1) nausea. Protein ~0.6 g/kg. Stopped lifting. The miss is **muscle**. | Continue the drug. Do **not** stop for expected nausea. Restart protein and resistance. Write the off-label consent. Compounded is not branded. |
| 2 · Tuesday night RUQ | Here for a dose increase. Mentions a bad night after takeaway. | **Biliary colic** after 1.4 kg/week. Pale stool once. | Do not uptitrate. Hold. LFTs and RUQ ultrasound. Safety-net jaundice / fever / relentless pain → ED. |
| 3 · I thought it was the dose | Walk-in, looks uncomfortable. “Sensitive stomach.” Gallbladder already out. | **Pancreatitis pattern**: constant epigastric pain to the back, vomiting, oliguria. | ED now. Hold the GLP-1. Do not give ondansetron and send home. Cholecystectomy does not exclude pancreatitis. |
| 4 · Food just sits there | “Unable to eat properly.” She increased the dose herself. | Delayed emptying plus **volume depletion**. Yesterday’s pasta in tonight’s vomit. Dizzy on standing. | Hold. Fluids. Creatinine. Self-titration is a dosing error. Not metoclopramide-and-continue. |
| 5 · I don't enjoy anything | Weight is “on track.” Quieter than last visit. Protein and lifting are actually fine. | New anhedonia and **passive suicidal ideation**. FDA watch. | This is a psych safety visit, not a dose visit. Ask plan/intent. Hold is defensible. Do not book a 12-week review and leave. |
| 6 · A curtain over the lower vision | Visual episode yesterday. Can she drive to the coast? Mixed T2DM + “longevity dose.” | Acute painless **monocular field defect**. Treat as NAION until proven otherwise. | Same-day ophthalmology / ED eye. Do not drive. Not community optometrist next week. Not dry eye. |
| 7 · Research peptide, same thing | Telegram “sema,” kitchen reconstitution, fever, wants a proper script today. | Unlicensed vial, **febrile injection-site infection**. | Stop the vial. Treat the infection. Do not convert this into branded Wegovy in the same consult. |
| 8 · Neck lump, sister’s thyroid | New hoarse voice. Sister had “a rare type” of thyroid cancer. | Neck mass + hoarseness + unclarified family history — **boxed-warning territory**. | Stop. Endocrine / thyroid workup. Do not assume papillary. Watery stool here is not “the usual GLP-1 diarrhoea.” |

---

## You fail the station if you miss these

“Fail-closed” means the rest of the consult does not save you. Same as missing meningism in a fever exam.

- Pancreatitis pattern not sent to ED, or the drug not held.
- Bowel obstruction, cholangitis, or anuria treated as “titrate slower.”
- Active suicidal ideation not asked, or asked and ignored.
- Sudden field cut in one eye treated as dry eye or “see the optometrist sometime.”
- Grey-market / self-reconstituted peptide **dose-adjusted as if it were licensed product**.
- Stopping the drug solely for expected mild nausea on a stable, tolerated dose.

---

## You also lose marks for the tempting GP errors

The “idiot index” is the examiner’s name for moves that look like care and are not.

- Shotgun labs with no finding to hang them on.
- Stopping the class for expected dose-day queasiness.
- Celebrating muscle loss as efficacy.
- Coaching (“have you tried protein powder?”) instead of triage when the patient needs ED.
- Treating a compounded or grey vial as if it were Ozempic.

---

## How the examiner marks you

Pass **0.70**. Distinction **0.85**. The examiner scores the **trace** — what you asked, what you found, how you graded it, what you did — not your confidence.

| Domain | Weight | In clinic language |
|---|---|---|
| Coverage | 0.20 | Did you ask the GLP-1 items, or a long general ROS that missed pancreas and one eye? |
| Critical detection | 0.25 | Did the hidden red flag actually get elicited? |
| AE classification | 0.15 | Right term, right severity, expected vs not, related vs coincidental. |
| Disposition | 0.25 | Did the action match the finding? Fail-closed overrides a pretty note. |
| Body composition | 0.10 | Protein, lifting, rate of loss — the off-label point. |
| Safety-net | 0.05 | Specific, time-bound, usable at 2 a.m. |

Final mark is pulled down by the idiot index. A perfect-sounding note that sends pancreatitis home is a fail.

Disposition verbs, as a GP would write them:

| Verb | Meaning |
|---|---|
| `continue` | Stay on the current dose. |
| `reduce` | Step down. |
| `hold` | Skip upcoming doses; review soon. |
| `stop` | Cease the class. |
| `ed` | Leave this room for emergency care now. |
| `refer` | Specialist, not ED. |

---

## What this is not

- Not T2DM clinic by default. Some stations have diabetes; most are euglycaemic longevity users.
- Not weight-loss coaching. Kilograms without composition is an incomplete efficacy endpoint.
- Not a licence to invent a 40-item pathology panel.
- Not pharmacovigilance theatre. If they need ED, they go. If the nausea is mild on a stable dose, you do not stop the drug.

Asking is the clinical act. Unasked findings are missed findings.

---

## For the machine

Room pipeline: `TASK.md` defines the job → `harness.py` is the consult → rust runtime traces it → `rubric.py` scores a copy → `/score/score.json` is the record.

Commands in the room: `chart` `items` `ask <item_id>` `examine` `order <test>` `note <json>` `submit`.

```sh
python harness.py --list
python harness.py --vignette st03 --script scripts/gold_st03.jsonl
```

Gold script on station 3 (pancreatitis to ED): **1.00 distinction**. Idiot script (pancreatitis sent home): **fail-closed**.

Class-specific review: `systems_review.json`. Station stems and gold plans: `vignettes.jsonl`. Scoring contract: `TASK.md`.
