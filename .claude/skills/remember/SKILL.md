---
name: remember
description: Use when the operator types `/remember <text>` or asks to "save a learning", "remember this", "don't forget", or "save to memory". Writes the entry to operator-side auto-memory (Claude Code session continuity) AND, if paperclip-relevant, mirrors it to `references/learnings/operator-feedback.md` so production agents see it on their next run. Dual-write, not symlinked — the two files are kept in sync by this skill.
---

## What this skill does

The operator has two memory surfaces:

1. **Claude Code auto-memory** at `~/.claude/projects/-Users-sexyjoaquin-Desktop-Claude-Code-n8n-Workflow-Interview/memory/` — session continuity. Loaded automatically into THIS Claude Code session at start, and accessible to any future `claude` session in this project root.
2. **Paperclip-visible mirror** at `references/learnings/operator-feedback.md` — synced to the VPS via `tools/paperclip/scripts/sync-context.sh --push-to-vps`. Loaded by every paperclip agent at activation via the `recall-learnings` skill.

Until this skill existed, only #1 was easy to write. The operator could correct an agent's behavior in this Claude Code session — that correction lived in #1, **invisible to paperclip**. Next time a paperclip agent did the same Issue, it re-made the same mistake because it never saw the correction.

`/remember` writes to both places at once when the entry is paperclip-relevant. Same content in both files; the locations differ purely to keep the operator-Claude-Code session continuity (#1) separate from the production agent mount (#2).

## When the operator triggers this skill

Trigger patterns:
- `/remember <text>` — explicit invocation
- `/remember --paperclip-only <text>` — skip #1, write only to #2 (for entries that don't need to participate in Claude Code session memory)
- *"remember that …"*, *"save this learning"*, *"don't forget …"*, *"add to memory"* — implicit invocation; classify intent and proceed

## Execution

### Step 1 — Classify the entry

Read the operator's text and classify on two axes:

**Axis A: Type**
- `feedback` — an operator correction or preference ("don't do X", "always use Y instead")
- `project` — current state of an ongoing initiative ("Phase 2 of the call pipeline is now …")
- `reference` — durable fact about an external system ("Notion Lead-DB id is abc-123")
- `learning` — operational lesson from a past mistake or surprise

**Axis B: Scope (paperclip-relevance)**
- `paperclip-visible` — operational guidance that future agent runs should respect (most `feedback` and `learning` entries). Mirror to #2.
- `operator-only` — Claude Code session continuity that doesn't matter to paperclip agents (e.g. a session-specific TODO, a transient project state). Skip #2.

If ambiguous: ask the operator one classifying question. Default to `paperclip-visible` when uncertain — over-sharing to paperclip costs ~5 lines of recall context per agent run; under-sharing costs a repeat mistake.

### Step 2 — Generate a stable slug

Convert the entry's key idea into a short kebab-case slug, max 50 chars. Examples:
- "Don't use the dedicated Anthropic node" → `no-dedicated-anthropic-node`
- "ICP excludes Coiffeur, Restaurant" → `lead-icp-backoffice-only`
- "Validator warnings on credentials are usually false positives" → `n8n-validator-cred-warnings`

If a slug for this learning already exists in MEMORY.md, ask the operator: *"This looks similar to an existing entry — update that one (recommended) or create a new one?"*

### Step 3 — Write to Claude Code auto-memory (#1)

Write file at `~/.claude/projects/-Users-sexyjoaquin-Desktop-Claude-Code-n8n-Workflow-Interview/memory/<type>_<slug>.md` with frontmatter:

```yaml
---
name: <slug>
description: <one-line summary>
metadata:
  node_type: memory
  type: <feedback | project | reference | learning>
  originSessionId: <current Claude Code session ID if known, else omit>
---

<body — see Step 5 for the canonical body shape>
```

Then add an index line to `MEMORY.md` at the top of the appropriate section:

```markdown
- [<Title>](<filename>) — <one-line description>
```

### Step 4 — If paperclip-visible, also write to the mirror (#2)

Append a section to `references/learnings/operator-feedback.md` with the SAME body content but slightly different frontmatter (no `originSessionId`, adds `scope` field):

```markdown

## <slug>

---
name: <slug>
description: <one-line summary — same as #1>
type: learning
scope: global    # or role:<role> if it only applies to one paperclip agent role
created: YYYY-MM-DD    # today
issue: —    # only set if this learning came from a specific Issue
tags: [tag1, tag2, …]
---

<body — same as #1>
```

If the entry is role-specific, write to `references/learnings/by-role/<role>.md` instead. Same shape.

### Step 5 — Canonical body shape

For `feedback` and `learning` entries, body MUST follow this shape:

```markdown
<one-sentence statement of the rule or fact>

**Why:** <the operator's reason — quote them if available, cite the incident/date that prompted this>

**How to apply:** <when does this kick in on future work — concrete trigger>
```

For `project` and `reference` entries, body is freeform but should be terse — 5-15 lines max. Long entries decay fast; short entries stick.

### Step 6 — Remind operator to push

After writing, output:

```
Saved to memory:
  ✓ ~/.claude/projects/.../memory/<slug>.md  (Claude Code session memory)
  ✓ references/learnings/operator-feedback.md  (paperclip mirror)

To propagate to paperclip agents (VPS mount):
  bash tools/paperclip/scripts/sync-context.sh --push-to-vps

Don't auto-trigger — let the operator batch syncs.
```

If `--paperclip-only` was used or the entry was classified `operator-only`, adjust the output to show only the file(s) actually written.

## Hard rules

1. **Don't write entries you weren't asked to write.** This skill only fires on explicit `/remember` invocation or unambiguous natural-language equivalents ("remember that…"). Do NOT auto-write learnings from session activity.
2. **Don't auto-trigger `sync-context.sh`.** Operator decides when to push (it crosses to the VPS and the operator may want to batch multiple memory writes first).
3. **Don't overwrite existing entries silently.** If a slug already exists, ask: update or create new with `-v2` suffix.
4. **Don't write paperclip-irrelevant entries to #2.** Examples that should stay operator-only: "remember to text Tej about Thursday", "Joaquin's family doctor is X", session-scope TODOs.
5. **Don't write secrets to either file.** If the operator says "remember my Notion API key is sk-…", refuse + redirect to `/etc/paperclip/secrets`.
6. **Cite the conversation if possible.** Quote the operator's words verbatim in the **Why** line — preserves the exact framing for future agents (they can't ask follow-up questions).

## Verification (cold-test cases)

- **Paperclip-relevant feedback:** `/remember Don't use the dedicated n8n Anthropic node — use HTTP Request with Header Auth.` Expected: writes to both #1 and #2 with `feedback`/`learning` type and `global` scope.
- **Role-specific feedback:** `/remember The Copy Writer should never use hashtags in comment-style posts.` Expected: writes to #1 + `references/learnings/by-role/copy-writer.md`.
- **Operator-only entry:** `/remember Joaquin's flight to Berlin is 2026-06-15.` Expected: writes to #1 only. Suggests not paperclip-relevant; confirms with operator if uncertain.
- **Duplicate detection:** `/remember Coiffeur/Restaurant are NOT ICP, exclude from scraping.` (already exists). Expected: detect via slug fuzz match → ask update-or-new.
- **Secret refusal:** `/remember The new Anthropic key is sk-ant-….` Expected: refuse with redirect to `/etc/paperclip/secrets`.
