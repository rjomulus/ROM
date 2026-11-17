# Golden task 1: trace tool_choice through the LLM client

Gate for Phase 0. Exercises: coding, code search, writing a deliverable.

## Prompt

Give `main.py` exactly this prompt (paths are fixed so the check can find the output):

```
Clone https://github.com/FoundationAgents/OpenManus into workspace/golden-01/OpenManus. In that clone, find every place an LLM client is constructed, trace how tool_choice travels from config.toml to the API call, and write it up as a short Markdown doc at workspace/golden-01/llm-trace.md. Cite code as path:line, with paths relative to the clone root (for example app/llm.py:216).
```

On Windows PowerShell, from the repo root:

```
uv run python main.py --prompt (Get-Content tests/golden/task_01.prompt.txt -Raw)
```

## Pass condition

```
uv run python tests/golden/check_refs.py workspace/golden-01/llm-trace.md workspace/golden-01/OpenManus
```

Passes when the doc exists, has at least 5 `path:line` references, cites `app/llm.py`, mentions
`tool_choice`, and every reference resolves to a real line in the clone.
