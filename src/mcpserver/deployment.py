"""MCP tool definitions for the to-do server."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from mcpserver.utils import TaskStore

mcp = MCPServer("todo")
store = TaskStore()


@mcp.tool()
def add_task(title: str, description: str = "") -> str:
    """Add a task to the to-do list and return its id."""
    task = store.add(title, description)
    return f"Added task {task.id}: {task.title}"


@mcp.tool()
def list_tasks(include_completed: bool = True) -> str:
    """List tasks, optionally hiding completed ones."""
    tasks = [t for t in store.load() if include_completed or not t.completed]
    if not tasks:
        return "No tasks found."
    lines = [
        f"[{t.id}] {'done' if t.completed else 'open'}: {t.title}"
        + (f" ({t.description})" if t.description else "")
        for t in tasks
    ]
    return "\n".join(lines)


@mcp.tool()
def complete_task(task_id: int) -> str:
    """Mark a task as completed."""
    task = store.complete(task_id)
    return (
        f"Task {task_id} not found." if task is None else f"Completed task {task_id}: {task.title}"
    )


@mcp.tool()
def delete_task(task_id: int) -> str:
    """Delete a task from the list."""
    task = store.delete(task_id)
    return f"Task {task_id} not found." if task is None else f"Deleted task {task_id}: {task.title}"
