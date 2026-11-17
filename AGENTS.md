# AGENTS.md: working on ROM

Rules for any coding agent (Claude Code, Codex, ROM itself) changing this repo.
Read `ARCHITECTURE.md` first for the map.

## What ROM is

A personal fork of OpenManus, aimed at Manus-level follow-through: an orchestrator with specialist
agents, a live view of the work, steering mid-task, and per-role model routing across Claude, DeepSeek
and local models on a Windows PC with an RTX 5080 (16 GB VRAM). The phased plan lives in Romulus's
build brief; phases 0 to 5 are summarised under "Build order" below.

## Ground rules

1. **Stay rebaseable.** `upstream` is FoundationAgents/OpenManus. Prefer new files and small,
   clearly marked edits (`# ROM:` comments) over rewrites of upstream files, so monthly rebases stay easy.
2. **Config, not code, picks models.** Never hard-code a model name or key in Python. Keys never go in
   git: `config/config.toml` is git-ignored.
3. **Claude 5 on the OpenAI-compatible endpoint needs `temperature = 1.0`,** and Opus/Sonnet 5.5 reject
   forced tool use. Keep `tool_choice` at `auto`; if a step must call a tool, say so in the prompt.
4. **Every phase has a gate in `tests/golden/`.** A change that claims a phase is done shows its golden
   task passing.
5. **Guards live in code, not prompts:** path and executable allow-lists, and confirmation before
   deleting, overwriting a Live set, sending messages or spending money.
6. **The `sensitive` flag (Phase 3) pins a task to local models and fails closed** if none is up.
7. Python 3.12, `uv`, Windows first. Use `pathlib`; don't assume POSIX shells or paths.
8. Run `pre-commit run --all-files` and `pytest tests/golden` before you call a change done.

## Build order (from the brief)

- **Phase 0, fork and baseline.** uv on Windows, config pointed at Claude, Browser Use on local Chrome,
  `ARCHITECTURE.md`. Gate: golden task 1 completes from `main.py` with no edits to upstream code.
- **Phase 1, event bus and UI.** JSONL event log per task, FastAPI + WebSocket, Plan / Computer / Chat /
  Deliverables panes, an interjection queue in the loop. Gate: steer golden task 1 mid-run.
- **Phase 2, Conductor and specialists.** Grow `PlanningFlow` into the Conductor; Browser, Coder,
  Researcher and Deliverables specialists; fan-out; project memory. Gate: golden tasks 1 to 3.
- **Phase 3, model routing.** LiteLLM in front of Anthropic (native, with prompt caching), DeepSeek,
  local and others; per-role config, fallbacks, cost per call, `sensitive` forces local.
  Gate: golden task 3 completes with the Anthropic key removed.
- **Phase 4, studio integrations.** Ableton, Max for Live and plugin-build MCP servers. Gate: tasks 4 and 5.
- **Phase 5, hardening.** Windows service, LAN-only UI with a token, scheduled runs, an upstream rebase
  script. Gate: an overnight unattended run leaves deliverables and a summary.

## Status

Phase 0 in progress on branch `rom/phase-0-models`: model configs, this file, the architecture map,
golden task 1 and its checker.
