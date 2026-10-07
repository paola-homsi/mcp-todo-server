import asyncio
import json

import pytest

from mcpserver.utils import TaskStore


@pytest.fixture
def store(tmp_path):
    return TaskStore(tmp_path / "tasks.json")


def test_ids_are_unique_and_increasing(store):
    a = store.add("first")
    b = store.add("second")
    assert (a.id, b.id) == (1, 2)


def test_second_add_does_not_crash_and_persists(store):
    # Regression: v0.1 raised TypeError on the second write.
    store.add("first")
    store.add("second")
    assert [t.title for t in store.load()] == ["first", "second"]


def test_created_at_is_per_task(store):
    a = store.add("a")
    b = store.add("b")
    assert b.created_at >= a.created_at
    assert a.created_at.tzinfo is not None


def test_complete_and_delete(store):
    t = store.add("ship it")
    done = store.complete(t.id)
    assert done.completed and done.completed_at is not None
    assert store.delete(t.id).id == t.id
    assert store.load() == []


def test_unknown_ids_return_none(store):
    assert store.complete(99) is None
    assert store.delete(99) is None


def test_ids_not_reused_after_delete_of_earlier_task(store):
    store.add("a")
    b = store.add("b")
    store.delete(1)
    assert store.add("c").id == b.id + 1


def test_corrupt_file_is_not_overwritten(store):
    store.path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        store.add("x")
    assert store.path.read_text(encoding="utf-8") == "{not json"


def test_file_is_plain_json(store):
    store.add("a", "desc")
    data = json.loads(store.path.read_text(encoding="utf-8"))
    assert data[0]["title"] == "a" and data[0]["description"] == "desc"


def test_tools_are_registered(monkeypatch, tmp_path):
    monkeypatch.setenv("MCP_TODO_FILE", str(tmp_path / "t.json"))
    import importlib

    import mcpserver.deployment as dep

    importlib.reload(dep)
    names = {t.name for t in asyncio.run(dep.mcp.list_tools())}
    assert names == {"add_task", "list_tasks", "complete_task", "delete_task"}
    assert dep.add_task("write tests") == "Added task 1: write tests"
    assert "[1] open: write tests" in dep.list_tasks()
