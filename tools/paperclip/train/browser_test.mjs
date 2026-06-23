#!/usr/bin/env node
// browser_test.mjs — headless Playwright runner for the train loop's verify step (+ golden case 03).
//
// Drives a real browser via the Playwright CLI lib (NOT the MCP server — ~27k vs ~114k tokens, and we
// pay real API money once metered). Reads a JSON spec, walks the acceptance steps, screenshots, and
// prints a single JSON verdict. The QA/engine agent reads that verdict; the screenshots can be fed back
// to Claude as image blocks for a semantic "is this right?" judgment (grayscale-safe — see the SKILL).
//
// Usage:
//   node browser_test.mjs spec.json            # or:  node browser_test.mjs -   (spec on stdin)
//   PLAYWRIGHT_PKG=/abs/node_modules/playwright/index.js node browser_test.mjs spec.json   # off-box test
//   SHOT_DIR=/tmp/run123 node browser_test.mjs spec.json
//
// Spec: { url, headers?, viewport?, hardTimeoutMs?, steps: [ {action, ...} ] }
//   goto is implicit (the url). Actions:
//     fill {selector, value} · click {selector} · wait {ms} · waitFor {selector, timeoutMs}
//     assertVisible {selector} · assertText {selector, contains} · assertCanvasDrew {selector?}
//     assertNoPageErrors · screenshot {name?}
// Exit 0 = all steps ok + no page errors; 1 = any failure/timeout. Browser always closed (finally).
import { readFileSync } from 'fs';

const pwPkg = process.env.PLAYWRIGHT_PKG || 'playwright';
const _pw = await import(pwPkg);
const chromium = _pw.chromium || (_pw.default && _pw.default.chromium);

function readSpec() {
  const arg = process.argv[2];
  const raw = (arg && arg !== '-') ? readFileSync(arg, 'utf8') : readFileSync(0, 'utf8');
  return JSON.parse(raw);
}

const spec = readSpec();
const SHOT_DIR = process.env.SHOT_DIR || '/tmp';
// 15GB-VPS guardrails: no sandbox, no /dev/shm reliance, software-GL so WebGL pages render headless.
const ARGS = ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
              '--enable-unsafe-swiftshader', '--use-gl=angle'];
const result = { ok: true, url: spec.url, steps: [], errors: [], screenshots: [] };

let browser;
const hardTimeout = setTimeout(() => {
  result.ok = false; result.errors.push('hard timeout');
  console.log(JSON.stringify(result, null, 2));
  process.exit(1);
}, spec.hardTimeoutMs || 90000);

try {
  browser = await chromium.launch({ args: ARGS });
  const page = await browser.newPage({
    viewport: spec.viewport || { width: 1280, height: 800 },
    extraHTTPHeaders: spec.headers || {},
  });
  page.on('pageerror', e => result.errors.push('pageerror: ' + String(e)));
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) result.errors.push('console: ' + m.text()); });

  await page.goto(spec.url, { waitUntil: 'load', timeout: 30000 });

  for (const step of (spec.steps || [])) {
    const s = { action: step.action };
    try {
      if (step.action === 'fill') await page.fill(step.selector, step.value);
      else if (step.action === 'click') await page.click(step.selector);
      else if (step.action === 'wait') await page.waitForTimeout(step.ms || 500);
      else if (step.action === 'waitFor') await page.waitForSelector(step.selector, { timeout: step.timeoutMs || 10000 });
      else if (step.action === 'assertVisible') {
        const ok = await page.evaluate(sel => { const e = document.querySelector(sel); if (!e) return false; const b = e.getBoundingClientRect(); return b.width > 0 && b.height > 0; }, step.selector);
        if (!ok) throw new Error('not visible: ' + step.selector);
      } else if (step.action === 'assertText') {
        const t = await page.textContent(step.selector);
        if (!t || !t.includes(step.contains)) throw new Error('text "' + step.contains + '" not in ' + step.selector);
      } else if (step.action === 'assertCanvasDrew') {
        const sel = step.selector || 'canvas';
        const ok = await page.evaluate(s => { const c = document.querySelector(s); if (!c) return false; const b = c.getBoundingClientRect(); const gl = c.getContext('webgl2') || c.getContext('webgl'); return b.width > 100 && b.height > 100 && !!gl; }, sel);
        if (!ok) throw new Error('canvas did not draw: ' + sel);
      } else if (step.action === 'assertNoPageErrors') {
        if (result.errors.length) throw new Error('page errors: ' + result.errors.slice(0, 3).join(' | '));
      } else if (step.action === 'screenshot') {
        const p = `${SHOT_DIR}/bt_${step.name || result.screenshots.length}.png`;
        await page.screenshot({ path: p });
        result.screenshots.push(p); s.path = p;
      } else throw new Error('unknown action: ' + step.action);
      s.ok = true;
    } catch (e) { s.ok = false; s.error = String(e.message || e); result.ok = false; }
    result.steps.push(s);
  }
} catch (e) {
  result.ok = false; result.errors.push('fatal: ' + String(e.message || e));
} finally {
  if (browser) await browser.close().catch(() => {});
  clearTimeout(hardTimeout);
}

console.log(JSON.stringify(result, null, 2));
process.exit(result.ok ? 0 : 1);
