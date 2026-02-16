from __future__ import annotations

import json
import re
from typing import Any

from config import BLOCKED_COMMAND_PATTERNS, DESTRUCTIVE_TOOLS


class SafetyManager:
    def __init__(
        self,
        yolo: bool = False,
        destructive_tools: set[str] | None = None,
        blocked_command_patterns: tuple[str, ...] | None = None,
    ) -> None:
        self.yolo = yolo
        self.destructive_tools = destructive_tools or set(DESTRUCTIVE_TOOLS)
        patterns = blocked_command_patterns or BLOCKED_COMMAND_PATTERNS
        self.blocked_command_patterns = [re.compile(pattern) for pattern in patterns]

    def is_destructive(self, tool_name: str) -> bool:
        return tool_name in self.destructive_tools

    def is_blocked_command(self, command: str) -> tuple[bool, str | None]:
        for pattern in self.blocked_command_patterns:
            if pattern.search(command):
                return True, pattern.pattern
        return False, None

    def confirm_execution(self, tool_name: str, args: dict[str, Any]) -> bool:
        if self.yolo or not self.is_destructive(tool_name):
            return True

        preview = self._preview_args(args)
        print(f"[Safety] {tool_name} requested with args: {preview}")
        answer = input("[Safety] Execute this action? [Y/n]: ").strip().lower()
        return answer in {"", "y", "yes"}

    @staticmethod
    def _preview_args(args: dict[str, Any]) -> str:
        try:
            rendered = json.dumps(args, ensure_ascii=False)
        except TypeError:
            rendered = str(args)
        return rendered if len(rendered) <= 300 else f"{rendered[:297]}..."
