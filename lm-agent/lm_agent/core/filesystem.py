from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


def _resolve_path(path: str, cwd: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path(cwd) / candidate
    return candidate.resolve()


def read_file(
    path: str,
    cwd: str,
    start_line: int | None = None,
    end_line: int | None = None,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    file_path = _resolve_path(path, cwd)
    content = file_path.read_text(encoding=encoding)

    if start_line is not None or end_line is not None:
        lines = content.splitlines()
        start = max((start_line or 1) - 1, 0)
        end = end_line if end_line is not None else len(lines)
        sliced = lines[start:end]
        content = "\n".join(sliced)

    return {"path": str(file_path), "content": content}


def write_file(
    path: str,
    content: str,
    cwd: str,
    encoding: str = "utf-8",
    append: bool = False,
) -> dict[str, Any]:
    file_path = _resolve_path(path, cwd)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with file_path.open(mode, encoding=encoding) as handle:
        handle.write(content)
    return {"path": str(file_path), "bytes_written": len(content.encode(encoding))}


def edit_file(
    path: str,
    search: str,
    replace: str,
    cwd: str,
    encoding: str = "utf-8",
    count: int = 0,
) -> dict[str, Any]:
    file_path = _resolve_path(path, cwd)
    original = file_path.read_text(encoding=encoding)
    occurrences = original.count(search)
    if occurrences == 0:
        raise ValueError(f"Text not found in {file_path}")
    updated = original.replace(search, replace, count if count > 0 else occurrences)
    file_path.write_text(updated, encoding=encoding)
    return {"path": str(file_path), "occurrences_replaced": min(count, occurrences) if count > 0 else occurrences}


def delete_file(path: str, cwd: str, recursive: bool = False) -> dict[str, Any]:
    target = _resolve_path(path, cwd)
    if target.is_dir():
        if not recursive:
            raise ValueError("Refusing to delete directory without recursive=true.")
        shutil.rmtree(target)
        return {"path": str(target), "deleted": "directory"}
    if target.exists():
        target.unlink()
        return {"path": str(target), "deleted": "file"}
    raise FileNotFoundError(f"Path not found: {target}")


def list_directory(path: str, cwd: str, include_hidden: bool = False) -> dict[str, Any]:
    dir_path = _resolve_path(path, cwd)
    entries = []
    for item in sorted(dir_path.iterdir(), key=lambda p: p.name.lower()):
        if not include_hidden and item.name.startswith("."):
            continue
        entry_type = "directory" if item.is_dir() else "file"
        size = item.stat().st_size if item.is_file() else None
        entries.append({"name": item.name, "type": entry_type, "size": size})
    return {"path": str(dir_path), "entries": entries}


def create_directory(path: str, cwd: str, parents: bool = True) -> dict[str, Any]:
    dir_path = _resolve_path(path, cwd)
    dir_path.mkdir(parents=parents, exist_ok=True)
    return {"path": str(dir_path), "created": True}


def move_file(source: str, destination: str, cwd: str, overwrite: bool = False) -> dict[str, Any]:
    source_path = _resolve_path(source, cwd)
    destination_path = _resolve_path(destination, cwd)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    if destination_path.exists():
        if not overwrite:
            raise FileExistsError(f"Destination exists: {destination_path}")
        if destination_path.is_dir():
            shutil.rmtree(destination_path)
        else:
            destination_path.unlink()

    shutil.move(str(source_path), str(destination_path))
    return {"source": str(source_path), "destination": str(destination_path)}


def copy_file(
    source: str,
    destination: str,
    cwd: str,
    recursive: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    source_path = _resolve_path(source, cwd)
    destination_path = _resolve_path(destination, cwd)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    if destination_path.exists() and not overwrite:
        raise FileExistsError(f"Destination exists: {destination_path}")

    if source_path.is_dir():
        if not recursive:
            raise ValueError("Source is a directory; set recursive=true to copy directories.")
        if destination_path.exists():
            shutil.rmtree(destination_path)
        shutil.copytree(source_path, destination_path)
    else:
        shutil.copy2(source_path, destination_path)

    return {"source": str(source_path), "destination": str(destination_path)}


def find_files(pattern: str, root: str, cwd: str, max_results: int = 200) -> dict[str, Any]:
    root_path = _resolve_path(root, cwd)
    matches = []
    for path in root_path.rglob(pattern):
        matches.append(str(path))
        if len(matches) >= max_results:
            break
    return {"root": str(root_path), "pattern": pattern, "matches": matches}


def get_file_info(path: str, cwd: str) -> dict[str, Any]:
    target = _resolve_path(path, cwd)
    stats = target.stat()
    return {
        "path": str(target),
        "exists": target.exists(),
        "is_file": target.is_file(),
        "is_directory": target.is_dir(),
        "size_bytes": stats.st_size,
        "modified_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
    }
