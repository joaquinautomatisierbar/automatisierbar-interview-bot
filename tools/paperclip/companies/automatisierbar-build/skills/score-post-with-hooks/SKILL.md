---
name: score-post-with-hooks
description: >
  Score a LinkedIn post draft 1-10 against Hormozi Hook + Retain + Reward + CTA
  criteria. Outputs a breakdown + improvement note. Used by Hook Strategist agent.
  Not for rewriting — only for scoring + flagging.
---

# Score Post With Hooks

A LinkedIn post draft gets a score. Four dimensions, each 1-10. Average = the headline rating.

## The 4 dimensions

### 1. `hook_strength` (1-10)

How strong is the FIRST SENTENCE?

| Score | Hook quality |
|---|---|
| 9-10 | Stops the scroll instantly. Concrete number + outcome OR contrarian claim + curiosity gap. Reader MUST read sentence 2. |
| 7-8 | Solid hook. Specific, surprising, or question that surfaces real pain. Reader probably reads sentence 2. |
| 5-6 | Generic but functional. "Diese Woche habe ich gelernt…" — works but not memorable. |
| 3-4 | Vague generality. "In der heutigen schnelllebigen Welt…" |
| 1-2 | Buzzword opener, "Liebe Community", or "Heute möchte ich teilen". Auto-fail. |

If hook is buzzword-laden (skalierbar, ganzheitlich, End-to-End, Mehrwert, Synergie) → cap at 3.

### 2. `specificity` (1-10)

How many concrete numbers/names does the post carry?

| Score | Specificity |
|---|---|
| 9-10 | ≥3 concrete numbers (CHF, time, count) + ≥1 named customer/situation. Reader visualizes immediately. |
| 7-8 | 2 concrete numbers + 1 specific anecdote. |
| 5-6 | 1 concrete number + general reference. |
| 3-4 | 0 numbers but specific story. |
| 1-2 | Pure abstraction, no numbers, no anchor. |

### 3. `arc_quality` (1-10)

Does it follow Hook → Retain → Reward?

| Score | Arc |
|---|---|
| 9-10 | Clean 3-beat arc. Hook lands, anecdote pays it off, lesson + CTA closes. |
| 7-8 | Arc present but one beat is weak (often the Retain). |
| 5-6 | 2 of 3 beats present. |
| 3-4 | Hook + Reward but no Retain (no story to bridge). |
| 1-2 | No discernible arc — just a wall of thoughts. |

### 4. `cta_quality` (1-10)

Does it close with a question/invitation that pulls engagement?

| Score | CTA |
|---|---|
| 9-10 | Sharp question tied to the reader's reality ("Wo siehst du das in deiner Kanzlei?"). |
| 7-8 | Question but slightly generic ("Was denkst du dazu?"). |
| 5-6 | Statement-CTA ("Lass uns sprechen wenn du es probieren willst"). |
| 3-4 | "Tell me in the comments!" or other American-flavored CTA. |
| 1-2 | No CTA, just trails off. |

## Final rating

`rating = round((hook_strength + specificity + arc_quality + cta_quality) / 4)`

Cap at 9 unless it's truly outlier. 10 reserved for "this is the post we'd run a paid promotion behind."

## Improvement note rules

If `rating <= 5`: write a one-sentence note pointing at the SINGLE weakest dimension's fix.

Example:
- "Hook is generic — try opening with the '5h pro Woche' number instead of 'Diese Woche'."
- "Specificity weak — pick one named Treuhand case and anchor the anecdote there."

If `rating >= 6`: improvement_note is optional. Set null OR a small tightening suggestion.

## Effect goal classification

Independently of rating, classify what the post actually achieves:

- `trust-build` — demonstrates expertise / shows the work / vulnerability moment
- `lead-warm` — surfaces pain, invites self-identification, opens conversation
- `brand-grow` — broad value / philosophy / opinion that builds reach
- `proof` — named case study with concrete results

If a draft requested `trust-build` but you observe it's actually `brand-grow`, set `effect_goal` to what it actually is + flag in `improvement_note`.

## Output format

Return JSON only:

```json
{
  "hook_confirmed": "H3",
  "rating": 8,
  "rating_breakdown": {
    "hook_strength": 8,
    "specificity": 9,
    "arc_quality": 7,
    "cta_quality": 7
  },
  "effect_goal": "trust-build",
  "improvement_note": null
}
```

## What this skill does NOT do

- It does NOT rewrite drafts. Score + note; Copy Writer rewrites.
- It does NOT decide whether to ship — PR Director makes that call based on rating + how unique the angle is.
- It does NOT rank drafts against each other — score each independently.
