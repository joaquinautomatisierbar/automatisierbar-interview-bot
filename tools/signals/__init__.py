"""Signal collectors for the weekly LinkedIn brief.

Each module exposes a `collect(week_start, week_end)` function that returns a
JSON-serializable dict. The orchestrator in tools/linkedin_brief.py merges
them, then hands the result to the synthesis prompt.
"""
