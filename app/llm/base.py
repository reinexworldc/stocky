from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LLMMessage:
    role: str
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_api_dict(self) -> dict[str, Any]:
        msg: dict[str, Any] = {"role": self.role}
        if self.content is not None:
            msg["content"] = self.content
        if self.tool_calls is not None:
            msg["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            msg["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            msg["name"] = self.name
        return msg


@dataclass(slots=True)
class LLMToolCallRequest:
    id: str
    function_name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class LLMCompletionResult:
    provider: str
    model: str
    content: str | None = None
    tool_calls: list[LLMToolCallRequest] = field(default_factory=list)
    finish_reason: str | None = None
    error: str | None = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    provider_name: str

    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMCompletionResult:
        raise NotImplementedError

    def stream_complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
    ):
        """Yield content delta strings as they arrive from the LLM.

        Default implementation falls back to non-streaming complete().
        Subclasses may override for true token-level streaming.
        """
        result = self.complete(messages, temperature)
        if result.content:
            yield result.content
