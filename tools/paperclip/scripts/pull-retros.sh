#!/usr/bin/env bash
# pull-retros.sh — materialize RETRO: comments posted by paperclip Release
# Engineer into local files under references/retros/ + append carry-forward
# learnings to references/learnings/ scope files.
#
# Operator-side. Run from project root on MacBook. Requires paperclip API
# reachable at http://127.0.0.1:3100 (SSH tunnel or local instance).
#
# Idempotent — only writes retros that don't already exist as files. Does
# NOT commit; operator reviews `git diff references/` and commits manually.
#
# Usage:
#   bash tools/paperclip/scripts/pull-retros.sh                 # last 30 days
#   bash tools/paperclip/scripts/pull-retros.sh --days 90       # custom window

set -euo pipefail

DAYS="${DAYS:-30}"
if [[ "${1:-}" == "--days" ]]; then
  DAYS="${2:?}"
  shift 2
fi

PROJECT_ROOT="${PROJECT_ROOT:-/Users/sexyjoaquin/Desktop/Claude Code/n8n Workflow Interview}"
COMPANY_ID="${COMPANY_ID:-47196d38-2f19-4168-af8f-fe9451dff910}"
API="${PAPERCLIP_API:-http://127.0.0.1:3100}"

cd "${PROJECT_ROOT}"

python3 - <<PY
import json, os, re, sys, urllib.request, datetime
from pathlib import Path

API = "${API}"
COMPANY = "${COMPANY_ID}"
DAYS = int("${DAYS}")
ROOT = Path("${PROJECT_ROOT}")
RETROS_DIR = ROOT / "references" / "retros"
LEARNINGS_DIR = ROOT / "references" / "learnings"

def fetch(path):
    req = urllib.request.Request(f"{API}{path}", headers={"User-Agent": "pull-retros"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# ---- 1. Pull all issues + filter to recent shipped ----
print(f"[pull-retros] fetching issues from {API}/api/companies/{COMPANY}/issues …", file=sys.stderr)
issues_resp = fetch(f"/api/companies/{COMPANY}/issues")
issues = issues_resp if isinstance(issues_resp, list) else issues_resp.get("issues", [])
cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=DAYS)).isoformat()
recent = [i for i in issues if (i.get("updatedAt") or "") >= cutoff and i.get("status") in ("done", "in_review")]
print(f"[pull-retros] {len(recent)} recent terminal issues (last {DAYS} days)", file=sys.stderr)

# ---- 2. Resolve agent urlKeys ----
agents = fetch(f"/api/companies/{COMPANY}/agents")
agents = agents if isinstance(agents, list) else agents.get("agents", [])
by_id = {a["id"]: a for a in agents}

# ---- 3. For each issue, scan comments for RETRO: marker ----
RETRO_RE = re.compile(r"^RETRO:\s*([\w\-]+)\s*$", re.MULTILINE)
DELTA_RE = re.compile(r"^RETRO-DELTA:\s*([\w\-]+)\s*$", re.MULTILINE)

new_retros = []
deltas = []
for issue in recent:
    try:
        comments = fetch(f"/api/issues/{issue['id']}/comments")
    except Exception as e:
        print(f"  WARN: failed to fetch comments for {issue.get('identifier')}: {e}", file=sys.stderr)
        continue
    for c in comments:
        body = c.get("body") or ""
        m = RETRO_RE.search(body)
        if m:
            slug = m.group(1)
            target = RETROS_DIR / f"{slug}.md"
            if target.exists():
                continue   # already pulled
            # The body has RETRO: header on first line; the rest is the file content
            file_content = body.split("\n", 1)[1].lstrip() if "\n" in body else ""
            new_retros.append({
                "slug": slug,
                "issue": issue.get("identifier"),
                "issue_id": issue["id"],
                "shipped_at": c.get("createdAt", "")[:10],
                "content": file_content,
            })
        md = DELTA_RE.search(body)
        if md:
            deltas.append({
                "slug": md.group(1),
                "issue": issue.get("identifier"),
                "content_appendix": body,
            })

print(f"[pull-retros] {len(new_retros)} new retros, {len(deltas)} deltas to apply", file=sys.stderr)
if not new_retros and not deltas:
    print("[pull-retros] nothing to pull — exiting.", file=sys.stderr)
    sys.exit(0)

# ---- 4. Write retro files + parse carry-forward learnings ----
LEARNING_HEADING = re.compile(r"^## Carry-forward learnings\s*$", re.MULTILINE)
LEARNING_ENTRY = re.compile(
    r"### \d+\.\s*(?P<title>.+?)\n+(?P<body>.+?)(?=^###\s|\Z)",
    re.MULTILINE | re.DOTALL,
)
SCOPE_RE = re.compile(r"\*\*Scope:\*\*\s*(?P<scope>[\w\-:]+)", re.IGNORECASE)
RULE_RE = re.compile(r"\*\*Rule:\*\*\s*(?P<rule>.+?)$", re.MULTILINE | re.IGNORECASE)

RETROS_DIR.mkdir(parents=True, exist_ok=True)

def scope_to_path(scope: str) -> Path:
    """Map scope string to learning file."""
    if scope == "global":
        return LEARNINGS_DIR / "global.md"
    if scope.startswith("operator-feedback") or scope == "role:operator":
        return LEARNINGS_DIR / "operator-feedback.md"
    if scope.startswith("role:"):
        role = scope.split(":", 1)[1].strip()
        return LEARNINGS_DIR / "by-role" / f"{role}.md"
    return LEARNINGS_DIR / "global.md"  # fallback

learnings_appended = []
for retro in new_retros:
    target = RETROS_DIR / f"{retro['slug']}.md"
    target.write_text(retro["content"])
    print(f"  wrote {target.relative_to(ROOT)}", file=sys.stderr)

    # Parse carry-forward learnings from the retro
    m = LEARNING_HEADING.search(retro["content"])
    if not m:
        continue
    after = retro["content"][m.end():]
    # Stop at next H2 if present
    next_h2 = re.search(r"^##\s", after, re.MULTILINE)
    if next_h2:
        after = after[:next_h2.start()]

    for entry in LEARNING_ENTRY.finditer(after):
        title = entry.group("title").strip()
        body = entry.group("body").strip()
        scope_match = SCOPE_RE.search(body)
        scope = scope_match.group("scope") if scope_match else "global"
        rule_match = RULE_RE.search(body)
        rule = rule_match.group("rule").strip() if rule_match else title
        slug = re.sub(r"[^a-z0-9-]+", "-", title.lower()).strip("-")[:60]

        path = scope_to_path(scope)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(f"# Learnings — {path.stem}\n\n")
        existing = path.read_text()
        if f"name: {slug}" in existing:
            continue   # already there

        block = f"""
## {slug}

---
name: {slug}
description: {rule[:140]}
type: learning
scope: {scope}
created: {retro['shipped_at']}
issue: {retro['issue']}
tags: []
---

{body}

(Carried forward from [retro {retro['issue']}](../retros/{retro['slug']}.md))
"""
        with open(path, "a") as f:
            f.write(block)
        learnings_appended.append((slug, str(path.relative_to(ROOT))))
        print(f"    appended learning '{slug}' to {path.relative_to(ROOT)}", file=sys.stderr)

# ---- 5. Apply DELTA appendices to existing retro files ----
for d in deltas:
    target = RETROS_DIR / f"{d['slug']}.md"
    if not target.exists():
        print(f"  WARN: delta for {d['slug']} but no base retro file exists", file=sys.stderr)
        continue
    with open(target, "a") as f:
        f.write(f"\n\n---\n## Delta — {d['issue']}\n\n{d['content_appendix']}\n")
    print(f"  appended delta to {target.relative_to(ROOT)}", file=sys.stderr)

# ---- 6. Update retros/INDEX.md ----
index_path = RETROS_DIR / "INDEX.md"
if index_path.exists() and new_retros:
    idx_text = index_path.read_text()
    insertion = "\n## Recent retros (sorted by `shipped_at` desc)\n"
    if insertion in idx_text:
        new_lines = "\n".join(
            f"- [{r['issue']} {r['slug']}]({r['slug']}.md) — shipped {r['shipped_at']}"
            for r in new_retros
        )
        idx_text = idx_text.replace(
            insertion,
            insertion + "\n" + new_lines + "\n",
            1,
        )
        index_path.write_text(idx_text)
        print(f"  updated {index_path.relative_to(ROOT)}", file=sys.stderr)

print("", file=sys.stderr)
print(f"[pull-retros] DONE. {len(new_retros)} new retro file(s) + {len(learnings_appended)} learnings appended.", file=sys.stderr)
print("[pull-retros] Review with: git diff references/", file=sys.stderr)
print("[pull-retros] Commit + push when ready, then run: bash tools/paperclip/scripts/sync-context.sh --push-to-vps", file=sys.stderr)
PY
