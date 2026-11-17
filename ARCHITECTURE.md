# ROM architecture map

ROM is Romulus's fork of [OpenManus](https://github.com/FoundationAgents/OpenManus).
This map covers the upstream code as it stands; ROM-only changes are marked **ROM**.

## Entry points

| File | What it runs |
| --- | --- |
| `main.py` | One `Manus` agent on one prompt (`--prompt "..."` or typed). The everyday entry point. |
| `run_flow.py` | `PlanningFlow`: an LLM writes a plan, then steps go to `Manus` (and `DataAnalysis` if `[runflow] use_data_analysis_agent = true`). Upstream calls it unstable. |
| `run_mcp.py` | `MCPAgent` talking to OpenManus's own tools over MCP (stdio or SSE). |
| `run_mcp_server.py` | Serves OpenManus's tools as an MCP server (`app/mcp/server.py`). |
| `sandbox_main.py` | `SandboxManus` in a Daytona cloud sandbox (`app/daytona/`). |

## The agent loop (`app/agent/`)

Inheritance runs top to bottom:

```
BaseAgent (base.py)        run(): step loop, max_steps, stuck detection, memory, state
 └─ ReActAgent (react.py)  step() = think() then act()
     └─ ToolCallAgent (toolcall.py)
         │   think(): llm.ask_tool(messages, tools, tool_choice) -> tool calls
         │   act():   runs each tool, appends results; Terminate ends the run
         ├─ Manus (manus.py)            general agent: Python, file editor, ask-human,
         │                              terminate, plus tools from MCP servers
         ├─ MCPAgent (mcp.py)
         │   └─ BrowserAgent (browser.py)  browser via Browser Use CLI 3.0 MCP server
         ├─ SWEAgent (swe.py)           bash + file editor coding agent
         ├─ DataAnalysis (data_analysis.py)  Python + chart tools
         └─ SandboxManus (sandbox_agent.py)  Daytona-backed tools
```

`tool_choice` is `auto` everywhere (`ToolCallAgent.tool_choices`, `PlanningFlow`), which matters
because Opus 5.5 and Sonnet 5.5 reject forced tool use.

## Flows (`app/flow/`)

- `base.py`: `BaseFlow` holds named agents.
- `planning.py`: `PlanningFlow` creates a plan with the `planning` tool, picks the executor per step,
  marks steps done, and summarises at the end. This is where the build brief's Conductor grows (Phase 2).
- `flow_factory.py`: `FlowType.PLANNING` is the only flow.

## Tools (`app/tool/`)

Every tool subclasses `BaseTool` (`base.py`) and returns a `ToolResult`; `ToolCollection`
(`tool_collection.py`) turns them into OpenAI-style function schemas.

- Code and files: `python_execute.py`, `bash.py`, `str_replace_editor.py`, `file_operators.py`
- Planning and control: `planning.py`, `terminate.py`, `ask_human.py`, `create_chat_completion.py`
- Web: `web_search.py` + `search/` (Google, Bing, DuckDuckGo, Baidu with fallbacks), `crawl4ai.py`
- Browser: no in-process tool any more; `browser-use --cli-mcp` is attached as an MCP server
  (upstream, Aug 2026) and `BrowserContextHelper` (`app/agent/browser.py`) feeds page state and
  screenshots back to the agent.
- `computer_use_tool.py`, `chart_visualization/`, `sandbox/` (tools that run inside the Docker sandbox)
- `mcp.py`: `MCPClients` connects to MCP servers and exposes their tools as local tools.

## The LLM client (`app/llm.py`)

One `LLM` class, one instance per config name (singleton). Everything goes through the OpenAI SDK:

- `api_type = "azure"` → `AsyncAzureOpenAI`
- `api_type = "aws"` → `BedrockClient` (`app/bedrock.py`, an OpenAI-shaped wrapper over Bedrock)
- anything else → `AsyncOpenAI(base_url=...)`, which covers Anthropic's OpenAI-compatible endpoint,
  DeepSeek, Ollama, LM Studio and other OpenAI-compatible providers.

Methods: `ask()` (text), `ask_with_images()`, `ask_tool()` (the one agents use). Token counting uses
tiktoken with a `cl100k_base` fallback, so counts for Claude and DeepSeek are estimates.

Images are only sent to models listed in `MULTIMODAL_MODELS`; any other model silently gets text only.
**ROM:** added Claude 5, `deepseek-flash` and `qwen3-vl:8b` to that list so screenshots reach them.

## Config (`app/config.py`, `config/`)

`config/config.toml` is read if present, else `config/config.example.toml`. `[llm]` is the default
model. Named sub-sections (`[llm.vision]`, `[llm.<name>]`) are parsed, but today's agents all use
`[llm]`; per-role routing is Phase 3 of the build brief. Other sections: `[browser]`, `[search]`,
`[sandbox]`, `[mcp]`, `[runflow]`, `[daytona]`. MCP servers to auto-connect live in `config/mcp.json`.
**ROM:** `daytona_api_key` is now optional; upstream required it, so any config without a `[daytona]`
section crashed at start, including every `config.example-model-*.toml`.

Ready-made model configs: `config.example-model-*.toml`. **ROM:** `anthropic` updated for Claude 5,
`deepseek` added, `ollama` sized for a 16 GB GPU.

## MCP (`app/mcp/`)

`server.py` exposes the bash, editor and terminate tools over MCP. As a client, `Manus` connects to
every server in `config/mcp.json` at start and adds their tools.

## Sandbox (`app/sandbox/`, `app/daytona/`)

- `app/sandbox/`: optional local Docker sandbox (`[sandbox] use_sandbox`), with a terminal and file ops
  inside the container.
- `app/daytona/`: Daytona cloud sandboxes for `sandbox_main.py`.

## Where output goes

Agents write files under `workspace/` (`config.workspace_root`). Logs go to `logs/`.

## Other

- `app/prompt/`: system and next-step prompts per agent.
- `protocol/a2a/`: an Agent-to-Agent protocol server wrapping Manus.
- `tests/`: sandbox and browser-MCP tests (upstream); **ROM:** `tests/golden/` (see `tests/golden/README.md`).
