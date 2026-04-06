"""In-memory conversation store with TTL-based expiration.

Each conversation is identified by a UUID. The store keeps the last N
messages per conversation and automatically evicts stale sessions.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

MAX_MESSAGES_PER_CONVERSATION = 50
MAX_CONVERSATIONS = 200
CONVERSATION_TTL_SECONDS = 60 * 60  # 1 hour


@dataclass
class ConversationEntry:
    role: str
    content: str | None = None
    tool_calls_raw: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class Conversation:
    id: str
    messages: list[ConversationEntry] = field(default_factory=list)
    last_resolved_sku: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class ConversationStore:
    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}
        self._lock = threading.Lock()

    def create(self) -> Conversation:
        with self._lock:
            self._evict_stale()
            conversation = Conversation(id=str(uuid.uuid4()))
            self._conversations[conversation.id] = conversation
            return conversation

    def get(self, conversation_id: str) -> Conversation | None:
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation is None:
                return None
            if time.time() - conversation.updated_at > CONVERSATION_TTL_SECONDS:
                del self._conversations[conversation_id]
                return None
            return conversation

    def get_or_create(self, conversation_id: str | None) -> Conversation:
        if conversation_id:
            existing = self.get(conversation_id)
            if existing is not None:
                return existing
        return self.create()

    def append(self, conversation_id: str, entry: ConversationEntry) -> None:
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation is None:
                return
            conversation.messages.append(entry)
            conversation.updated_at = time.time()
            if len(conversation.messages) > MAX_MESSAGES_PER_CONVERSATION:
                overflow = len(conversation.messages) - MAX_MESSAGES_PER_CONVERSATION
                conversation.messages = conversation.messages[overflow:]

    def set_last_sku(self, conversation_id: str, sku: str | None) -> None:
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation is not None and sku is not None:
                conversation.last_resolved_sku = sku
                conversation.updated_at = time.time()

    def get_last_sku(self, conversation_id: str) -> str | None:
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation is None:
                return None
            return conversation.last_resolved_sku

    def _evict_stale(self) -> None:
        now = time.time()
        stale_keys = [
            key
            for key, conv in self._conversations.items()
            if now - conv.updated_at > CONVERSATION_TTL_SECONDS
        ]
        for key in stale_keys:
            del self._conversations[key]

        if len(self._conversations) >= MAX_CONVERSATIONS:
            sorted_convs = sorted(
                self._conversations.items(), key=lambda item: item[1].updated_at
            )
            to_remove = len(self._conversations) - MAX_CONVERSATIONS + 1
            for key, _ in sorted_convs[:to_remove]:
                del self._conversations[key]


# Singleton instance
store = ConversationStore()
