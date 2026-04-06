import type {
  CatalogResponse,
  ChatResponse,
  DeadStockResponse,
  DeepDiveResponse,
  PurchaseOrderResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string): Promise<T> {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`);
  } catch (error) {
    throw new Error(`Connection failed. Make sure backend is running. Details: ${error instanceof Error ? error.message : "Unknown error"}`);
  }

  if (!response.ok) {
    let errorText = response.statusText;
    try {
      const data = await response.json();
      if (data.detail) errorText = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    } catch (e) {
      // ignore
    }
    throw new Error(`API request failed: ${response.status} ${errorText}`);
  }

  return response.json() as Promise<T>;
}

async function requestJson<T>(path: string, body: unknown): Promise<T> {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (error) {
    throw new Error(`Connection failed. Make sure backend is running. Details: ${error instanceof Error ? error.message : "Unknown error"}`);
  }

  if (!response.ok) {
    let errorText = response.statusText;
    try {
      const data = await response.json();
      if (data.detail) errorText = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    } catch (e) {
      // ignore
    }
    throw new Error(`API request failed: ${response.status} ${errorText}`);
  }

  return response.json() as Promise<T>;
}

export interface StreamCallbacks {
  onMeta: (meta: {
    conversation_id: string;
    resolved_sku: string | null;
    tool_calls: ChatResponse["tool_calls"];
  }) => void;
  onToken: (token: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

async function chatStream(
  message: string,
  conversationId: string | null,
  callbacks: StreamCallbacks,
): Promise<void> {
  const response = await fetch(`${API_BASE}/agent-tools/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });

  if (!response.ok || !response.body) {
    let errorText = response.statusText;
    try {
      const data = await response.json();
      if (data.detail)
        errorText =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
    } catch {
      // ignore
    }
    callbacks.onError(`API request failed: ${response.status} ${errorText}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const lines = part.split("\n");
      let eventType = "";
      let eventData = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7);
        } else if (line.startsWith("data: ")) {
          eventData = line.slice(6);
        }
      }

      if (!eventType) continue;

      switch (eventType) {
        case "meta":
          try {
            callbacks.onMeta(JSON.parse(eventData));
          } catch {
            // ignore parse errors
          }
          break;
        case "token":
          // Token data is JSON-encoded to preserve newlines in Markdown
          try {
            callbacks.onToken(JSON.parse(eventData));
          } catch {
            callbacks.onToken(eventData);
          }
          break;
        case "done":
          callbacks.onDone();
          break;
        case "error": {
          let errorMsg = eventData || "Unknown streaming error";
          try { errorMsg = JSON.parse(eventData); } catch { /* use raw */ }
          callbacks.onError(errorMsg);
          break;
        }
      }
    }
  }
}

export const api = {
  getCatalog: () => request<CatalogResponse>("/agent-tools/analyze-full-catalog"),
  getDeadStock: () => request<DeadStockResponse>("/agent-tools/flag-dead-stock"),
  getPurchasePlan: () =>
    request<PurchaseOrderResponse>("/agent-tools/build-purchase-order"),
  getDeepDive: (sku: string) =>
    request<DeepDiveResponse>(
      `/agent-tools/items/${encodeURIComponent(sku)}/deep-dive`,
    ),
  chat: (message: string, conversationId: string | null) =>
    requestJson<ChatResponse>("/agent-tools/chat", {
      message,
      conversation_id: conversationId,
    }),
  chatStream,
};
