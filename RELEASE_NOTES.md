# Release Notes

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
