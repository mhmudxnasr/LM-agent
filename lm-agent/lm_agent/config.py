from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


def _load_yaml_settings(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}

    try:
        import yaml  # type: ignore
    except Exception:
        return {}

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

    return data if isinstance(data, dict) else {}


def load_runtime_settings(config_path: Path | None = None) -> dict[str, Any]:
    """Load runtime settings from config.yaml and environment overrides."""
    settings: dict[str, Any] = {
        "log_level": "INFO",
        "default_working_dir": str(Path.cwd()),
    }

    path = config_path or Path(__file__).with_name("config.yaml")
    settings.update(_load_yaml_settings(path))

    env_log = os.getenv("LM_AGENT_LOG_LEVEL")
    if env_log:
        settings["log_level"] = env_log

    env_workdir = os.getenv("LM_AGENT_WORKDIR")
    if env_workdir:
        settings["default_working_dir"] = env_workdir

    raw_workdir = str(settings.get("default_working_dir", Path.cwd()))
    expanded_workdir = os.path.expandvars(os.path.expanduser(raw_workdir))
    settings["default_working_dir"] = str(Path(expanded_workdir))

    settings["log_level"] = str(settings.get("log_level", "INFO")).upper()
    return settings


def load_config() -> dict[str, Any]:
    """Backward-compatible alias used by earlier revisions."""
    return load_runtime_settings()
