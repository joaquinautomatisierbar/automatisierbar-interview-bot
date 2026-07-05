#!/usr/bin/env python3
"""final_script_cache.py — resolve the walk-in Follow-Up Email Script (Final Script template +
Branchenspezifische Pitch-Bibliothek).

Notion is the single source of truth (page 388bebb0c2f98088991deea070765a37). This mirrors
infomaniak_signature.get_signature()'s live -> cache -> committed-fallback shape so the headless
walk-in draft worker always has grounding copy, even during a Notion outage. The
/walkinmail-improvement skill keeps the committed fallback in sync with Notion.
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_SCRIPT_DIR))  # put tools/ on the path for notion_session
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, os.pardir, os.pardir))

FINAL_SCRIPT_PAGE_ID = "388bebb0c2f98088991deea070765a37"
CACHE_PATH = os.path.join(_SCRIPT_DIR, "final_script_cache.txt")
FALLBACK_PATH = os.path.join(_SCRIPT_DIR, "final_script_fallback.md")


def _ensure_notion_key():
    """notion_session reads only os.environ. On the VPS the cron sources /etc/cockpit/env; for
    local runs (and the improvement skill) fill NOTION_API_KEY from the repo-root .env once."""
    if os.environ.get("NOTION_API_KEY"):
        return
    try:
        with open(os.path.join(_REPO_ROOT, ".env")) as fh:
            for ln in fh:
                s = ln.strip()
                if s.startswith("NOTION_API_KEY"):
                    os.environ["NOTION_API_KEY"] = s.split("=", 1)[1].strip()
                    break
    except FileNotFoundError:
        pass


def _write_cache(text):
    try:
        with open(CACHE_PATH, "w") as f:
            f.write(text)
    except OSError:
        pass


def _read_file(path):
    try:
        with open(path) as f:
            t = f.read().strip()
            return t or None
    except FileNotFoundError:
        return None


def get_final_script(*, refresh=True):
    """Resolve {"text": str, "source": "live"|"cache"|"fallback"|"none"}. Never raises.
    Live Notion first (refresh the cache on success), else the local cache, else the committed
    fallback snapshot."""
    if refresh:
        try:
            _ensure_notion_key()
            import notion_session as ns
            text = ns.fetch_page_plain_text(FINAL_SCRIPT_PAGE_ID)
            if text and text.strip():
                _write_cache(text)
                return {"text": text, "source": "live"}
        except Exception as e:
            print(f"[final_script] live fetch failed ({e}); using cache/fallback", file=sys.stderr)
    cached = _read_file(CACHE_PATH)
    if cached:
        return {"text": cached, "source": "cache"}
    fb = _read_file(FALLBACK_PATH)
    if fb:
        return {"text": fb, "source": "fallback"}
    return {"text": "", "source": "none"}


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Resolve/refresh the walk-in Follow-Up Script.")
    ap.add_argument("--refresh", action="store_true", help="Force a live fetch + rewrite the cache")
    ap.add_argument("--show", action="store_true", help="Print the resolved text")
    args = ap.parse_args()
    res = get_final_script(refresh=True)
    print(f"[final_script] source={res['source']} chars={len(res['text'])}")
    if args.show:
        print("-" * 60)
        print(res["text"])
    return 0 if res["text"] else 1


if __name__ == "__main__":
    sys.exit(main())
