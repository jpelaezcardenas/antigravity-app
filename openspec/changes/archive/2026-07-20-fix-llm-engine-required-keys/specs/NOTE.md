# No capability spec changes

This change is a pure internal bugfix in `agents/llm_engine.py`'s private
`_get_json_with_retry_custom_order` method — an implementation detail with no dedicated
`openspec/specs/` capability document covering it. No `ADDED`/`MODIFIED`/`REMOVED` requirements
apply. See `proposal.md` and `design.md` for the full rationale.
