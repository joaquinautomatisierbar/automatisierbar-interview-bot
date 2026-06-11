---
name: playwright-browser-test
description: >
  Drive a real Chromium browser via Playwright to test customer-facing UI, forms,
  and end-user-visible workflow outputs. Use when the artifact under test has a
  human-touched surface — webhook responses rendered in a UI, n8n form triggers,
  customer dashboards, email-to-Slack flows where the human's view of the result
  matters. Skip for pure backend artifacts where MCP validate_workflow + pin-data
  testing covers everything.
---

# Playwright Browser Test

QA Engineer's tool for real-browser verification. Pin-data tests via the n8n
MCP catch *structural* and *node-level* failures. They miss things like:

- "The Slack message arrives but the body's markdown rendering is broken on mobile."
- "The webhook returns 200 but the customer-facing thank-you page shows a CORS error."
- "The form-trigger workflow accepts input but the success state UI never appears."
- "The email goes out but the customer's email client clips the from-name."

Playwright lets you drive Chromium to *observe what the human will see*.

## Pre-requisites (one-time setup)

Playwright is NOT auto-installed in the agent's environment. On first use:

```bash
# Install Playwright Chromium globally (one-time, ~150MB)
npx playwright install chromium

# Verify
npx playwright --version
```

The bundled Chromium lives at `~/Library/Caches/ms-playwright/`. After this,
the QA Engineer agent can spawn browser instances via Node + Playwright in
its workspace.

## When to invoke (HARD vs. judgment)

**Hard-required (no judgment, skipping = TEST_FAIL):**

| Artifact surface | Required |
|---|---|
| Modifies `static/**`, `*.html`, files with `<form>` / `<script>` | ✅ MANDATORY |
| n8n Form Trigger nodes | ✅ MANDATORY |
| Flask / FastAPI / Express route returning rendered HTML (not JSON) | ✅ MANDATORY |
| Render / Vercel / Netlify published pages | ✅ MANDATORY |

**Judgment call:**

| Artifact surface | Test approach |
|---|---|
| Pure webhook → server-side integration (no UI) | MCP only (validate_workflow + test_workflow with pin data) |
| Email / Slack / Telegram outbound with rich rendering | MCP first; **Playwright recommended** for HTML email, Markdown formatting, attachments |
| API consumed by another automation (not a human) | MCP only |

Default for the judgment-call rows to MCP-only. Default for the hard-required rows is non-negotiable.

## Screenshot ritual (HARD requirement on TEST_PASS for UI builds)

For every UI-bearing TEST_PASS, capture **two viewports minimum**:

```javascript
// Desktop
await page.setViewportSize({ width: 1280, height: 800 });
await page.screenshot({ path: 'browser-tests/desktop-golden.png', fullPage: true });

// Mobile
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({ path: 'browser-tests/mobile-golden.png', fullPage: true });
```

Both screenshots get attached to your TEST_PASS handoff comment. If either is missing, the QA Engineer's AGENTS.md hard-gate says you fail your own check.

For Phase 9+ (when the Presentation Designer agent exists), screenshots ALSO get attached to the `PRESENTATION.md` so customers see visual proof.

## How to use

Write a short test script in the agent's workspace, run it, capture results.

```bash
# In the agent workspace
mkdir -p browser-tests
cat > browser-tests/test-golden-path.mjs <<'EOF'
import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

// 1. Trigger the workflow (curl or whatever the customer flow is)
await fetch('https://hook.example.com/trigger', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ test: 'golden-path-input' }),
});

// 2. Wait for the side effect to land in the observable surface
//    (e.g. open the Slack web client, navigate to the channel, find the message)
await page.goto('https://app.slack.com/client/T.../C...');
// ... login flow (skip if test channel is public or use cookies via setup-browser-cookies)
await page.waitForSelector('[data-qa="message_text"]:has-text("Dringend")');

// 3. Capture evidence
await page.screenshot({ path: 'browser-tests/golden-path-result.png', fullPage: true });

// 4. Assertions
const messageText = await page.locator('[data-qa="message_text"]').first().textContent();
console.log(JSON.stringify({
  ok: messageText.includes('Dringend'),
  observed: messageText,
}));

await browser.close();
EOF

node browser-tests/test-golden-path.mjs
```

Run it. Capture stdout (the JSON line). Attach the screenshot to your
`TEST_PASS` / `TEST_FAIL` comment.

## Reporting format

Per scenario, include:

- **Test name** (golden path / edge / failure mode)
- **Steps run** (curl → wait → assert)
- **Expected** (what the brief says should happen)
- **Observed** (what the screenshot + stdout show)
- **Pass/fail per assertion**
- **Screenshot reference** (relative path in workspace)

Example `TEST_PASS` body excerpt:

> Golden-path Slack rendering check: ✅
> - Trigger: webhook with `subject="Dringend - Test"`
> - Observed in #client-priority: "🚨 Dringend von …" with bold formatting + Gmail link preview
> - Screenshot: `browser-tests/golden-path-result.png` — shows the rendered Slack message correctly
> - Markdown parsing: bold + link both render correctly on mobile (verified via mobile viewport `await page.setViewportSize({width: 375, height: 812})`)

Example `TEST_FAIL` body excerpt:

> Golden-path: ❌ Slack message body shows literal `**` instead of bold
> - Cause: `parse_mode: "Markdown"` is set but the message uses `**` (Markdown V2 syntax). Slack expects `*single-asterisk*` for the legacy mode.
> - Fix: either drop `parse_mode` (Slack auto-parses *bold*) or switch to `parse_mode: "MarkdownV2"` (and escape special chars).
> - Screenshot: `browser-tests/golden-path-result.png`

## Safety + cost

- **Always headless.** Don't open a windowed browser on the host machine.
- **Use test channels and test accounts.** Don't drive Playwright against
  production Slack workspaces, real customer email inboxes, etc. — use the
  dedicated Automatisierbar test workspace + dedicated test channels.
- **Capture screenshots, not full HTML dumps.** Screenshots are small; full
  page HTML can be 5+ MB and bloat the issue.
- **Limit retries.** If a Playwright test fails to even start (no Chromium
  installed, network error to the target), report `TEST_FAIL: environment`
  and stop — don't burn 10 min retrying.

## Phase note

This skill is the *Phase 4 outcome* of the original build plan. It replaces
the "build a custom paperclip Playwright adapter" approach which would have
been weeks of plugin SDK work for the same end result.
