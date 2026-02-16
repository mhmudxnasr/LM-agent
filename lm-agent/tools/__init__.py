from __future__ import annotations

from typing import Any, Callable

from .code import grep_search, read_imports, tree
from .filesystem import (
    copy_file,
    create_directory,
    delete_file,
    edit_file,
    find_files,
    get_file_info,
    list_directory,
    move_file,
    read_file,
    write_file,
)
from .shell import run_command, run_python

ToolHandler = Callable[..., dict[str, Any]]


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents; optional line range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "append": {"type": "boolean"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace text inside a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "search": {"type": "string"},
                    "replace": {"type": "string"},
                    "count": {"type": "integer"},
                },
                "required": ["path", "search", "replace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file or directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "recursive": {"type": "boolean"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files/folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "include_hidden": {"type": "boolean"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "Create a directory (with parents).",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move or rename a file/directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                    "overwrite": {"type": "boolean"},
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copy a file or directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                    "recursive": {"type": "boolean"},
                    "overwrite": {"type": "boolean"},
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "Find files by glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "root": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
                "required": ["pattern", "root"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_info",
            "description": "Get metadata about a file/directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a PowerShell command and return stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "timeout_seconds": {"type": "integer"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Run a Python snippet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "timeout_seconds": {"type": "integer"},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_search",
            "description": "Search for a pattern across files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string"},
                    "glob": {"type": "string"},
                    "max_results": {"type": "integer"},
                    "case_sensitive": {"type": "boolean"},
                },
                "required": ["pattern", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tree",
            "description": "Show directory tree structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_depth": {"type": "integer"},
                    "max_entries": {"type": "integer"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_imports",
            "description": "Read imports/dependencies from a source file.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
]


class ToolRegistry:
    def __init__(self, cwd: str, command_timeout_seconds: int = 30, max_output_lines: int = 200) -> None:
        self.cwd = cwd
        self.command_timeout_seconds = command_timeout_seconds
        self.max_output_lines = max_output_lines
        self.handlers: dict[str, ToolHandler] = {
            "read_file": lambda **kwargs: read_file(cwd=self.cwd, **kwargs),
            "write_file": lambda **kwargs: write_file(cwd=self.cwd, **kwargs),
            "edit_file": lambda **kwargs: edit_file(cwd=self.cwd, **kwargs),
            "delete_file": lambda **kwargs: delete_file(cwd=self.cwd, **kwargs),
            "list_directory": lambda **kwargs: list_directory(cwd=self.cwd, **kwargs),
            "create_directory": lambda **kwargs: create_directory(cwd=self.cwd, **kwargs),
            "move_file": lambda **kwargs: move_file(cwd=self.cwd, **kwargs),
            "copy_file": lambda **kwargs: copy_file(cwd=self.cwd, **kwargs),
            "find_files": lambda **kwargs: find_files(cwd=self.cwd, **kwargs),
            "get_file_info": lambda **kwargs: get_file_info(cwd=self.cwd, **kwargs),
            "run_command": self._run_command,
            "run_python": self._run_python,
            "grep_search": lambda **kwargs: grep_search(cwd=self.cwd, **kwargs),
            "tree": lambda **kwargs: tree(cwd=self.cwd, **kwargs),
            "read_imports": lambda **kwargs: read_imports(cwd=self.cwd, **kwargs),
        }

    def execute_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name not in self.handlers:
            return {"ok": False, "error": f"Unknown tool: {name}"}

        if not isinstance(args, dict):
            return {"ok": False, "error": "Tool arguments must be an object."}

        try:
            result = self.handlers[name](**args)
            if isinstance(result, dict) and "ok" not in result:
                result["ok"] = True
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _run_command(self, command: str, timeout_seconds: int | None = None) -> dict[str, Any]:
        return run_command(
            command=command,
            cwd=self.cwd,
            timeout_seconds=timeout_seconds or self.command_timeout_seconds,
            max_output_lines=self.max_output_lines,
        )

    def _run_python(self, code: str, timeout_seconds: int | None = None) -> dict[str, Any]:
        return run_python(
            code=code,
            cwd=self.cwd,
            timeout_seconds=timeout_seconds or self.command_timeout_seconds,
            max_output_lines=self.max_output_lines,
        )
