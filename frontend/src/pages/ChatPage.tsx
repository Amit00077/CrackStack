import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { client } from "../api/client";
import { Button } from "../components/ui/Button";
import { ChatBubble, TypingIndicator } from "../components/chat/ChatBubble";
import type { ChatMessage, ChatSession } from "../types/chat";
import { goalsApi } from "../api/goals";

function generateQuickPrompts(goal: { target_role?: string; target_company?: string; goal_text?: string; weak_areas?: string[] } | null) {
  if (!goal) {
    return [
      "What should I study today?",
      "Explain system design concepts",
      "Give me a coding challenge",
      "How do I approach behavioral questions?",
      "Tips for time management",
      "Review my progress",
    ];
  }

  const role = goal.target_role || "your target role";
  const company = goal.target_company || "your target company";
  const weakAreas = goal.weak_areas?.join(", ") || "key topics";

  return [
    `What should I study today for ${role} at ${company}?`,
    `Create a study plan for ${role} interviews`,
    `Explain key ${weakAreas} concepts for ${role}`,
    `Give me a coding challenge relevant to ${role}`,
    `How to approach ${role} behavioral questions at ${company}?`,
    `Review my weak areas: ${weakAreas}`,
    `Tips for time management during ${role} prep`,
    `What are common ${role} interview questions at ${company}?`,
  ];
}

export function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: goal } = useQuery({
    queryKey: ["active-goal"],
    queryFn: goalsApi.getActiveGoal,
    retry: false,
  });

  const quickPrompts = useMemo(() => generateQuickPrompts(goal || null), [goal]);

  const { data: sessions } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: () =>
      client.get<ChatSession[]>("/chat/sessions").then((r) => r.data),
    retry: false,
  });

  const handleSend = useCallback(async () => {
    if (!input.trim() || isStreaming) return;
    const userContent = input.trim();
    setInput("");
    setIsStreaming(true);

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      session_id: sessionId || "",
      role: "user",
      content: userContent,
      extra_metadata: null,
      created_at: new Date().toISOString(),
    };
    const aiMsg: ChatMessage = {
      id: crypto.randomUUID(),
      session_id: sessionId || "",
      role: "assistant",
      content: "",
      extra_metadata: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg, aiMsg]);

    try {
      const token = localStorage.getItem("access_token");
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
      const response = await fetch(`${baseUrl}/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: userContent, session_id: sessionId }),
      });

      if (!response.ok || !response.body) {
        throw new Error("Failed to send message");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let currentSessionId = sessionId;
      let aiContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const parsed = JSON.parse(line.slice(6));
              if (parsed.type === "session_id") {
                currentSessionId = parsed.session_id;
                setSessionId(currentSessionId);
                setMessages((prev) =>
                  prev.map((m): ChatMessage =>
                    m.id === userMsg.id ? { ...m, session_id: currentSessionId || m.session_id } : m
                  )
                );
              } else if (parsed.type === "chunk") {
                aiContent += parsed.content;
                setMessages((prev) =>
                  prev.map((m): ChatMessage =>
                    m.id === aiMsg.id ? { ...m, content: aiContent, session_id: currentSessionId || m.session_id } : m
                  )
                );
              }
            } catch {
              /* skip malformed lines */
            }
          }
        }
      }
    } catch {
      setMessages((prev) => prev.filter((m) => m.id !== aiMsg.id && m.id !== userMsg.id));
    } finally {
      setIsStreaming(false);
    }
  }, [input, isStreaming, sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handlePrompt = (prompt: string) => {
    setInput(prompt);
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId(null);
    setInput("");
  };

  const handleArchive = async () => {
    if (!sessionId) return;
    try {
      await client.post(`/chat/sessions/${sessionId}/archive`);
      handleNewChat();
    } catch {
    }
  };

  const sessionList = sessions || [];

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4 animate-fade-in">
      <aside
        className={`fixed lg:relative inset-y-0 left-0 z-40 w-64 transform rounded-2xl border border-surface-100 bg-white p-4 shadow-soft transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-4">
          <Button size="sm" className="w-full" onClick={handleNewChat}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </Button>
        </div>
        {sessionList.length === 0 ? (
          <p className="text-center text-sm text-surface-400 py-8">No sessions yet</p>
        ) : (
          <div className="space-y-1">
            {sessionList.map((s) => (
              <button
                key={s.id}
                onClick={async () => {
                  setSessionId(s.id);
                  setSidebarOpen(false);
                  try {
                    const res = await client.get<{ messages: ChatMessage[] }>(
                      `/chat/sessions/${s.id}`,
                    );
                    setMessages(res.data.messages);
                  } catch {
                  }
                }}
                className={`w-full rounded-xl px-3 py-2.5 text-left text-sm transition-all duration-200 ${
                  s.id === sessionId
                    ? "bg-primary-50 text-primary-700 border border-primary-200"
                    : "text-surface-600 hover:bg-surface-50 border border-transparent"
                }`}
              >
                <p className="truncate font-medium">{s.title}</p>
                <p className="text-xs text-surface-400 mt-0.5">
                  {new Date(s.created_at).toLocaleDateString()}
                </p>
              </button>
            ))}
          </div>
        )}
      </aside>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 backdrop-blur-sm lg:hidden animate-fade-in"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex flex-1 flex-col rounded-2xl border border-surface-100 bg-white shadow-soft overflow-hidden">
        <div className="flex items-center justify-between border-b border-surface-100 px-5 py-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="flex h-8 w-8 items-center justify-center rounded-xl text-surface-500 hover:bg-surface-100 hover:text-surface-700 transition-all lg:hidden"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-primary text-white text-xs font-bold shadow-sm shadow-primary-500/20">
              AI
            </div>
            <h3 className="text-sm font-bold text-surface-900">
              {sessionId ? "AI Mentor" : "New Chat"}
            </h3>
          </div>
          {sessionId && (
            <button
              onClick={handleArchive}
              className="flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-semibold text-surface-500 hover:bg-surface-100 hover:text-surface-700 transition-all"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
              </svg>
              Archive
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4 scrollbar-thin">
          {messages.length === 0 && !isStreaming && (
            <div className="flex flex-col items-center justify-center h-full animate-fade-in">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-primary shadow-lg shadow-primary-500/20 mb-5">
                <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="mb-2 text-xl font-bold text-surface-900">
                AI Mentor
              </h3>
              <p className="mb-6 text-sm text-surface-500">
                Ask me anything about your preparation
              </p>
              <div className="flex flex-wrap justify-center gap-2 max-w-md">
                {quickPrompts.slice(0, 3).map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handlePrompt(prompt)}
                    className="rounded-xl border border-surface-200 px-4 py-2 text-xs font-medium text-surface-600 hover:border-primary-300 hover:text-primary-600 hover:bg-primary-50/50 transition-all duration-200"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg) => (
            <ChatBubble key={msg.id} message={msg} />
          ))}
          {isStreaming && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {messages.length > 0 && (
          <div className="border-t border-surface-100 px-5 py-3">
            <div className="flex flex-wrap gap-2">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handlePrompt(prompt)}
                  className="rounded-xl bg-surface-100 px-3 py-1.5 text-xs font-medium text-surface-600 hover:bg-surface-200 hover:text-surface-800 transition-all"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="border-t border-surface-100 p-4 sm:p-5">
          <div className="flex gap-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Type your message..."
              className="flex-1 rounded-xl border border-surface-200 bg-surface-50 px-4 py-3 text-sm text-surface-900 placeholder-surface-400 focus:border-primary-300 focus:ring-2 focus:ring-primary-500/20 focus:outline-none transition-all"
              disabled={isStreaming}
            />
            <Button
              onClick={handleSend}
              isLoading={isStreaming}
              disabled={!input.trim()}
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
