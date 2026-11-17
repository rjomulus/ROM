# Golden tasks

Each phase of ROM's build brief has a gate: a real task the agent must finish, plus a check that
decides pass or fail without a human. Live runs need a model key; the checkers and their tests don't.

| # | Gate for | Task file | Check |
| --- | --- | --- | --- |
| 1 | Phase 0 | `task_01.md` | `check_refs.py` |

Tasks 2 to 5 (one-page gigs site, cited PDF summary, Max for Live humanizer, JUCE FM synth) are added
with the phases they gate.

Run the checkers' own tests (no key needed):

```
uv run pytest tests/golden
```
