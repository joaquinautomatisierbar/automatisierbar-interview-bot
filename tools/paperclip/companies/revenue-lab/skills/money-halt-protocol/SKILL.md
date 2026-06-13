---
name: money-halt-protocol
description: >
  The money-specific halt-before-acting wrapper for Revenue Lab. Use before ANY money-touching
  or external-trust action (spend, real outbound, Stripe TEST->LIVE, first live charge). Pages
  the operator on Telegram and waits for an explicit yes before proceeding.
---

# Money Halt Protocol

A $300 cap and a legal-shell model only hold if every risky action pauses for the operator.
This is the mechanism. Use it for the triggers below — no exceptions.

## When to halt (any one of these → halt FIRST)

- Committing the company to a specific offer (CEO).
- Any external/business spend at all (paid non-Claude API, ad, domain, tool, paid list).
- Any real outbound (email / DM / LinkedIn / call) to a real prospect.
- **Switching Stripe TEST → LIVE** (the most important gate).
- Creating the first LIVE payment surface (link/invoice) for an offer.
- Any charge or invoice above CHF 200.
- Any virtual-card transaction (Phase 2+).

## How to halt + wait (single yes/no question)

From the project root:

```bash
bash .claude/hooks/notify-telegram.sh halt "[revenue-lab] About to <action>. Approve? (yes/no)"
reply=$(bash .claude/hooks/telegram-poll.sh 600)   # 10-min timeout
case "$(echo "$reply" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')" in
  yes|y|ok|go|approve|approved) echo "operator approved" ;;
  no|n|stop|abort|cancel)       echo "operator declined"; exit 1 ;;
  *) echo "ambiguous/timeout: '$reply' — do NOT proceed; treat as no" ;;
esac
```

## Rules

- **One question, ideally yes/no.** The poller captures the first matching reply only.
- **Timeout = no.** Exit code 1 from the poller (10-min default) means no answer → do NOT
  proceed. Pick the safe default (don't spend, don't send).
- **Prefer the Revenue Lab channel.** If `REVENUE_TELEGRAM_BOT_TOKEN` / `REVENUE_TELEGRAM_CHAT_ID`
  are set, the hooks use them — keeps Revenue Lab halts off the Automatisierbar operator bot
  (avoids the documented getUpdates reply-crosstalk).
- **When in doubt, don't act — produce the artifact and hand it to the operator instead.** The
  cost of a clarifying ping is trivial against a $300 cap.
