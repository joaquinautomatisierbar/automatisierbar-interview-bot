# Voice Agent Script / Config Changelog

Newest first. Each entry: `vN · YYYY-MM-DD · what changed · why`. The live Vapi assistant
(`0a7576f1-35ac-4293-977e-09b6fc3b5923`) always reflects the latest version.

- **v3 · 2026-06-01 · Naturalness + turn-taking pass** — reverted Azure→ElevenLabs native German voice (`eleven_multilingual_v2`, stability 0.4 / style 0.4 / speed 1.08); enabled Vapi **smart (semantic) endpointing** so short answers + pauses don't get cut off; added "lies NICHT Wort für Wort ab" + "nicht wiederholt entschuldigen" rules; firstMessage uses periods (cleaner TTS pacing). *Why:* test call 2 (Azure de-CH) was robotic + slow + choppy turn-taking.
- **v2 · 2026-06-01 · Siezen + tightening** — enforced strict "Sie" (no duzen), shorter replies (maxTokens 250), faster turn-wait, backgroundSound off, tried Azure Swiss voice (later reverted). *Why:* test call 1 slipped from "Sie" into "du", had ambient noise + lag.
- **v1 · 2026-06-01 · Initial build from Skript v2** — deployed assistant from `prompts/voice_agent_conversation.md`: German Skript v2 flow, branche-specific Q1, recording OFF, post-call analysis schema, Claude Haiku 4.5, Deepgram de transcriber.
