from __future__ import annotations

import ast
import fnmatch
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _resolve_path(path: str, cwd: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path(cwd) / candidate
    return candidate.resolve()


def grep_search(
    pattern: str,
    path: str,
    cwd: str,
    glob: str | None = None,
    max_results: int = 200,
    case_sensitive: bool = False,
) -> dict[str, Any]:
    search_root = _resolve_path(path, cwd)
    if shutil.which("rg"):
        return _grep_with_ripgrep(
            pattern=pattern,
            search_root=search_root,
            glob=glob,
            max_results=max_results,
            case_sensitive=case_sensitive,
        )
    return _grep_with_python(
        pattern=pattern,
        search_root=search_root,
        glob=glob,
        max_results=max_results,
        case_sensitive=case_sensitive,
    )


def _grep_with_ripgrep(
    pattern: str,
    search_root: Path,
    glob: str | None,
    max_results: int,
    case_sensitive: bool,
) -> dict[str, Any]:
    command = ["rg", "--json", "--line-number"]
    if not case_sensitive:
        command.append("-i")
    if glob:
        command.extend(["-g", glob])
    command.extend([pattern, str(search_root)])

    completed = subprocess.run(command, capture_output=True, text=True, shell=False)
    if completed.returncode not in (0, 1):
        raise RuntimeError(completed.stderr.strip() or "ripgrep failed")

    matches = []
    for raw_line in completed.stdout.splitlines():
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        if payload.get("type") != "match":
            continue
        data = payload.get("data") or {}
        path_text = (data.get("path") or {}).get("text")
        line_number = data.get("line_number")
        line_text = ((data.get("lines") or {}).get("text") or "").rstrip("\n")
        matches.append({"path": path_text, "line": line_number, "text": line_text})
        if len(matches) >= max_results:
            break

    return {"pattern": pattern, "path": str(search_root), "matches": matches, "used_ripgrep": True}


def _grep_with_python(
    pattern: str,
    search_root: Path,
    glob: str | None,
    max_results: int,
    case_sensitive: bool,
) -> dict[str, Any]:
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags=flags)
    except re.error:
        regex = re.compile(re.escape(pattern), flags=flags)

    matches = []
    for file_path in search_root.rglob("*"):
        if not file_path.is_file():
            continue
        if glob and not fnmatch.fnmatch(file_path.name, glob):
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for idx, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                matches.append({"path": str(file_path), "line": idx, "text": line})
                if len(matches) >= max_results:
                    return {
                        "pattern": pattern,
                        "path": str(search_root),
                        "matches": matches,
                        "used_ripgrep": False,
                    }

    return {"pattern": pattern, "path": str(search_root), "matches": matches, "used_ripgrep": False}


def tree(path: str, cwd: str, max_depth: int = 3, max_entries: int = 500) -> dict[str, Any]:
    root = _resolve_path(path, cwd)
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {root}")

    lines: list[str] = [root.name or str(root)]
    entry_count = 0

    def walk(current: Path, prefix: str, depth: int) -> None:
        nonlocal entry_count
        if depth > max_depth or entry_count >= max_entries:
            return
        children = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for index, child in enumerate(children):
            entry_count += 1
            if entry_count > max_entries:
                lines.append(f"{prefix}... (truncated)")
                return
            connector = "`-- " if index == len(children) - 1 else "|-- "
            lines.append(f"{prefix}{connector}{child.name}")
            if child.is_dir() and depth < max_depth:
                extension = "    " if index == len(children) - 1 else "|   "
                walk(child, prefix + extension, depth + 1)

    if root.is_dir():
        walk(root, "", 1)

    return {"path": str(root), "tree": "\n".join(lines), "max_depth": max_depth}


def read_imports(path: str, cwd: str) -> dict[str, Any]:
    target = _resolve_path(path, cwd)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(f"File not found: {target}")

    suffix = target.suffix.lower()
    text = target.read_text(encoding="utf-8", errors="ignore")
    imports: list[str] = []

    if suffix == ".py":
        parsed = ast.parse(text)
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for entry in node.names:
                    imports.append(entry.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append(module)
    elif suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        pattern = re.compile(
            r"^\s*import\s+(?:.+?\s+from\s+)?['\"]([^'\"]+)['\"]|^\s*const\s+\w+\s*=\s*require\(['\"]([^'\"]+)['\"]\)",
            flags=re.MULTILINE,
        )
        for match in pattern.finditer(text):
            imports.append(match.group(1) or match.group(2))
    else:
        raise ValueError(f"Unsupported file type for import parsing: {suffix}")

    unique_imports = sorted({item for item in imports if item})
    return {"path": str(target), "imports": unique_imports}
