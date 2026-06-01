# Rollback — AUT-46

## Marketing image pipeline — render tools + agent/skill updates

**Branch:** `build/AUT-46-marketing-image-pipeline`

All changes are additive. Rollback is file-deletion + optional Notion schema remove. No Render deploy, no n8n activation touched.

### Severity 1 (< 2 min) — Remove render tools, revert brief prompt

If the render tools cause import errors or break the cron pipeline:

```bash
rm tools/render_linkedin_image.py tools/render_n8n_workflow_diagram.py
git revert HEAD~1  # reverts the commit that added the render tools + brief synthesis
git push origin build/AUT-46-marketing-image-pipeline
```

Image Curator automatically falls back to spec-only output (no actual PNGs generated). Pipeline keeps running without images — same behaviour as before AUT-46.

### Severity 2 — Revert agent/skill instruction changes

If the live Paperclip agent instructions cause bad behaviour in a Friday run, restore the previous versions from git history:

```bash
git log --oneline build/AUT-46-marketing-image-pipeline  # find the pre-AUT-46 commit
# Then restore each file individually:
git show <pre-AUT-46-sha>:tools/paperclip/companies/automatisierbar-build/agents/image-curator/AGENTS.md \
  > /home/paperclip/automatisierbar-build/agents/image-curator/AGENTS.md
git show <pre-AUT-46-sha>:tools/paperclip/companies/automatisierbar-build/agents/pr-director/AGENTS.md \
  > /home/paperclip/automatisierbar-build/agents/pr-director/AGENTS.md
git show <pre-AUT-46-sha>:tools/paperclip/companies/automatisierbar-build/skills/suggest-linkedin-image/SKILL.md \
  > /home/paperclip/automatisierbar-build/skills/suggest-linkedin-image/SKILL.md
```

### Severity 3 — Remove Notion Image Files property

If the `Image Files` property on the Post Variants DB causes Notion API errors:

1. Open Notion DB `013ef8bc-4837-44c3-bfa2-b8b15792fb80`.
2. Click the `Image Files` property header → **Delete property**.
3. Existing variant rows are unaffected (the property is additive).

### Deployment note

No Render service or n8n workflow was activated by this change. After rollback to main, no redeployment is required — the MacBook Friday cron picks up the reverted tools on the next run.

---

# Rollback — AUT-22

## Q&A Archive in Notion payoff (commit 7e64cdb)

This is a purely additive change (one new parameter + new Notion blocks). Rollback options:

**Revert commit on branch (before merge):**
```bash
git revert 7e64cdb
git push origin fix/AUT-22-full-feature-restore
```

**Revert after merge to main:**
```bash
git revert <merge-sha> -m 1  # or revert 7e64cdb directly if fast-forward
git push origin main
```

Existing Notion pages that already have the "Interview-Verlauf (Q&A)" section are unaffected (Notion blocks are not deleted by a code rollback). Future payoff writes will stop appending the Q&A section. No session-state schema changes — `all_qa` was already in the state; rollback only removes the rendering call.

**Deployment note:** Render is auto-deployed from `fix/AUT-7-bug-02-03-04` (not from `main` — see SHA mismatch note in AUT-22 comments). After merge+rollback to `main`, Render must be manually triggered to redeploy from `main`.

---

# Rollback — AUT-37

The two tracks are independently revertable. Pick the one(s) you need to back
out. Both routes assume the feature branch has already been merged to `main`.

## Both tracks together (fastest)

```bash
# Identify the merge commit
git log --oneline --merges -5

# Revert it on main and push
git revert -m 1 <merge-sha>
git push origin main
```

Render auto-deploys the reverted state in ~2-3 minutes. The validator endpoint
and the textarea row template both disappear in the same step. Existing
in-flight sessions are unaffected — the session-state schema additions
(`validation_passes`, `validation_cost_usd`) are extra keys that older code
silently ignores.

## Track A only — back out the textbox fix, keep validation gate

```bash
git revert --no-commit <commit-sha-track-A>
git checkout HEAD -- RELEASE_NOTES.md ROLLBACK.md  # keep the docs
git commit -m "Revert AUT-37 Track A (textbox fix)"
git push origin main
```

Track A is a pure `static/index.html` diff:

- `.pm-cell textarea` CSS additions (lines ~570-583).
- `App.renderProcessMap()` row template (lines ~1366-1374) reverts to `<input
  type="text">` for `who`, `tool`, `data_in`, `data_out`.
- `App._autoGrowTextarea()` helper and the delegated `input` listener on
  `#screen-process-map` are removed.

No backend change to revert. Track B keeps working.

## Track B only — back out validation gate, keep textbox fix

```bash
git revert --no-commit <commit-sha-track-B>
git checkout HEAD -- RELEASE_NOTES.md ROLLBACK.md  # keep the docs
git commit -m "Revert AUT-37 Track B (validation gate)"
git push origin main
```

Track B touches three files:

- `tools/claude_client.py` — remove `validate_brief_completeness` + the
  `_SONNET_*_USD_PER_M` constants + the `_VALIDATE_SYSTEM` prompt block.
- `api.py` — remove the `validate_session` view function (the `@app.route(
  "/api/session/<session_id>/validate")` block).
- `static/index.html` — restore `dispatchBuild()` to the original body (currently
  in `_doDispatch()`) and delete `_renderValidationGap`,
  `_appendContextAndRevalidate`, and the new `dispatchBuild` wrapper.

The frontend's fail-open path means partial reverts are safe: if you leave
the frontend wrapper in place but delete the backend endpoint, the wrapper
catches the 404 and dispatches directly. If you leave the backend in place
but revert the frontend wrapper, `/validate` is just an unused endpoint.

## Session-state cleanup (optional, not required for rollback)

After rollback, existing sessions that ran ≥1 validation pass will have these
extra keys in their State JSON on Notion:

- `validation_passes` — list of pass records
- `validation_cost_usd` — cumulative float

Older `notion_session.py` code paths ignore unknown keys, so leaving them
in place is fine. If you want a clean state, run a one-off Notion script
that strips both keys. Not required for the rollback to be functional.

## Render-side

No env-var changes were made for AUT-37, so nothing to undo on the Render
dashboard. Auto-deploy is wired to `main` only — once the revert merge lands,
the rollback is complete in one deploy cycle.

---

# Rollback — AUT-149

## Fix /prompt 500 (async generation + state=None)

5 commits were merged directly to `main`. All changes are in `api.py`,
`tools/claude_client.py`, and `static/index.html`. No schema changes,
no new credentials, no external side-effects during rollback.

### Full revert (all 5 AUT-149 commits)

```bash
# Revert in reverse-commit order (newest first):
git revert --no-edit 24fa52b ccdf27a cc2e689 7f125f0 9ceed81
git push origin main
# Render auto-deploys the reverted state in ~2-3 minutes
```

### What each commit did (for surgical partial rollback)

| SHA | File | What it does |
|---|---|---|
| `24fa52b` | `api.py` | `_prompt_errors` dict — prevents repeated LLM-call spam on failure |
| `cc2e689` | `api.py`, `static/index.html` | Core fix: async generation + frontend polling loop (202 response) |
| `ccdf27a` | `api.py` | Single LLM retry on cold-start + exc_info logging |
| `7f125f0` | `api.py` | exc_info=True + exception type in error string |
| `9ceed81` | `tools/claude_client.py` | ANTHROPIC_API_KEY .get() + RuntimeError instead of KeyError |

### Session-state safety

No Notion schema changes. Existing sessions are unaffected — the endpoint
only reads from and writes to the `claude_code_prompt` key already present
in session state. Rollback does not corrupt any session.

### Render-side

No env-var changes were made for AUT-149. After revert + push to main,
Render auto-deploys. No manual Render dashboard steps needed.

### Note on `_prompt_generating` / `_prompt_errors` in-flight state

These are in-process dicts (not persisted). On Render the instance restarts
after redeploy — both dicts are cleared automatically. No stale state survives
a rollback deploy.

---

# Rollback — AUT-156

## Interviewer Selector + Re-evaluate Button (Changes 1 & 2)

**Branch:** `build/AUT-156-interviewer-selector-reevaluate`
**Commit:** `2f2a1dc`

All changes are in `api.py` (+80 lines) and `static/index.html` (+106 lines). No schema changes, no new credentials, no new environment variables.

### Full revert (both changes together)

```bash
git revert --no-edit 2f2a1dc
git push origin build/AUT-156-interviewer-selector-reevaluate
# Render auto-deploys the reverted state in ~2-3 minutes
```

### Change 1 only — revert interviewer selector (frontend)

If the pill selector causes UI regressions but `/reevaluate` should stay:

```bash
# Cherry-pick what to keep or manually restore the three frontend hunks:
# - Remove .pill-interviewer / .pill-interviewer--active CSS (~line 136)
# - Remove the <div class="field-group"> pill block (~line 829)
# - Revert startSession() body: remove `interviewer: this.selectedInterviewer`
# - Remove App.selectedInterviewer and App.setInterviewer()
```

No backend change to revert for Change 1 — api.py already stored `interviewer` before AUT-156.

### Change 2 only — revert /reevaluate route + frontend panel

If the re-evaluate flow causes issues but the selector should stay:

**Backend (`api.py`):** Remove the `reevaluate_session` view function (the `@app.route("/api/session/<session_id>/reevaluate")` block, ~80 lines added at line 463).

**Frontend (`static/index.html`):**
- Remove `#reevaluate-section` div (~line 1036)
- Remove `_reevaluateLock` state property
- Remove the `showROI()` reveal block for `reevaluate-section` (~line 1860)
- Remove the `resetROI()` cleanup block for `reevaluate-section` (~line 2308)
- Remove `toggleReevaluate()` and `submitReevaluate()` methods

### Session-state safety

The `extra_context` field in Notion session state is APPENDED to (never overwritten). Existing sessions that had no `extra_context` are unaffected — the field defaults to `""`. Rollback does not corrupt existing session state.

### Render-side

No env-var changes were made for AUT-156. After revert + push to the branch, Render auto-deploys from whatever branch is wired to production. No manual Render dashboard steps needed.
