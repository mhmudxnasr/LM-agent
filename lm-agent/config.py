from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_LM_STUDIO_URL = "http://localhost:1234/v1"
DEFAULT_COMMAND_TIMEOUT_SECONDS = 30
DEFAULT_MAX_OUTPUT_LINES = 200
DEFAULT_MAX_HISTORY_MESSAGES = 40

DESTRUCTIVE_TOOLS = {
    "write_file",
    "edit_file",
    "delete_file",
    "move_file",
    "run_command",
    "run_python",
}

BLOCKED_COMMAND_PATTERNS = (
    r"(?i)\bformat\b",
    r"(?i)\brm\s+-rf\s+([\\/]|[A-Za-z]:\\?)",
    r"(?i)\bdel\s+\/s\b",
    r"(?i)\bremove-item\b.*\b-recurse\b.*\b-force\b",
    r"(?i)\bshutdown\b",
    r"(?i)\breboot\b",
)

SYSTEM_PROMPT = """You are a local coding agent running on the user's Windows PC.
You have tools to read, write, and edit files, run shell commands, and search code.
Always use the provided tools for actions. Do not only describe what to do.
Be precise with file paths.
Ask for clarification if a task is ambiguous.
Before destructive actions, request confirmation from the user through the safety system."""


@dataclass(slots=True)
class AgentConfig:
    url: str = DEFAULT_LM_STUDIO_URL
    model: str | None = None
    yolo: bool = False
    cwd: Path = Path.cwd()
    command_timeout_seconds: int = DEFAULT_COMMAND_TIMEOUT_SECONDS
    max_output_lines: int = DEFAULT_MAX_OUTPUT_LINES
    max_history_messages: int = DEFAULT_MAX_HISTORY_MESSAGES
