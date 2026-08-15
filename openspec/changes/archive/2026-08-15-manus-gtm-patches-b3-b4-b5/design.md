## Context

Manus AI applied B3/B4/B5 directly to the working tree via a desktop filesystem mount, without a
Python/pytest environment on its side to verify (confirmed by Manus itself: "pytest no está
instalado"). The applied code passed `ast.parse()` (valid Python) but contained a real logic bug
that only manifests at runtime on the success path — exactly the kind of defect a syntax check
can't catch and only a test exercising the actual control flow would.

## Goals / Non-Goals

**Goals:** formalize the already-applied B3/B4/B5 code through this repo's TDD/OpenSpec process;
add the missing test coverage that would have caught the indentation bug; confirm no other
subtle defect exists in the applied diff.

**Non-Goals:** not re-litigating B3/B4/B5's design (already reviewed and approved via the Manus
report `INFORME-FINAL-MANUS-GTM.md`); not implementing B2 (webhook) — separate, larger scope,
deliberately deferred per the playbook.

## Decisions

**Add tests for the dispatch-time schema-passing behavior**, since that's precisely the code path
the bug lived in and had zero coverage. Mirrors the existing `TestRunTick`/`_dispatch_pending`
test style already in `test_poller.py`.

## Risks / Trade-offs

- **[Risk] Externally-applied patches bypassing TDD is a repeatable failure mode** (an agent
  without a Python environment editing Python files). **Mitigation**: not a policy change in this
  small fix-up change — noting it here as the reason this change exists, and that the founder/
  Claude Code combination remains the verification backstop for any externally-applied code before
  it reaches `main`.

## Migration Plan

1. Bug already fixed (poller.py indentation).
2. Add failing-then-passing test for schema-passing on dispatch.
3. Run the full poller suite, confirm green.
4. Sync spec delta.
5. Stage 11 (local service): commit + push; founder `git pull` + poller restart.

## Open Questions

None blocking.
