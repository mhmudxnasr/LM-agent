from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any


def _truncate_output(text: str, max_lines: int) -> tuple[str, bool]:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text, False
    trimmed = "\n".join(lines[-max_lines:])
    return trimmed, True


def run_command(
    command: str,
    cwd: str,
    timeout_seconds: int = 30,
    max_output_lines: int = 200,
) -> dict[str, Any]:
    resolved_cwd = str(Path(cwd).resolve())
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            capture_output=True,
            text=True,
            cwd=resolved_cwd,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout, stdout_truncated = _truncate_output(exc.stdout or "", max_output_lines)
        stderr, stderr_truncated = _truncate_output(exc.stderr or "", max_output_lines)
        return {
            "command": command,
            "cwd": resolved_cwd,
            "ok": False,
            "timed_out": True,
            "exit_code": None,
            "stdout": stdout,
            "stderr": stderr,
            "output_truncated": stdout_truncated or stderr_truncated,
        }

    stdout, stdout_truncated = _truncate_output(completed.stdout or "", max_output_lines)
    stderr, stderr_truncated = _truncate_output(completed.stderr or "", max_output_lines)
    return {
        "command": command,
        "cwd": resolved_cwd,
        "ok": completed.returncode == 0,
        "timed_out": False,
        "exit_code": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "output_truncated": stdout_truncated or stderr_truncated,
    }


def run_python(
    code: str,
    cwd: str,
    timeout_seconds: int = 30,
    max_output_lines: int = 200,
) -> dict[str, Any]:
    resolved_cwd = str(Path(cwd).resolve())
    try:
        completed = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=resolved_cwd,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout, stdout_truncated = _truncate_output(exc.stdout or "", max_output_lines)
        stderr, stderr_truncated = _truncate_output(exc.stderr or "", max_output_lines)
        return {
            "ok": False,
            "timed_out": True,
            "exit_code": None,
            "stdout": stdout,
            "stderr": stderr,
            "output_truncated": stdout_truncated or stderr_truncated,
        }

    stdout, stdout_truncated = _truncate_output(completed.stdout or "", max_output_lines)
    stderr, stderr_truncated = _truncate_output(completed.stderr or "", max_output_lines)
    return {
        "ok": completed.returncode == 0,
        "timed_out": False,
        "exit_code": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "output_truncated": stdout_truncated or stderr_truncated,
    }
