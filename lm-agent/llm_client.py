from __future__ import annotations

import ast
import json
import re
import uuid
from dataclasses import dataclass
from typing import Any, Callable

import httpx


TokenCallback = Callable[[str], None]


@dataclass(slots=True)
class ToolCall:
    id: str
    name: str
    arguments_raw: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class ChatResponse:
    content: str
    tool_calls: list[ToolCall]
    finish_reason: str | None
    streamed: bool


class LMStudioClient:
    def __init__(self, base_url: str, model: str | None = None, timeout_seconds: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout_seconds)

    def close(self) -> None:
        self.client.close()

    def list_models(self) -> list[str]:
        response = self.client.get("/models")
        response.raise_for_status()
        payload = response.json()
        models = [entry.get("id", "") for entry in payload.get("data", []) if entry.get("id")]
        return models

    def health_check(self) -> dict[str, Any]:
        models = self.list_models()
        return {"ok": True, "models": models, "model_count": len(models)}

    def ensure_model(self) -> str:
        if self.model:
            return self.model
        models = self.list_models()
        if not models:
            raise RuntimeError("No models found from LM Studio /v1/models.")
        self.model = models[0]
        return self.model

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        on_token: TokenCallback | None = None,
        temperature: float = 0.2,
    ) -> ChatResponse:
        model = self.ensure_model()
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            return self._chat_stream(payload, on_token=on_token)
        except Exception:
            payload["stream"] = False
            return self._chat_non_stream(payload)

    def _chat_stream(self, payload: dict[str, Any], on_token: TokenCallback | None) -> ChatResponse:
        content_parts: list[str] = []
        partial_tool_calls: dict[int, dict[str, Any]] = {}
        finish_reason: str | None = None

        with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                if not line.startswith("data:"):
                    continue

                data = line[5:].strip()
                if not data:
                    continue
                if data == "[DONE]":
                    break

                chunk = json.loads(data)
                choice = (chunk.get("choices") or [{}])[0]
                delta = choice.get("delta") or {}
                finish_reason = choice.get("finish_reason") or finish_reason

                token = delta.get("content")
                if token:
                    content_parts.append(token)
                    if on_token:
                        on_token(token)

                for delta_call in delta.get("tool_calls") or []:
                    index = int(delta_call.get("index", 0))
                    partial = partial_tool_calls.setdefault(
                        index,
                        {
                            "id": None,
                            "name": "",
                            "arguments": "",
                        },
                    )

                    call_id = delta_call.get("id")
                    if call_id:
                        partial["id"] = call_id

                    function_data = delta_call.get("function") or {}
                    if "name" in function_data:
                        partial["name"] += function_data.get("name", "")
                    if "arguments" in function_data:
                        partial["arguments"] += function_data.get("arguments", "")

        tool_calls = self._finalize_tool_calls(partial_tool_calls)
        content = "".join(content_parts)
        if not tool_calls:
            tool_calls = self._parse_fallback_tool_calls(content)
        return ChatResponse(content=content, tool_calls=tool_calls, finish_reason=finish_reason, streamed=True)

    def _chat_non_stream(self, payload: dict[str, Any]) -> ChatResponse:
        response = self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        body = response.json()
        choice = (body.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        finish_reason = choice.get("finish_reason")

        tool_calls: list[ToolCall] = []
        for call in message.get("tool_calls") or []:
            function_data = call.get("function") or {}
            arguments_raw = function_data.get("arguments") or "{}"
            tool_calls.append(
                ToolCall(
                    id=call.get("id") or f"call_{uuid.uuid4().hex}",
                    name=function_data.get("name", ""),
                    arguments_raw=arguments_raw,
                    arguments=self._parse_jsonish(arguments_raw),
                )
            )

        if not tool_calls:
            tool_calls = self._parse_fallback_tool_calls(content)

        return ChatResponse(content=content, tool_calls=tool_calls, finish_reason=finish_reason, streamed=False)

    def _finalize_tool_calls(self, partial_tool_calls: dict[int, dict[str, Any]]) -> list[ToolCall]:
        tool_calls: list[ToolCall] = []
        for index in sorted(partial_tool_calls):
            call = partial_tool_calls[index]
            name = call.get("name", "").strip()
            if not name:
                continue
            arguments_raw = call.get("arguments", "") or "{}"
            tool_calls.append(
                ToolCall(
                    id=call.get("id") or f"call_{uuid.uuid4().hex}",
                    name=name,
                    arguments_raw=arguments_raw,
                    arguments=self._parse_jsonish(arguments_raw),
                )
            )
        return tool_calls

    def _parse_fallback_tool_calls(self, content: str) -> list[ToolCall]:
        fallback_calls: list[ToolCall] = []
        if not content:
            return fallback_calls

        xml_pattern = re.compile(
            r"<tool\s+name=['\"](?P<name>[^'\"]+)['\"]\s*>(?P<args>.*?)</tool>",
            flags=re.DOTALL | re.IGNORECASE,
        )
        action_pattern = re.compile(r"```action\s*(?P<body>.*?)```", flags=re.DOTALL | re.IGNORECASE)

        for match in xml_pattern.finditer(content):
            name = match.group("name").strip()
            args_raw = match.group("args").strip()
            fallback_calls.append(
                ToolCall(
                    id=f"call_{uuid.uuid4().hex}",
                    name=name,
                    arguments_raw=args_raw,
                    arguments=self._parse_jsonish(args_raw),
                )
            )

        for match in action_pattern.finditer(content):
            body = match.group("body").strip()
            data = self._parse_jsonish(body)
            name = str(data.get("tool") or data.get("name") or "").strip()
            args = data.get("args") if isinstance(data.get("args"), dict) else data.get("arguments")
            if name and isinstance(args, dict):
                args_raw = json.dumps(args, ensure_ascii=False)
                fallback_calls.append(
                    ToolCall(
                        id=f"call_{uuid.uuid4().hex}",
                        name=name,
                        arguments_raw=args_raw,
                        arguments=args,
                    )
                )

        return fallback_calls

    @staticmethod
    def _parse_jsonish(raw: str) -> dict[str, Any]:
        if not raw:
            return {}

        raw = raw.strip()
        if not raw:
            return {}

        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(raw)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                continue
        return {"_raw": raw}
