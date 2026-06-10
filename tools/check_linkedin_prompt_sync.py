#!/usr/bin/env python3
"""Drift guard for the LinkedIn voice prompt.

prompts/linkedin_voice.md is the CANONICAL source of the LinkedIn comment voice.
Two consumers embed/use it:
  1. tools/linkedin_comment_gen.py  — loads the .md directly (always in sync).
  2. workflows/linkedin_engagement_bot.n8n.json — embeds a *copy* in the
     "Build Anthropic Payload" Code node (VOICE_PROMPT_LINES). n8n cloud can't
     read the repo file, so this copy is hand-synced and can silently drift.

This script compares the embedded copy against the canonical .md after
normalizing away cosmetic differences (the embedded copy strips markdown
emphasis and the .md's meta-frontmatter). It reports any *content* divergence.

Usage:
  python3 tools/check_linkedin_prompt_sync.py        # exit 0 = in sync, 1 = drift
  python3 tools/check_linkedin_prompt_sync.py -v     # also print the diff

Wire it into pre-commit / CI to fail loudly when the prompt changes in one
place but not the other. (See decisions/log.md 2026-05-02.)
"""
import json
import re
import sys
import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "prompts" / "linkedin_voice.md"
BOT = ROOT / "workflows" / "linkedin_engagement_bot.n8n.json"
NODE_NAME = "Build Anthropic Payload"


def extract_embedded() -> list[str]:
    """Pull the VOICE_PROMPT_LINES string array out of the n8n Code node."""
    data = json.loads(BOT.read_text(encoding="utf-8"))
    node = next((n for n in data.get("nodes", []) if n.get("name") == NODE_NAME), None)
    if node is None:
        raise SystemExit(f"ERROR: node '{NODE_NAME}' not found in {BOT.name}")
    code = node.get("parameters", {}).get("jsCode") or node.get("parameters", {}).get("functionCode") or ""
    m = re.search(r"VOICE_PROMPT_LINES\s*=\s*\[(.*?)\]\s*;", code, re.S)
    if not m:
        raise SystemExit("ERROR: VOICE_PROMPT_LINES array not found in node code")
    # JS string literals — the array mixes single- AND double-quoted strings
    # (double quotes are used for lines containing an apostrophe). Honor escapes.
    pat = re.compile(r"'((?:\\.|[^'\\])*)'|\"((?:\\.|[^\"\\])*)\"")
    out = []
    for mm in pat.finditer(m.group(1)):
        s = mm.group(1) if mm.group(1) is not None else mm.group(2)
        s = (s.replace("\\\\", "\\").replace("\\'", "'").replace('\\"', '"')
             .replace("\\n", "\n").replace("\\t", "\t"))
        out.extend(s.split("\n"))
    return out


def load_md() -> list[str]:
    # The n8n bot embeds the .md verbatim (matching how linkedin_comment_gen.py
    # loads it — read_text() on the whole file), so compare whole-to-whole.
    return MD.read_text(encoding="utf-8").splitlines()


_EMPH = re.compile(r"[*`_]+")


def normalize(lines: list[str]) -> list[str]:
    """Drop blanks; strip markdown emphasis + backticks; collapse whitespace."""
    out = []
    for l in lines:
        s = _EMPH.sub("", l)
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            out.append(s)
    return out


def main() -> int:
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    md = normalize(load_md())
    emb = normalize(extract_embedded())
    if md == emb:
        print(f"✓ LinkedIn prompt in sync ({len(md)} content lines): "
              f"{MD.relative_to(ROOT)} == n8n '{NODE_NAME}' node")
        return 0
    print(f"⚠ DRIFT: prompts/linkedin_voice.md and the n8n embedded copy differ "
          f"(canonical={len(md)} lines, embedded={len(emb)} lines).")
    diff = list(difflib.unified_diff(emb, md, fromfile="n8n embedded copy",
                                     tofile="prompts/linkedin_voice.md (canonical)", lineterm=""))
    changed = [d for d in diff if d and d[0] in "+-" and not d.startswith(("+++", "---"))]
    print(f"  {len(changed)} differing content lines. "
          f"Re-sync the n8n Code node from the .md, then re-import the workflow.")
    if verbose:
        print("\n".join(diff[:120]))
    else:
        print("  (run with -v to see the full diff)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
