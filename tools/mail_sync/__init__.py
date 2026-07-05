"""mail_sync — inbound/outbound mail → CRM logger (Hub LeadMail thread + intent tags).

Reads INBOX + Sent across the 5 team mailboxes, classifies each message's intent, and pushes
it to the Automatisierbar Hub as a tagged LeadMail. Reuses the battle-tested IMAP helpers from
tools/inbox_reply_drafter.py (single source of that logic) and the Anthropic primitives in
tools/claude_client.py. DRAFTS/READS ONLY on the mail side — never sends.
"""
