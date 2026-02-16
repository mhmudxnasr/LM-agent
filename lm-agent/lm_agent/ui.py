from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Iterator

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


class UI:
    def __init__(self) -> None:
        self.console = Console()
        self._is_streaming = False

    def show_banner(self, model: str, url: str, cwd: str, yolo: bool) -> None:
        mode = "YOLO (no confirmations)" if yolo else "Safe (confirm destructive tools)"
        text = f"[bold]LM Studio CLI Agent[/bold]\nModel: [cyan]{model}[/cyan]\nURL: {url}\nCWD: {cwd}\nMode: {mode}"
        self.console.print(Panel(text, border_style="blue"))

    @contextmanager
    def status(self, message: str) -> Iterator[None]:
        with self.console.status(message, spinner="dots"):
            yield

    def info(self, message: str) -> None:
        self.console.print(f"[cyan]i[/cyan] {message}")

    def warn(self, message: str) -> None:
        self.console.print(f"[yellow]![/yellow] {message}")

    def error(self, message: str) -> None:
        self.console.print(f"[red]x[/red] {message}")

    def show_tool_call(self, name: str, args: dict[str, Any]) -> None:
        rendered = json.dumps(args, ensure_ascii=False)
        if len(rendered) > 260:
            rendered = f"{rendered[:257]}..."
        self.console.print(f"[magenta]tool[/magenta] {name} {rendered}")

    def show_tool_result(self, name: str, result: dict[str, Any]) -> None:
        status = "ok" if result.get("ok") else "error"
        symbol = "[green]✓[/green]" if status == "ok" else "[red]✗[/red]"
        self.console.print(f"{symbol} {name} ({status})")

    def start_stream(self) -> None:
        self._is_streaming = True

    def stream_token(self, token: str) -> None:
        if not token:
            return
        self.console.print(token, end="", highlight=False, soft_wrap=True)

    def end_stream(self) -> None:
        if self._is_streaming:
            self.console.print()
        self._is_streaming = False

    def render_assistant(self, content: str) -> None:
        if not content:
            return
        self.console.print(Markdown(content))
