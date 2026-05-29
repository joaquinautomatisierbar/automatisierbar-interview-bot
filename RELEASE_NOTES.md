# Release Notes

## build/AUT-115-canary (AUT-115) — [INTERNAL] Pipeline canary

**What changed:** Adds a single-file heartbeat marker `tools/paperclip/CANARY_LASTRUN.md` containing one line: `2026-05-29T20:38:19Z pipeline canary ok`. This is an internal canary build that validates all five build-pipeline agent stages (CTO → Engineer → QA → Product → Release) are operational. Zero impact on `api.py`, Render, Notion, n8n workflows, or any live system — this file is not loaded or referenced at runtime.

### Review the change

```bash
cd "/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview"
git fetch origin
git checkout build/AUT-115-canary
git diff main..HEAD
```

Expected diff: exactly 1 file added (`tools/paperclip/CANARY_LASTRUN.md`), 1 line inserted.

Commit: `356285b Add canary heartbeat marker file (AUT-115)`

### Verify locally

```bash
cat tools/paperclip/CANARY_LASTRUN.md
# Expected: 2026-05-29T20:38:19Z pipeline canary ok
```

File must contain exactly one non-empty line matching `YYYY-MM-DDTHH:MM:SSZ pipeline canary ok`.

### Deploy procedure (when ready)

```bash
git checkout main
git merge --no-ff build/AUT-115-canary
git push origin main
```

Render auto-deploys from `main` push in ~2-3 min. Since this file is not referenced by `api.py` or any workflow, there is zero runtime impact. No env-var changes required.

### Rollback

The change is trivially reversible:

```bash
git revert 356285b
git push origin main
```

Or simply delete the file manually and commit. Render redeploys in ~2-3 min.

### Pre-merge gate

- [x] Branch pushed to `origin/build/AUT-115-canary`
- [x] No commits to `main`
- [x] `.env` confirmed gitignored; diff clean — no secrets
- [x] QA `TEST_PASS` and Product `SHIP` markers on AUT-115
- [ ] Joaquin reviews diff + merges to main *(owner: Joaquin)*

---

## feature/aut-37-validation-textbox-fix (AUT-37)

Two surgical changes to the Interview-Bot. Both ship in a single PR but are
independently revertable. INTERNAL change — Joaquin merges to `main` manually;
Render auto-deploys from `main` only.

### Track A — Process-map row textbox fix

**What changed:** Four cells of every Prozess-Map row (`Wer`, `Tool`, `Daten
rein`, `Daten raus`) flipped from `<input type="text">` to `<textarea rows="1">`.
The `Was passiert` cell was already a textarea. A delegated `input` listener on
`#screen-process-map` calls a new `App._autoGrowTextarea` helper that sets
`height = scrollHeight + 2px` on each keystroke, so the cell grows with the
content and the user always sees the full sentence — even after blur.

**Files:** `static/index.html`
- `.pm-cell textarea` CSS: `resize: none; overflow: hidden; white-space:
  pre-wrap; word-break: break-word` so auto-grown cells don't show scrollbars
  or fight the user's resize handle.
- `App.renderProcessMap()` emits textareas instead of inputs; auto-grow runs
  once on render via `requestAnimationFrame` (so it measures after the screen
  becomes visible).
- `App._autoGrowTextarea(el)` — the shared sizing routine.
- `App.init()`: delegated `input` listener on `#screen-process-map`.

**Why:** Tej, Nico, Patrik couldn't see the value they typed after clicking
away — anything past ~60-80px got clipped because `<input>` only horizontally
scrolls when focused. The acceptance test sentence
"Buchhalterin überträgt PDF in Bexio" now wraps and stays visible on both
desktop ≥900px and mobile <900px.

**Behaviour change to flag:** the Tool cell's `list="common-tools"` autocomplete
attribute is preserved in the markup but is a no-op on `<textarea>` (HTML spec
only honours `list=` on `<input>`). The Q&A flow's separate JS-driven
autocomplete (`_acItems`) is untouched. If the datalist UX in the row template
turns out to be load-bearing, follow-up: add a custom popover-based suggestion
list on the Tool textarea — out of scope for AUT-37.

**API contract:** unchanged. `data-key` attributes preserved; `collectProcessMap`
reads via `.value` which works identically on `<textarea>` and `<input>`. Old
sessions render correctly.

### Track B — Pre-dispatch validation gate

**What changed:** Clicking "An Build-Team senden" no longer fires the n8n
dispatcher webhook directly. It first runs a Sonnet 4.6 completeness pass over
the generated Claude-Code-Prompt. If the brief passes, dispatch proceeds
exactly as before. If gaps are found, the UI lists them inline with two CTAs:

- **Klärung anfordern** — reveals an inline textarea so the operator can add
  context; on save, the new note is appended to the session's `extra_context`
  (via the existing `PATCH /api/session/<id>/extras` route) and validation is
  re-run.
- **Erneut prüfen** — re-run validation without adding context (handles a flaky
  pass).

After 4 passes the UI switches to soft-warn mode: the same gap list plus a
"Trotzdem senden" button that bypasses validation and runs the original
dispatch path. Whichever branch the operator picks, the previously-working
dispatch behaviour is fully preserved when validation passes on first try.

**Files:**

- `tools/claude_client.py` — `validate_brief_completeness(prompt_text,
  process_map, klärungspunkte_text, pass_history) -> dict`. Single Sonnet 4.6
  call with cacheable system prompt, strict JSON output. Returns `status`,
  `missing` (each `{element, question_to_ask_interviewee}`), `reasoning`,
  `cost_usd`. Element labels constrained to the 5-element process-map plus
  `Klärungspunkte`; questions clipped at 400 chars. Cost computed inline from
  `usage.input_tokens` × $3/M + `usage.output_tokens` × $15/M and logged via
  `[claude-stats] label=validate_brief_completeness …`. Validator never raises
  — on any exception it returns `status="pass"` so the dispatch path stays
  unblocked.
- `api.py` — `POST /api/session/<id>/validate`. Guards on `_valid_session_id`,
  refuses if `claude_code_prompt` is missing (409), extracts the
  `## Offene Klärungspunkte` block from the prompt via regex, calls the
  validator, appends the result to `state.validation_passes`, accumulates
  `state.validation_cost_usd`. Returns `{status, missing, pass_number,
  soft_warn: pass_number >= 4, cost_usd_total, reasoning}`. Validator errors
  trip a fail-open path that returns `status="pass"` with HTTP 200 so the
  frontend dispatches anyway.
- `static/index.html` — `App.dispatchBuild()` is now the validation entry point;
  the original direct-dispatch body lives in `App._doDispatch()`. New
  `App._renderValidationGap()` and `App._appendContextAndRevalidate()` paint
  the missing-info UI and wire the "Klärung anfordern" textarea. If
  `/validate` returns non-2xx or throws, the frontend logs a warning and falls
  through to `_doDispatch()` directly — bug in the validator never blocks the
  operator.

**Why:** the AI-Tej/Nico/Patrik chat interview occasionally produces briefs
where one of the 5 process-map elements (Trigger / Data sources /
Transformations / Decision points / Destination) is hand-waved, or the
`Offene Klärungspunkte` block lists items without MVP defaults — both lead to
silent build-team follow-ups that erode customer trust. AUT-37 acceptance
target: zero-followup rate ≥95% (up from ~80% per
`workflows/web_interview_bot.md`).

**Cost:** ~$0.005-0.012 per validation pass at current Sonnet 4.6 pricing,
i.e. ≤$0.05/dispatch even at the 4-pass soft-warn cap. Logged silently to the
session as `validation_cost_usd`; not surfaced to the UI.

**Env vars:** none added. Uses the existing `ANTHROPIC_API_KEY` already
required by `evaluate_context` / `evaluate_answers` / `generate_claude_code_prompt`.

**No regression in:** `/api/session/start`, `/api/session/<id>/answers`,
`/api/session/<id>/process_map`, `/api/session/<id>/prompt`,
`/api/session/<id>/dispatch_build`.

### Halt-policy compliance

- No push to `main`. Branch `feature/aut-37-validation-textbox-fix` only.
- No auto-deploy hook touched. Render still deploys from `main` only.
- No env-var changes.
- No outbound side effects on import — the validator hits Anthropic only when
  the new `/validate` endpoint is called, which is only reachable after
  `claude_code_prompt` has been generated (i.e. after a full interview).

---

## Release Engineer handoff — Joaquin reviews before merge

`[INTERNAL]` artifact staged on GitHub. **Joaquin owns the merge to `main`.**
Release Engineer will NOT push to `main` and will NOT touch the live Render
service. Render auto-deploys from `main` only — merging is the deploy.

### 1. Pull the branch locally

```bash
cd "/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview"
git fetch origin
git checkout feature/aut-37-validation-textbox-fix
git diff main..HEAD                                # full diff for review
git diff main..HEAD -- static/index.html           # Track A only
git diff main..HEAD -- api.py tools/claude_client.py # Track B only
```

Branch tip: `2e40ad7` (single squash) on top of baseline `a2cc1f9` (manual
build-team dispatch infrastructure, pre-existing on this branch and required
for Track B's `/validate` to slot in).

GitHub PR helper (one click): <https://github.com/sexyjoaquin15-cloud/automatisierbar-interview-bot/pull/new/feature/aut-37-validation-textbox-fix>

### 2. Local verification (MacBook, before merge)

```bash
# Optional: smoke-test the Flask app locally on the branch
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ANTHROPIC_API_KEY=$(grep ANTHROPIC_API_KEY .env | cut -d= -f2) python api.py
# Browse http://localhost:5000 and walk Golden-Path A2 in TESTING.md
```

Full reproducible test plan: `TESTING.md` on this branch — Track A textbox
golden-path + Track B validation pass/fail/soft-warn scenarios, with curl
recipes for the new `/api/session/<id>/validate` endpoint and screenshots
checklist.

### 3. Deploy procedure (when ready)

```bash
git checkout main
git merge --no-ff feature/aut-37-validation-textbox-fix     # preserves squash
git push origin main
```

Render auto-deploys from `main` push in ~2-3 min. Release Engineer will
monitor logs for the first 5 min after merge via Render dashboard.

If you prefer the merge-via-PR path, the GitHub PR link above is ready;
"Squash and merge" or "Create a merge commit" both work — the squash on the
feature branch keeps history clean either way.

### 4. Rollback

Full procedure lives in `ROLLBACK.md` on this branch. Quick reference:

- **Both tracks together:** `git revert -m 1 <merge-sha>` on main + push.
- **Track A only (keep validation gate):** `git revert --no-commit <commit-sha-track-A>` — note that since AUT-37 is a single squash, partial revert requires hunk-picking out the `static/index.html` Track A diff; ROLLBACK.md walks through it.
- **Track B only (runtime-disable, no revert):** delete the `/api/session/<id>/validate` endpoint route block in `api.py` and redeploy — the frontend falls open to direct dispatch via its existing fail-open path.

Render auto-redeploys reverted state in ~2-3 min.

### 5. Things Joaquin should specifically eyeball

Per the Product Engineer SHIP comment:

1. Run TESTING.md **Golden-Path A2** in a real Chrome — QA's mobile screenshot
   was taken from a demo HTML, not the production page. Verify the textarea
   auto-grow works on the live route, not just in QA's standalone fixture.
2. The Tool cell autocomplete (`list="common-tools"`) is **silently no-op'd**
   on the new `<textarea>` (HTML spec). The attribute is still in the markup
   but does nothing. Decide whether to file a follow-up issue or accept it.
3. ROLLBACK.md's partial-revert recipe assumes commit-per-track granularity;
   the squash collapses this. Full revert is the safe path; partial requires
   hunk-picking.

### 6. Pre-merge gate (Release Engineer policy)

- [x] Branch pushed to `origin/feature/aut-37-validation-textbox-fix`
- [x] No commits to `main`
- [x] `.env` confirmed gitignored; diff scanned for API-key leakage — clean
- [x] Engineer artifacts (RELEASE_NOTES.md, ROLLBACK.md, TESTING.md) present
- [x] QA `TEST_PASS` and Product Engineer `SHIP` markers logged on AUT-38
- [ ] Joaquin reviews diff + merges to main *(owner: Joaquin)*
- [ ] Release Engineer monitors Render deploy logs (5 min post-merge) *(owner: Release Engineer, on Joaquin's go-ahead)*
