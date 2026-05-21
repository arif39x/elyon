# Monad v0.1.0

![Monad Logo](assets/Logo.png)

Monad is a multi-agent CLI workspace whose main focus is to use cli agentss but not use so much tokens for autonomous software engineering.

## Components

- `cli/`: command surface for interactive and non-interactive workflows
- `orchestration/`: Python cognition/orchestration/event routing layer
- `runtime/`: Rust execution runtime for sandboxed subprocess control
- `compiler/` + `diagnostics/`: structured compiler diagnostic parsing/classification
- `repair/`: repair strategy generation from compiler diagnostics
- `providers/`: provider abstraction and lazy registration
- `state/`: immutable session and event storage facilities
- `telemetry/`: structured logging and timing helpers

## Quick Start

1. Create a config:
   - `monad init --output configs/monad.toml`
2. Point CLI to config:
   - `export MONAD_CONFIG=configs/monad.toml`
3. Check health:
   - `monad doctor`
4. Run:
   - `monad run --prompt "analyze compile error" --provider local_mock`

## CLI Commands

| Command                              | Description                                                 |
| ------------------------------------ | ----------------------------------------------------------- |
| `monad init`                         | Generate a starter config file                              |
| `monad run`                          | Send a prompt to an LLM provider                            |
| `monad repair`                       | Generate a repair plan from compiler diagnostics            |
| `monad doctor`                       | Check system health and configuration                       |
| `monad providers`                    | List configured LLM providers                               |
| `monad agents`                       | Detect CLI agents on your system and list configured agents |
| `monad project --file <file>`        | Orchestrate a project across CLI agents via JSONL task file |
| `monad sandbox`                      | Validate sandbox policy for a given command                 |
| `monad trace`                        | Look up an execution trace by ID                            |
| `monad compile --diagnostics <file>` | Parse a structured diagnostics file                         |
| `monad compile --exec-command "..."` | Execute a compiler command via the runtime                  |
| `monad compile --zero <file>`        | Compile a `.zero` file and estimate token savings           |

## Agent Detection

`monad agents` dynamically scans your `$PATH` for AI CLI tools using heuristic name patterns (not a hardcoded list). It detects tools like opencode, aider, claude, codex, gemini, ollama, deepseek, and any binary with AI-related naming. Each detected agent shows its command signature (how Monad will invoke it).

## Project Orchestration

Create a `.jsonl` file defining tasks, their agent assignments, and dependencies:

```jsonl
{"id": "setup", "agent": "opencode", "prompt": "Create a FastAPI app", "files": ["main.py"]}
{"id": "models", "agent": "codex", "prompt": "Define Pydantic models", "files": ["models.py"], "depends_on": ["setup"]}
```

Tasks without dependencies run in **parallel**. All execution goes through the **Rust sandbox** for security.

## Zero Compiler

The Zero compiler (`monad compile --zero <file>`) parses `.zero` files, strips commentary and filler words, and reports token savings. This reduces LLM token usage by stripping unnecessary prose before sending prompts to agents.
