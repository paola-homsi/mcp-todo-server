# mcp-todo-server

[![CI](https://github.com/paola-homsi/mcp-todo-server/actions/workflows/ci.yml/badge.svg)](https://github.com/paola-homsi/mcp-todo-server/actions/workflows/ci.yml)

A small [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that gives an AI assistant a persistent to-do list it can read and update.

## Why

MCP is the standard way to give an LLM client (Claude Desktop, IDE assistants, agent frameworks) access to tools and data. This project is a minimal, complete example of an MCP server: typed tool inputs, durable local storage, and tests that run without a model in the loop.

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

Add this to your MCP client configuration (for Claude Desktop, `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "todo": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/paola-homsi/mcp-todo-server.git",
        "mcp-todo-server"
      ]
    }
  }
}
```

Restart the client. Tasks are stored in `~/.mcp-todo/tasks.json`. Set `MCP_TODO_FILE` to use a different file.

## Usage

The server exposes four tools:

| Tool | Arguments | Effect |
|---|---|---|
| `add_task` | `title`, `description` (optional) | Adds a task and returns its id |
| `list_tasks` | `include_completed` (default `true`) | Lists tasks with id and status |
| `complete_task` | `task_id` | Marks a task done and records when |
| `delete_task` | `task_id` | Removes a task |

Example prompt: *"Add a task to review the Q3 roadmap, then show me what's still open."*

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## Design notes

- **Storage is a JSON file, written atomically** (temp file, then rename), so a crash mid-write cannot leave a half-written file.
- **A corrupt file stops the server instead of being overwritten.** Losing someone's tasks silently is worse than an error.
- **Ids are `max(id) + 1`**, so they stay unique after deletes within a single process. Concurrent writers from several processes are out of scope; see the roadmap.
- **The tools are thin wrappers over `TaskStore`**, which keeps the storage logic testable without an MCP client.

## Tech

Python 3.12, [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) 2.x, Pydantic 2, pytest, ruff, GitHub Actions.

## Roadmap

- [ ] File locking for concurrent clients
- [ ] Due dates and priorities
- [ ] Expose the task list as an MCP resource as well as through tools
- [ ] SQLite backend behind the same `TaskStore` interface

## License

MIT
