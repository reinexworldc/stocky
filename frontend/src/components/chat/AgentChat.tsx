import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowUp } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { api } from "../../lib/api";
import type { ChatResponse } from "../../lib/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ChatRole = "assistant" | "user";

interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  renderedText?: string;
  toolCalls?: ChatResponse["tool_calls"];
  error?: boolean;
  streaming?: boolean;
}

// ---------------------------------------------------------------------------
// Quick prompts
// ---------------------------------------------------------------------------

const QUICK_PROMPTS = [
  "What to order this week?",
  "Dead stock report",
  "Catalog overview",
  "Forecast demand",
];

const THINKING_LINES = [
  "Stocky is analyzing data",
  "Checking stock levels and movement",
  "Compiling recommendations",
];

const STICKY_BOTTOM_THRESHOLD = 96;

// ---------------------------------------------------------------------------
// Drip-feed streaming: tokens arrive fast but are revealed gradually
// ---------------------------------------------------------------------------

/** How many characters to reveal per drip tick */
const DRIP_CHARS_PER_TICK = 2;
/** Interval between drip ticks (ms) — lower = faster typing effect */
const DRIP_INTERVAL_MS = 18;
/** How often to flush renderedText to trigger markdown re-render (ms) */
const MARKDOWN_RENDER_THROTTLE_MS = 80;
/** Scroll-to-bottom throttle during streaming (ms) */
const SCROLL_THROTTLE_MS = 100;

// ---------------------------------------------------------------------------
// Markdown renderer with custom components
// ---------------------------------------------------------------------------

const REMARK_PLUGINS = [remarkGfm];

function MarkdownRenderer({ content }: { content: string }) {
  const normalizedContent = useMemo(
    () => content.replace(/\n{3,}/g, "\n\n").trim(),
    [content],
  );

  return (
    <ReactMarkdown
      remarkPlugins={REMARK_PLUGINS}
      components={{
        h3: ({ children }) => (
          <h3 className="mt-4 mb-2 text-[14px] font-semibold text-gray-900 first:mt-0">
            {children}
          </h3>
        ),
        h4: ({ children }) => (
          <h4 className="mt-3 mb-1.5 text-[14px] font-semibold text-gray-700 first:mt-0">
            {children}
          </h4>
        ),
        p: ({ children }) => (
          <p className="mb-2 last:mb-0 text-[14px] leading-relaxed text-gray-800">
            {children}
          </p>
        ),
        ul: ({ children }) => (
          <ul className="mb-2 ml-4 list-disc space-y-1 text-[14px] leading-relaxed text-gray-800 last:mb-0">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="mb-2 ml-4 list-decimal space-y-1 text-[14px] leading-relaxed text-gray-800 last:mb-0">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="pl-1 text-[14px] leading-relaxed">{children}</li>
        ),
        strong: ({ children }) => (
          <strong className="font-semibold text-gray-900">{children}</strong>
        ),
        em: ({ children }) => (
          <em className="text-gray-600">{children}</em>
        ),
        code: ({ children, className }) => {
          const isBlock = className?.includes("language-");
          if (isBlock) {
            return (
              <code className="block overflow-x-auto rounded-lg bg-gray-100 p-3 text-[13px] leading-relaxed text-gray-800 font-mono">
                {children}
              </code>
            );
          }
          return (
            <code className="rounded bg-gray-100 px-1.5 py-0.5 text-[13px] font-medium text-gray-800 font-mono">
              {children}
            </code>
          );
        },
        pre: ({ children }) => (
          <pre className="mb-2 last:mb-0">{children}</pre>
        ),
        blockquote: ({ children }) => (
          <blockquote className="mb-2 border-l-[3px] border-amber-400 bg-amber-50/50 py-2 pl-4 pr-3 text-[14px] leading-relaxed text-amber-900 rounded-r-lg last:mb-0">
            {children}
          </blockquote>
        ),
        table: ({ children }) => (
          <div className="mb-2 overflow-x-auto rounded-lg border border-gray-200 last:mb-0">
            <table className="w-full text-[13px]">{children}</table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-gray-50 text-left text-gray-600 font-medium">
            {children}
          </thead>
        ),
        th: ({ children }) => (
          <th className="px-3 py-2 font-medium">{children}</th>
        ),
        td: ({ children }) => (
          <td className="border-t border-gray-100 px-3 py-2 text-gray-800">
            {children}
          </td>
        ),
        hr: () => <hr className="my-3 border-gray-200" />,
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline decoration-blue-300 underline-offset-2 hover:text-blue-700 hover:decoration-blue-400"
          >
            {children}
          </a>
        ),
      }}
    >
      {normalizedContent}
    </ReactMarkdown>
  );
}

// ---------------------------------------------------------------------------
// Streaming cursor — smooth blink via custom CSS keyframes
// ---------------------------------------------------------------------------

function StreamingCursor() {
  return (
    <span className="streaming-cursor inline-block w-[2px] h-[1.1em] bg-gray-900 align-middle ml-0.5 rounded-full" />
  );
}

// ---------------------------------------------------------------------------
// Bubbles
// ---------------------------------------------------------------------------

function AssistantBubble({ message }: { message: ChatMessage }) {
  const mdClass = message.streaming
    ? "agent-markdown is-streaming max-w-none"
    : "agent-markdown max-w-none";

  return (
    <div className="flex gap-4 items-start w-full group">
      <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-900 text-white shadow-sm ring-1 ring-gray-900/5">
        <span className="text-[10px] font-semibold tracking-[0.14em]">ST</span>
      </div>
      <div className="min-w-0 flex-1 space-y-4">
        {(message.text || message.streaming) && (
          <div className={mdClass}>
            <MarkdownRenderer content={message.renderedText ?? message.text} />
            {message.streaming && <StreamingCursor />}
          </div>
        )}
      </div>
    </div>
  );
}

function UserBubble({ message }: { message: ChatMessage }) {
  return (
    <div className="flex justify-end gap-3 items-start w-full group">
      <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-gray-900 px-5 py-3.5 text-[14px] leading-relaxed text-white shadow-sm">
        {message.text}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Thinking indicator
// ---------------------------------------------------------------------------

function ThinkingIndicator({ step }: { step: number }) {
  return (
    <div className="w-full animate-in fade-in duration-300">
      <div
        key={step}
        className="text-[13px] font-medium text-gray-500 animate-pulse"
      >
        {THINKING_LINES[step % THINKING_LINES.length]}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function AgentChat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [thinkingStep, setThinkingStep] = useState(0);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const shouldStickToBottomRef = useRef(true);

  // ---- Drip-feed refs ----
  /** Full text received so far from SSE (ground truth) */
  const fullTextRef = useRef("");
  /** How many characters of fullText have been "revealed" so far */
  const revealedIndexRef = useRef(0);
  /** The drip interval id */
  const dripIntervalRef = useRef<number | null>(null);
  /** Markdown render throttle timer */
  const mdRenderTimerRef = useRef<number | null>(null);
  /** Scroll throttle timer */
  const scrollTimerRef = useRef<number | null>(null);
  /** Whether the SSE stream has finished */
  const streamDoneRef = useRef(false);
  /** Current assistant message id being streamed */
  const currentMsgIdRef = useRef<string | null>(null);

  const canSend = input.trim().length > 0 && !loading;

  // ---- Scroll helpers ----
  const scrollToBottom = useCallback((behavior: ScrollBehavior = "auto") => {
    messagesEndRef.current?.scrollIntoView({ behavior, block: "end" });
  }, []);

  const throttledScroll = useCallback(() => {
    if (scrollTimerRef.current !== null) return;
    scrollTimerRef.current = window.setTimeout(() => {
      scrollTimerRef.current = null;
      if (shouldStickToBottomRef.current) {
        requestAnimationFrame(() => scrollToBottom("auto"));
      }
    }, SCROLL_THROTTLE_MS);
  }, [scrollToBottom]);

  const handleMessagesScroll = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;
    shouldStickToBottomRef.current = distanceFromBottom < STICKY_BOTTOM_THRESHOLD;
  }, []);

  // ---- Drip-feed engine ----

  /** Flush current revealed text into renderedText for markdown rendering */
  const flushRenderedText = useCallback((msgId: string, text: string) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === msgId ? { ...msg, renderedText: text } : msg,
      ),
    );
    throttledScroll();
  }, [throttledScroll]);

  /** Start the drip interval that gradually reveals characters */
  const startDrip = useCallback((msgId: string) => {
    if (dripIntervalRef.current !== null) return; // already running

    dripIntervalRef.current = window.setInterval(() => {
      const full = fullTextRef.current;
      const idx = revealedIndexRef.current;

      if (idx >= full.length) {
        // Caught up with all received tokens
        if (streamDoneRef.current) {
          // Stream is done and we revealed everything — finalize
          window.clearInterval(dripIntervalRef.current!);
          dripIntervalRef.current = null;

          if (mdRenderTimerRef.current !== null) {
            window.clearTimeout(mdRenderTimerRef.current);
            mdRenderTimerRef.current = null;
          }

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === msgId
                ? { ...msg, streaming: false, renderedText: msg.text }
                : msg,
            ),
          );
          return;
        }
        // Stream still going — just wait for more tokens
        return;
      }

      // Adaptive speed: if buffer is growing large, reveal more chars per tick
      // to avoid lagging far behind the LLM. The base is DRIP_CHARS_PER_TICK (2),
      // and it scales up gently when the unrevealed backlog exceeds ~60 chars.
      const backlog = full.length - idx;
      const adaptiveChars = backlog > 120
        ? Math.min(8, DRIP_CHARS_PER_TICK + Math.floor(backlog / 40))
        : backlog > 60
          ? DRIP_CHARS_PER_TICK + 1
          : DRIP_CHARS_PER_TICK;

      const charsToReveal = Math.min(adaptiveChars, backlog);
      const newIdx = idx + charsToReveal;
      revealedIndexRef.current = newIdx;

      const revealed = full.slice(0, newIdx);

      // Update the message text (invisible — source of truth for revealed portion)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === msgId ? { ...msg, text: revealed } : msg,
        ),
      );

      // Throttle markdown re-renders
      if (mdRenderTimerRef.current === null) {
        mdRenderTimerRef.current = window.setTimeout(() => {
          mdRenderTimerRef.current = null;
          flushRenderedText(msgId, fullTextRef.current.slice(0, revealedIndexRef.current));
        }, MARKDOWN_RENDER_THROTTLE_MS);
      }
    }, DRIP_INTERVAL_MS);
  }, [flushRenderedText]);

  /** Stop the drip engine and clean up timers */
  const stopDrip = useCallback(() => {
    if (dripIntervalRef.current !== null) {
      window.clearInterval(dripIntervalRef.current);
      dripIntervalRef.current = null;
    }
    if (mdRenderTimerRef.current !== null) {
      window.clearTimeout(mdRenderTimerRef.current);
      mdRenderTimerRef.current = null;
    }
    if (scrollTimerRef.current !== null) {
      window.clearTimeout(scrollTimerRef.current);
      scrollTimerRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopDrip();
  }, [stopDrip]);

  // Scroll when messages change (non-streaming)
  useEffect(() => {
    const latestAssistant = [...messages].reverse().find((msg) => msg.role === "assistant");
    if (!latestAssistant) return;
    if (!shouldStickToBottomRef.current) return;
    if (latestAssistant.streaming) return; // drip handles scrolling during stream

    requestAnimationFrame(() => scrollToBottom("smooth"));
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (!thinking) return;
    const interval = window.setInterval(() => {
      setThinkingStep((prev) => prev + 1);
    }, 1400);
    return () => window.clearInterval(interval);
  }, [thinking]);

  // Auto-resize textarea
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value);
      const el = e.target;
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
    },
    [],
  );

  const sendMessage = useCallback(
    async (rawMessage: string) => {
      const message = rawMessage.trim();
      if (!message || loading) return;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        text: message,
      };
      shouldStickToBottomRef.current = true;
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);
      setThinking(true);
      setThinkingStep(0);

      // Reset textarea height
      if (inputRef.current) {
        inputRef.current.style.height = "auto";
      }

      const assistantMsgId = `assistant-${Date.now()}`;
      currentMsgIdRef.current = assistantMsgId;

      // Reset drip state
      fullTextRef.current = "";
      revealedIndexRef.current = 0;
      streamDoneRef.current = false;
      stopDrip();

      try {
        await api.chatStream(message, conversationId, {
          onMeta: (meta) => {
            setConversationId(meta.conversation_id);
            setThinking(false);

            // Create assistant message placeholder
            setMessages((prev) => [
              ...prev,
              {
                id: assistantMsgId,
                role: "assistant",
                text: "",
                renderedText: "",
                toolCalls: meta.tool_calls,
                streaming: true,
              },
            ]);

            // Start the drip engine
            startDrip(assistantMsgId);
          },
          onToken: (token) => {
            // Just accumulate into the buffer — drip engine reveals gradually
            fullTextRef.current += token;
          },
          onDone: () => {
            // Signal drip engine that no more tokens are coming
            streamDoneRef.current = true;

            // If drip already caught up (e.g. very short response), finalize now
            if (revealedIndexRef.current >= fullTextRef.current.length) {
              stopDrip();
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? {
                        ...msg,
                        text: fullTextRef.current,
                        renderedText: fullTextRef.current,
                        streaming: false,
                      }
                    : msg,
                ),
              );
            }

            setLoading(false);
            setThinking(false);
          },
          onError: (error) => {
            setThinking(false);
            streamDoneRef.current = true;
            stopDrip();

            setMessages((prev) => {
              const hasAssistant = prev.some((m) => m.id === assistantMsgId);
              if (hasAssistant) {
                return prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? {
                        ...msg,
                        text: msg.text || error,
                        renderedText: msg.text || error,
                        streaming: false,
                        error: true,
                      }
                    : msg,
                );
              }
              return [
                ...prev,
                {
                  id: assistantMsgId,
                  role: "assistant" as const,
                  text: error,
                  renderedText: error,
                  error: true,
                },
              ];
            });
            setLoading(false);
          },
        });
      } catch (error) {
        setThinking(false);
        streamDoneRef.current = true;
        stopDrip();

        setMessages((prev) => [
          ...prev,
          {
            id: assistantMsgId,
            role: "assistant",
            text:
              error instanceof Error
                ? error.message
                : "Failed to get a response from the assistant.",
            renderedText:
              error instanceof Error
                ? error.message
                : "Failed to get a response from the assistant.",
            error: true,
          },
        ]);
        setLoading(false);
      }
    },
    [conversationId, loading, startDrip, stopDrip],
  );

  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden bg-gray-50/30 font-sans">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200/60 bg-white z-10">
        <div className="flex flex-col">
          <span className="text-[14px] font-bold text-gray-900 tracking-tight">Stocky</span>
          <span className="text-[12px] text-gray-500 font-medium">
            {loading ? "Analyzing..." : "Online"}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={messagesContainerRef}
        onScroll={handleMessagesScroll}
        className="flex-1 overflow-y-auto p-6 scrollbar-hide space-y-6 flex flex-col items-center"
      >
        {messages.length === 0 && !loading && (
          <div className="mt-4 mb-4 flex w-full max-w-2xl flex-col items-center text-center space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="max-w-xl space-y-1">
              <h2 className="text-lg font-semibold leading-tight text-gray-900 tracking-tight">
                Hi, I'm Stocky
              </h2>
              <p className="text-[13px] leading-relaxed text-gray-500">
                Ask about stock levels, demand, dead stock, or purchase plans.
              </p>
            </div>

            <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => void sendMessage(prompt)}
                  className="flex min-h-[48px] items-center rounded-xl border border-gray-200 bg-white px-4 py-3 text-left text-[14px] font-medium text-gray-700 transition-all shadow-sm hover:border-gray-300 hover:bg-gray-50 hover:shadow active:scale-[0.98]"
                >
                  <span className="leading-snug">{prompt}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) =>
          msg.role === "assistant" ? (
            <div key={msg.id} className="w-full max-w-4xl animate-in fade-in duration-300">
              <AssistantBubble message={msg} />
            </div>
          ) : (
            <div key={msg.id} className="w-full max-w-4xl animate-in fade-in duration-300">
              <UserBubble message={msg} />
            </div>
          ),
        )}

        {thinking && (
          <div className="w-full max-w-4xl">
             <ThinkingIndicator step={thinkingStep} />
          </div>
        )}

        <div ref={messagesEndRef} className="h-4" />
      </div>

      {/* Input */}
      <div className="bg-white p-4 pb-6 relative z-10 border-t border-gray-200/60">
        <div className="mx-auto max-w-4xl">
          <div className="relative flex items-end gap-2 rounded-xl border border-gray-300 bg-white p-1.5 focus-within:border-gray-900 focus-within:ring-1 focus-within:ring-gray-900 transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void sendMessage(input);
                }
              }}
              placeholder="Ask anything..."
              rows={1}
              className="flex-1 resize-none bg-transparent px-3 py-2 text-[14px] text-gray-900 placeholder:text-gray-400 focus:outline-none leading-relaxed max-h-[160px] min-h-[38px]"
            />
            <button
              onClick={() => void sendMessage(input)}
              disabled={!canSend}
              className="mb-0.5 mr-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gray-900 text-white transition-all hover:bg-gray-800 hover:shadow-sm active:scale-95 disabled:bg-gray-100 disabled:text-gray-400 disabled:shadow-none"
            >
              <ArrowUp className="h-4 w-4" strokeWidth={2} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
