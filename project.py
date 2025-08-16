import argparse
import json
from pathlib import Path
from typing import Any

# Ruta por defecto (puede ser monkeypatcheada en tests)
DB_PATH = Path("db.json")

# ------------------------------
# Utilidades
# ------------------------------

def recompute_next_id(tasks: list[dict[str, Any]]) -> int:
    """Calcula el siguiente ID seguro en base a las tareas existentes."""
    max_id = max((t["id"] for t in tasks), default=0)
    return max_id + 1

# ------------------------------
# Capa de persistencia y validación
# ------------------------------

def load_db(path: Path = DB_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"next_id": 1, "tasks": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise ValueError("JSON inválido")
    _validate_db(data)
    return data

def save_db(db: dict[str, Any], path: Path = DB_PATH) -> None:
    # Forzamos coherencia antes de persistir
    db["next_id"] = recompute_next_id(db["tasks"])
    path.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

def _validate_db(data: dict[str, Any]) -> None:
    tasks = data.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("'tasks' debe ser una lista")

    ids = [t.get("id") for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("IDs duplicados")
    if any(not isinstance(tid, int) or tid <= 0 for tid in ids):
        raise ValueError("ID inválido")

    expected = recompute_next_id(tasks)
    next_id = data.get("next_id", 1)
    # Solo fallo si está por debajo → riesgo de colisión
    if next_id < expected:
        raise ValueError("next_id incoherente (riesgo de colisión)")

    # Normalizamos en memoria para el resto del flujo
    data["next_id"] = expected

# ------------------------------
# Lógica de negocio
# ------------------------------

def normalize_title(title: str) -> str:
    return " ".join(title.strip().split())

def add_task(db: dict[str, Any], title: str) -> dict[str, Any]:
    title = normalize_title(title)
    if not title:
        raise ValueError("El título no puede estar vacío")
    task = {"id": db["next_id"], "title": title, "done": False}
    db["tasks"].append(task)
    db["next_id"] += 1
    return task

def list_tasks(db: dict[str, Any], show_all: bool) -> None:
    """Muestra tareas filtrando por show_all, o avisa si no hay ninguna."""
    shown = 0
    for t in db["tasks"]:
        if not show_all and t["done"]:
            continue
        mark = "✓" if t["done"] else "·"
        print(f"{t['id']:>3} [{mark}] {t['title']}")
        shown += 1
        
    if shown == 0:
        print("(no hay tareas para mostrar)")


def delete_task(db: dict[str, Any], task_id: int) -> dict[str, Any]:
    if not isinstance(task_id, int):
        raise TypeError("task_id debe ser un int")
    if task_id <= 0:
        raise ValueError("ID debe ser entero positivo")
    for i, t in enumerate(db["tasks"]):
        if t["id"] == task_id:
            return db["tasks"].pop(i)
    raise ValueError("No se encontró tarea con ese ID")

# ------------------------------
# Handlers de subcomandos
# ------------------------------

def cmd_add(args) -> int:
    try:
        db = load_db(DB_PATH)
        task = add_task(db, args.title)
        save_db(db, DB_PATH)
        print(f"Tarea creada #{task['id']}: {task['title']}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 2

def cmd_list(args) -> int:
    try:
        db = load_db(DB_PATH)
        list_tasks(db, show_all=args.all)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 2

def cmd_delete(args) -> int:
    try:
        db = load_db(DB_PATH)
        removed = delete_task(db, int(args.id))
        save_db(db, DB_PATH)
        print(f"Eliminada #{removed['id']}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 2

# ------------------------------
# CLI
# ------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gestor de tareas CLI")
    subparsers = parser.add_subparsers(dest="cmd")

    p_add = subparsers.add_parser("add", help="Añadir una nueva tarea")
    p_add.add_argument("title", help="Título de la tarea")
    p_add.set_defaults(func=cmd_add)

    p_list = subparsers.add_parser("list", help="Listar tareas")
    p_list.add_argument("-a", "--all", action="store_true", help="Mostrar todas, incluidas completadas")
    p_list.set_defaults(func=cmd_list)

    p_del = subparsers.add_parser("delete", help="Eliminar tarea por ID")
    p_del.add_argument("id", type=int, help="ID de la tarea a eliminar")
    p_del.set_defaults(func=cmd_delete)

    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())