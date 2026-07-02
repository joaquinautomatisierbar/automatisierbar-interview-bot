"""Befund-Automat — Praxis Tina Ulrich (Zürich-Altstetten).

Self-contained Windows tray app: polls the HIN mailbox via IMAP, reads Befund-PDFs
with an LLM, files them (renamed per the practice's title conventions) into the
Aeskulap import folder, red-flags the mail ONLY on success, and hands Dr. Ulrich a
4-line German summary via toast + clipboard for paste into DigiSono.

Fail-safe contract: an unflagged mail means "wie bisher von Hand" — every failure
path leaves the mailbox untouched. No mail is ever deleted, moved or marked read.
"""

__version__ = "0.1.0"
APP_NAME = "BefundAutomat"
