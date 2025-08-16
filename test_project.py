from pathlib import Path
import json
import types
import project
import pytest


def _set_tmp_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect project.DB_PATH to a temp file and return its path."""
    db_path = tmp_path / "db.json"
    monkeypatch.setattr(project, "DB_PATH", db_path, raising=True)
    return db_path


def _write_json(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def test_load_db_initial_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = _set_tmp_db(monkeypatch, tmp_path)
    # No file yet → should initialize fresh structure
    db = project.load_db(db_path)
    assert db == {"next_id": 1, "tasks": []}


def test_add_and_persist_and_reload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = _set_tmp_db(monkeypatch, tmp_path)

    # Add a task and persist
    db = project.load_db(db_path)
    t = project.add_task(db, "  Hello    world  ")
    project.save_db(db, db_path)

    # Validate new task and normalization
    assert t["id"] == 1
    assert t["title"] == "Hello world"
    assert t["done"] is False

    # Reload and check persistence
    db2 = project.load_db(db_path)
    assert db2["next_id"] == 2
    assert db2["tasks"] == [{"id": 1, "title": "Hello world", "done": False}]


def test_list_outputs_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    db_path = _set_tmp_db(monkeypatch, tmp_path)
    _write_json(
        db_path,
        {
            "next_id": 3,
            "tasks": [
                {"id": 1, "title": "A", "done": False},
                {"id": 2, "title": "B", "done": True},
            ],
        },
    )

    db = project.load_db(db_path)

    # Default: hide done tasks
    project.list_tasks(db, show_all=False)
    out = capsys.readouterr().out
    assert "  1 [·] A" in out
    assert "  2 [✓] B" not in out

    # Show all
    project.list_tasks(db, show_all=True)
    out = capsys.readouterr().out
    assert "  2 [✓] B" in out


def test_delete_existing_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = _set_tmp_db(monkeypatch, tmp_path)
    _write_json(
        db_path,
        {"next_id": 3, "tasks": [{"id": 1, "title": "A", "done": False}, {"id": 2, "title": "B", "done": True}]},
    )
    db = project.load_db(db_path)
    removed = project.delete_task(db, 2)
    assert removed["id"] == 2
    assert all(t["id"] != 2 for t in db["tasks"])


def test_delete_nonexistent_id_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = _set_tmp_db(monkeypatch, tmp_path)
    _write_json(db_path, {"next_id": 1, "tasks": []})
    db = project.load_db(db_path)
    with pytest.raises(ValueError, match="No se encontró tarea"):
        project.delete_task(db, 99)


def test_cmd_delete_integration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    db_path = _set_tmp_db(monkeypatch, tmp_path)
    _write_json(
        db_path,
        {"next_id": 2, "tasks": [{"id": 1, "title": "Keep me", "done": False}]},
    )
    # Build args-like object for handler
    args = types.SimpleNamespace(id=1)
    code = project.cmd_delete(args)
    out = capsys.readouterr().out
    assert code == 0
    assert "Eliminada #1" in out
    # DB should be saved without the deleted item
    db = project.load_db(db_path)
    assert db["tasks"] == []


def test_main_integration_add_list_delete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    db_path = _set_tmp_db(monkeypatch, tmp_path)

    # Add
    code = project.main(["add", "Buy milk"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Tarea creada #1" in out

    # List
    code = project.main(["list"])
    out = capsys.readouterr().out
    assert code == 0
    assert "[·] Buy milk" in out

    # Delete
    code = project.main(["delete", "1"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Eliminada #1" in out

    # Delete non-existent → error code 2
    code = project.main(["delete", "999"])
    out = capsys.readouterr().out
    assert code == 2
    assert "Error:" in out


def test_load_db_json_corrupt_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = _set_tmp_db(monkeypatch, tmp_path)
    db_path.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON inválido"):
        project.load_db(db_path)


def test_load_db_duplicate_ids_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = _set_tmp_db(monkeypatch, tmp_path)
    _write_json(
        db_path,
        {
            "next_id": 3,
            "tasks": [
                {"id": 1, "title": "A", "done": False},
                {"id": 1, "title": "B", "done": True},
            ],
        },
    )
    with pytest.raises(ValueError, match="IDs duplicados"):
        project.load_db(db_path)


def test_load_db_next_id_incoherent_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = _set_tmp_db(monkeypatch, tmp_path)
    _write_json(
        db_path,
        {
            "next_id": 2,
            "tasks": [{"id": 2, "title": "A", "done": False}],
        },
    )
    with pytest.raises(ValueError, match="incoherente"):
        project.load_db(db_path)


def test_normalize_title_and_add_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = _set_tmp_db(monkeypatch, tmp_path)
    db = project.load_db(db_path)

    # Normalization
    t = project.add_task(db, "   Hola    mundo   ")
    assert t["title"] == "Hola mundo"

    # Empty after normalization
    with pytest.raises(ValueError, match="no puede estar vacío"):
        project.add_task(db, "    ")


def test_delete_task_type_and_value_checks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = _set_tmp_db(monkeypatch, tmp_path)
    _write_json(db_path, {"next_id": 1, "tasks": []})
    db = project.load_db(db_path)

    with pytest.raises(TypeError, match="task_id debe ser un int"):
        project.delete_task(db, "1")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="entero positivo"):
        project.delete_task(db, 0)