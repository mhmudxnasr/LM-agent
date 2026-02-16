from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from config import (
    DEFAULT_LM_STUDIO_URL,
    SYSTEM_PROMPT,
    AgentConfig,
)
from llm_client import ChatResponse, LMStudioClient, ToolCall
from safety import SafetyManager
from tools import TOOL_DEFINITIONS, ToolRegistry
from ui import UI


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LM Studio CLI Agent")
    parser.add_argument("--url", default=DEFAULT_LM_STUDIO_URL, help="LM Studio base URL")
    parser.add_argument("--model", default=None, help="Model name (auto-detect if omitted)")
    parser.add_argument("--yolo", action="store_true", help="Skip all confirmation prompts")
    parser.add_argument("--cwd", default=str(Path.cwd()), help="Working directory for tools")
    parser.add_argument("--health", action="store_true", help="Check API connectivity and list models")
    parser.add_argument(
        "--command-timeout",
        type=int,
        default=30,
        help="Default timeout for run_command/run_python tools in seconds",
    )
    parser.add_argument(
        "--max-output-lines",
        type=int,
        default=200,
        help="Maximum stdout/stderr lines kept from tool output",
    )
    parser.add_argument(
        "--max-history-messages",
        type=int,
        default=40,
        help="Maximum messages retained in conversation history",
    )
    return parser.parse_args()


def trim_messages(messages: list[dict[str, Any]], max_history_messages: int) -> list[dict[str, Any]]:
    if len(messages) <= max_history_messages:
        return messages
    system_message = messages[0]
    return [system_message, *messages[-(max_history_messages - 1) :]]


def serialize_tool_calls(tool_calls: list[ToolCall]) -> list[dict[str, Any]]:
    serialized = []
    for call in tool_calls:
        serialized.append(
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": call.arguments_raw or json.dumps(call.arguments),
                },
            }
        )
    return serialized


def run_health_check(client: LMStudioClient, ui: UI) -> int:
    try:
        with ui.status("Checking LM Studio connection..."):
            payload = client.health_check()
    except Exception as exc:
        ui.error(f"Health check failed: {exc}")
        return 1

    ui.info(f"LM Studio reachable: {payload['model_count']} model(s) available.")
    for model in payload["models"]:
        ui.info(f"- {model}")
    return 0


def handle_chat_turn(
    client: LMStudioClient,
    registry: ToolRegistry,
    safety: SafetyManager,
    ui: UI,
    messages: list[dict[str, Any]],
) -> None:
    while True:
        ui.start_stream()
        response: ChatResponse = client.chat(messages=messages, tools=TOOL_DEFINITIONS, on_token=ui.stream_token)
        ui.end_stream()

        if response.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": serialize_tool_calls(response.tool_calls),
                }
            )

            for tool_call in response.tool_calls:
                args = tool_call.arguments if isinstance(tool_call.arguments, dict) else {}
                tool_name = tool_call.name
                ui.show_tool_call(tool_name, args)

                if tool_name == "run_command":
                    command = str(args.get("command", ""))
                    blocked, reason = safety.is_blocked_command(command)
                    if blocked:
                        result = {
                            "ok": False,
                            "error": f"Blocked command pattern matched: {reason}",
                        }
                        ui.show_tool_result(tool_name, result)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result, ensure_ascii=False),
                            }
                        )
                        continue

                if not safety.confirm_execution(tool_name, args):
                    result = {"ok": False, "error": "User denied execution."}
                    ui.show_tool_result(tool_name, result)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )
                    continue

                result = registry.execute_tool(tool_name, args)
                ui.show_tool_result(tool_name, result)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            continue

        if not response.streamed:
            ui.render_assistant(response.content)
        messages.append({"role": "assistant", "content": response.content})
        break


def main() -> int:
    args = parse_args()
    config = AgentConfig(
        url=args.url,
        model=args.model,
        yolo=args.yolo,
        cwd=Path(args.cwd).resolve(),
        command_timeout_seconds=args.command_timeout,
        max_output_lines=args.max_output_lines,
        max_history_messages=args.max_history_messages,
    )
    config.cwd.mkdir(parents=True, exist_ok=True)

    ui = UI()
    client = LMStudioClient(base_url=config.url, model=config.model, timeout_seconds=max(120, config.command_timeout_seconds))

    if args.health:
        try:
            return run_health_check(client, ui)
        finally:
            client.close()

    try:
        model = client.ensure_model()
    except Exception as exc:
        ui.error(f"Failed to initialize LM Studio client: {exc}")
        client.close()
        return 1

    ui.show_banner(model=model, url=config.url, cwd=str(config.cwd), yolo=config.yolo)
    ui.info("Type `exit` or `quit` to leave.")

    safety = SafetyManager(yolo=config.yolo)
    registry = ToolRegistry(
        cwd=str(config.cwd),
        command_timeout_seconds=config.command_timeout_seconds,
        max_output_lines=config.max_output_lines,
    )

    history_path = Path.home() / ".lm_agent_history"
    session = PromptSession(history=FileHistory(str(history_path)))

    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    try:
        while True:
            try:
                user_input = session.prompt(">>> ").strip()
            except KeyboardInterrupt:
                continue
            except EOFError:
                ui.info("Exiting.")
                break

            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                break

            messages.append({"role": "user", "content": user_input})
            messages = trim_messages(messages, config.max_history_messages)

            handle_chat_turn(client=client, registry=registry, safety=safety, ui=ui, messages=messages)
            messages = trim_messages(messages, config.max_history_messages)
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
