---
name: browser-test
description: Browser-test a web/UI artifact (n8n Form, dashboard, web app) with headless Playwright via the CLI — drive a real browser, assert acceptance criteria, screenshot, return a JSON verdict. Use whenever a build produces something a human would open in a browser; validate_workflow alone is NOT proof a UI works.
---

# browser-test

The train loop's **verify step for anything visual**. A schema-valid n8n Form or a rendered dashboard
can still be broken on screen — so any web/UI artifact must be *driven in a real browser* (fill →
submit → assert), not just validated. This is the same lesson as the blank-page dashboard bug.

It uses the **Playwright CLI library via Bash, NOT the Playwright MCP server** — deliberate: the CLI
path is ~27k tokens/run vs ~114k for MCP, and once the loop runs on a metered key that gap is real money.

## When to use
- Golden case **03** (n8n Form → UI intake): load the form, fill, submit, assert the confirmation page
  AND that the Notion row was created.
- Any dashboard / web artifact the loop builds or hardens (assert the canvas/app actually drew).
- Visual regression: screenshot now, compare to a baseline (`toHaveScreenshot` / pixelmatch) later.

## How to run
Write a spec JSON, then:
```bash
node tools/paperclip/train/browser_test.mjs spec.json        # or:  ... browser_test.mjs -   (stdin)
SHOT_DIR=/tmp/run-<id> node tools/paperclip/train/browser_test.mjs spec.json
```
It prints ONE JSON verdict and exits 0 (all steps ok + no page errors) or 1 (any failure/timeout).
Read `result.ok`, the per-step `error`s, and `result.screenshots`.

### Spec format
```json
{
  "url": "https://…",
  "headers": { "Authorization": "Bearer …" },
  "viewport": { "width": 1280, "height": 800 },
  "hardTimeoutMs": 90000,
  "steps": [
    { "action": "fill", "selector": "#firma", "value": "Muster Treuhand AG" },
    { "action": "click", "selector": "button[type=submit]" },
    { "action": "waitFor", "selector": ".confirmation", "timeoutMs": 10000 },
    { "action": "assertText", "selector": ".confirmation", "contains": "Danke" },
    { "action": "assertVisible", "selector": "#done" },
    { "action": "assertCanvasDrew", "selector": "canvas#stage" },
    { "action": "screenshot", "name": "after_submit" },
    { "action": "assertNoPageErrors" }
  ]
}
```
`goto(url)` is implicit. Actions: `fill` · `click` · `wait{ms}` · `waitFor{selector,timeoutMs}` ·
`assertVisible{selector}` · `assertText{selector,contains}` · `assertCanvasDrew{selector?}` ·
`assertNoPageErrors` · `screenshot{name?}`.

## Two visual gates
1. **Deterministic** (this runner): explicit assertions → a hard pass/fail the loop's Validator trusts.
2. **Semantic** (optional): feed a returned screenshot back to Claude as an image block and ask "does
   this match the acceptance criteria?". **Grayscale-judge rule:** the operator's phone is permanent
   B&W — never judge correctness by colour alone; require state to be encoded in shape/text/position.

## Guardrails (15GB VPS)
Built in: headless, `--no-sandbox`, `--disable-dev-shm-usage`, software-GL (WebGL renders headless), a
hard run-timeout, and **always-close in `finally`** (no zombie chromium). Keep **concurrency ≤ 2**
browser runs at the orchestrator level. For containers add `--init`/tini to reap chromium.

## Install (once, on the VPS where the loop runs)
```bash
npx playwright install --only-shell chromium   # headless-shell, no Xvfb, smaller footprint
```
Off-box (e.g. testing from this repo) point at an existing install:
`PLAYWRIGHT_PKG=/abs/node_modules/playwright/index.js node browser_test.mjs spec.json`.

## ⛔ Prime directive
Browser-testing is read-only against the artifact's own test/sandbox surface. **Never** point it at a
real customer's live system, and never let a tested form write to a live production DB — pin-data /
sandbox only. (See `references/golden/README.md`.)
