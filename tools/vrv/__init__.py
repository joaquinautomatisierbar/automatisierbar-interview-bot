"""vRv Discovery Tool — tender-specific discovery companion (Ausschreibung vR verwaltungen ag).

Isolation contract (mirrors tools/ausgaben/):
- Self-contained package: catalog (static question catalog), store (JSON on disk),
  synthesis (AI follow-ups + exports), routes (Flask Blueprint).
- Registered in api.py behind a guarded try/except; a broken import must never
  crash the shared app.
- Own auth namespace (session["vrv_auth"], session["vrv_client"]); never reuses
  cockpit/ausgaben/team auth flags.
- Writes ONLY to VRV_DATA_DIR (default <repo>/data/vrv/, gitignored). Never touches
  Notion production databases or other tools' state.
- Spec + rationale: tender-vrv/MASTERPLAN.md (section "WS1 Detail-Spec").
"""
