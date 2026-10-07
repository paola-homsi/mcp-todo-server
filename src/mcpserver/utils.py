"""File-backed task storage for the to-do MCP server."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_PATH = Path.home() / ".mcp-todo" / "tasks.json"


def _now() -> datetime:
    return datetime.now(UTC)


class Task(BaseModel):
    id: int
    title: str
    description: str = ""
    completed: bool = False
    # default_factory, not a default value: a plain default is evaluated once
    # at import time, so every task would share the same timestamp.
    created_at: datetime = Field(default_factory=_now)
    completed_at: datetime | None = None


class TaskStore:
    """Persists tasks as a JSON list. Writes are atomic (temp file + rename)."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path or os.environ.get("MCP_TODO_FILE") or DEFAULT_PATH)

    def load(self) -> list[Task]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            # Refuse to continue rather than silently overwrite the user's data.
            raise ValueError(f"{self.path} is not valid JSON") from exc
        if not isinstance(data, list):
            raise TypeError(f"{self.path} must contain a JSON list")
        return [Task.model_validate(item) for item in data]

    def save(self, tasks: list[Task]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            [t.model_dump(mode="json") for t in tasks], indent=2, ensure_ascii=False
        )
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
            os.replace(tmp, self.path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    def add(self, title: str, description: str = "") -> Task:
        tasks = self.load()
        next_id = max((t.id for t in tasks), default=0) + 1
        task = Task(id=next_id, title=title, description=description)
        tasks.append(task)
        self.save(tasks)
        return task

    def complete(self, task_id: int) -> Task | None:
        tasks = self.load()
        for task in tasks:
            if task.id == task_id:
                if not task.completed:
                    task.completed = True
                    task.completed_at = _now()
                    self.save(tasks)
                return task
        return None

    def delete(self, task_id: int) -> Task | None:
        tasks = self.load()
        for i, task in enumerate(tasks):
            if task.id == task_id:
                removed = tasks.pop(i)
                self.save(tasks)
                return removed
        return None
