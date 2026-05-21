# ROLLBACK — AUT-29 fix

## What was changed

**File:** `api.py`  
**Branch:** `fix/AUT-29-generate-prompt-non-fatal`  
**Commit:** `d68035f`

Inside `_write_payoff_safely._worker()`, the call to `generate_claude_code_prompt`
was wrapped in its own `try/except`. On failure, `prompt_text` is `None` and
`write_payoff_to_page` is still called (Q&A Archive + process map write, build-prompt
block skipped). Previously any exception from the LLM call aborted the entire worker
thread before `write_payoff_to_page` was reached.

## How to revert

```bash
cd /home/paperclip/automatisierbar-interview-bot
git checkout fix/AUT-22-full-feature-restore
```

Or on Render: redeploy the previous deploy from the Render dashboard
(Deploys → previous green deploy → "Rollback to this deploy").

## Regression risk

**Low.** The change only adds error isolation around one function call; no
behaviour changes when `generate_claude_code_prompt` succeeds. The only new
observable difference is:

- On LLM failure: Notion page now gets Q&A Archive + process-map without build-prompt
  (previously: nothing written at all).
- Render logs now emit an `ERROR` entry instead of swallowing the failure silently.

## Verification after deploy

1. Open Render logs and confirm no `"payoff write failed (non-fatal)"` entries after
   a completed interview.
2. If `generate_claude_code_prompt` still fails (e.g. missing `ANTHROPIC_API_KEY`),
   you will now see `"payoff: generate_claude_code_prompt failed: …"` at ERROR level.
3. The Notion lead page should show `heading_2: "Interview-Verlauf (Q&A)"` and Q&A
   blocks even on prompt-generation failure.
4. When the LLM call succeeds, behavior is identical to before this fix.
