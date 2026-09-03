# glp1_clinic

OSCE room for a **clinical trial agent** specialised on **GLP-1 receptor agonists**.

Task: adverse-event monitoring at **routine follow-up**.
Usage: **off-label longevity**.
Style: **OSCE stations**. Image: `ghcr.io/wetwarehq/glp1_clinic`.

This is a scoring environment, not a protocol for unsupervised prescribing.

## Room

```
0  TASK.md              task is defined
1  harness.py           agent acts on the room
2  runtime (rust)       room is traced
3  rubric.py            trace is copied then scored
4  /score/score.json    score is recorded
```

## Run

```sh
python harness.py --list
python harness.py --vignette st03 --script scripts/gold_st01.jsonl
docker run --rm -it ghcr.io/wetwarehq/glp1_clinic:latest --vignette st02
```

Commands inside the room: `chart` `items` `ask <item_id>` `examine` `order <test>` `note <json>` `submit`.

Hidden findings exist only if the candidate asks the class-specific item. A fluent paragraph with no asks is a fail.

## Stations

| ID | Title | The actual problem |
|---|---|---|
| st01 | The uneventful twelve-week | Expected G1 nausea. The miss is sarcopenic-risk loss. |
| st02 | Tuesday night RUQ | Biliary colic after 1.4 kg/week. Do not uptitrate. |
| st03 | I thought it was the dose | Pancreatitis pattern. ED. Hold. |
| st04 | Food just sits there | Gastroparesis + volume depletion after self-titration. |
| st05 | I don't enjoy anything | Anhedonia + passive SI. FDA watch. |
| st06 | A curtain over the lower vision | Acute monocular field defect. Same-day eye. |
| st07 | Research peptide, same thing | Grey vial, febrile nodule. Not a titration. |
| st08 | Neck lump, sister’s thyroid | Boxed warning territory. Stop. |

## Scoring

Pass 0.70. Distinction 0.85. Fail-closed (score capped 0.30) on missed pancreatitis-to-ED, NAION-to-eye, active SI ignored, grey-product dose-adjust, MTC signal continued.

Idiot index penalises shotgun labs, stopping for expected G1 nausea, celebrating muscle loss, coaching instead of triage.

## Systems review

Class-specific, not a 14-system ROS. See `systems_review.json` and `TASK.md`.
