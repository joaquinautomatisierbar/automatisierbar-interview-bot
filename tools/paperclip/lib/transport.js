// transport.js — shared config + dual-mode (direct / SSH) access to the paperclip API.
//
// On the VPS: hits http://127.0.0.1:3100 directly (local_trusted, no auth).
// From the MacBook: tunnels each call through `ssh paperclip@host curl localhost:3100/...`.
// Every pipeline tool (status, preflight, canary, orchestrator helpers) builds on this.

const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const CFG = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "pipeline.config.json"), "utf8"));
const KEY = CFG.host.sshKey.replace(/^~/, process.env.HOME || "");
const SSH_BASE = ["-i", KEY, "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", `${CFG.host.sshUser}@${CFG.host.ip}`];

let MODE = null; // "direct" | "ssh"

async function probe() {
  try {
    const r = await fetch(`${CFG.api.internal}${CFG.api.healthPath}`, { signal: AbortSignal.timeout(4000) });
    if (r.ok) { MODE = "direct"; return MODE; }
  } catch {}
  MODE = "ssh";
  return MODE;
}
const mode = () => MODE;

async function ensureProbed() { if (!MODE) await probe(); }

// GET
async function api(p) {
  await ensureProbed();
  if (MODE === "direct") {
    const r = await fetch(`${CFG.api.internal}${p}`, { signal: AbortSignal.timeout(20000) });
    if (!r.ok) throw new Error(`GET ${p} -> ${r.status}`);
    return r.json();
  }
  const out = execFileSync("ssh", [...SSH_BASE, `curl -s -m 20 'http://127.0.0.1:3100${p}'`], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  return JSON.parse(out);
}

// POST / PATCH — body passed via stdin (avoids shell-quoting JSON over SSH)
async function send(method, p, body) {
  await ensureProbed();
  const payload = JSON.stringify(body ?? {});
  if (MODE === "direct") {
    const r = await fetch(`${CFG.api.internal}${p}`, {
      method, headers: { "Content-Type": "application/json" }, body: payload, signal: AbortSignal.timeout(20000),
    });
    const txt = await r.text();
    if (!r.ok) throw new Error(`${method} ${p} -> ${r.status}: ${txt.slice(0, 300)}`);
    return txt ? JSON.parse(txt) : {};
  }
  const cmd = `curl -s -m 20 -X ${method} -H 'Content-Type: application/json' --data-binary @- 'http://127.0.0.1:3100${p}'`;
  const out = execFileSync("ssh", [...SSH_BASE, cmd], { input: payload, encoding: "utf8", maxBuffer: 16 * 1024 * 1024 });
  return out ? JSON.parse(out) : {};
}
const apiPost = (p, body) => send("POST", p, body);
const apiPatch = (p, body) => send("PATCH", p, body);

// arbitrary shell on the VPS (systemctl, journalctl, …). Always SSH.
function sshExec(cmd) {
  try { return execFileSync("ssh", [...SSH_BASE, cmd], { encoding: "utf8" }).trim(); }
  catch (e) { return `__ERR__ ${e.message}`; }
}

const arr = (d, ...keys) => (Array.isArray(d) ? d : keys.map((k) => d?.[k]).find(Array.isArray) || []);

// resolve agents live, keyed by stable urlKey (drift-proof)
async function agentsByUrlKey() {
  const list = arr(await api(`/api/companies/${CFG.company.id}/agents`), "agents");
  const byUrlKey = {}, byId = {};
  for (const a of list) { byUrlKey[a.urlKey] = a; byId[a.id] = a; }
  return { list, byUrlKey, byId };
}

module.exports = { CFG, probe, mode, api, apiPost, apiPatch, sshExec, arr, agentsByUrlKey };
