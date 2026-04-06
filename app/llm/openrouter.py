from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings
from app.llm.base import LLMCompletionResult
from app.llm.base import LLMMessage
from app.llm.base import LLMProvider
from app.llm.base import LLMToolCallRequest


class OpenRouterProvider(LLMProvider):
    provider_name = "openrouter"

    def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMCompletionResult:
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        payload: dict[str, Any] = {
            "model": settings.openrouter_model,
            "temperature": temperature,
            "messages": [msg.to_api_dict() for msg in messages],
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://stocky.local",
            "X-Title": settings.openrouter_app_name,
        }

        with httpx.Client(
            base_url=settings.openrouter_base_url, timeout=60.0
        ) as client:
            response = client.post("/chat/completions", json=payload, headers=headers)
            response.raise_for_status()

        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]
        model = data.get("model", settings.openrouter_model)
        finish_reason = choice.get("finish_reason")

        content = message.get("content")
        raw_tool_calls = message.get("tool_calls") or []

        tool_call_requests: list[LLMToolCallRequest] = []
        for raw_tc in raw_tool_calls:
            fn = raw_tc.get("function", {})
            fn_name = fn.get("name", "")
            raw_args = fn.get("arguments", "{}")
            try:
                parsed_args = (
                    json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                )
            except json.JSONDecodeError:
                parsed_args = {}
            tool_call_requests.append(
                LLMToolCallRequest(
                    id=raw_tc.get("id", ""),
                    function_name=fn_name,
                    arguments=parsed_args if isinstance(parsed_args, dict) else {},
                )
            )

        return LLMCompletionResult(
            provider=self.provider_name,
            model=model,
            content=content,
            tool_calls=tool_call_requests,
            finish_reason=finish_reason,
            error=None,
        )

    def stream_complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
    ):
        """Yield content delta strings as they stream from OpenRouter."""
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        payload: dict[str, Any] = {
            "model": settings.openrouter_model,
            "temperature": temperature,
            "stream": True,
            "messages": [msg.to_api_dict() for msg in messages],
        }

        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://stocky.local",
            "X-Title": settings.openrouter_app_name,
        }

        with httpx.Client(
            base_url=settings.openrouter_base_url, timeout=120.0
        ) as client:
            with client.stream(
                "POST", "/chat/completions", json=payload, headers=headers
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content_piece = delta.get("content")
                        if content_piece:
                            yield content_piece
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue
