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
