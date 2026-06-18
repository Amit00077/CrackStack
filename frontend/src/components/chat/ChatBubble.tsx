import type { ChatMessage } from "../../types/chat";

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex items-end gap-3 ${isUser ? "justify-end" : "justify-start"} animate-fade-in-up`}>
      {!isUser && (
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-primary text-white shadow-sm shadow-primary-500/20 text-xs font-bold">
          AI
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-gradient-primary text-white rounded-br-sm shadow-md shadow-primary-500/20"
            : "bg-white border border-surface-100 text-surface-900 rounded-bl-sm shadow-soft"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm leading-relaxed">
          {message.content}
        </p>
        <p
          className={`mt-1.5 text-right text-[10px] font-medium ${
            isUser ? "text-white/60" : "text-surface-400"
          }`}
        >
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
      {isUser && (
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-surface-800 text-white text-xs font-bold shadow-sm">
          U
        </div>
      )}
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex items-end gap-3 animate-fade-in">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-primary text-white shadow-sm shadow-primary-500/20 text-xs font-bold">
        AI
      </div>
      <div className="rounded-2xl rounded-bl-sm bg-white border border-surface-100 px-4 py-3.5 shadow-soft">
        <div className="flex gap-1.5">
          <span className="h-2 w-2 animate-bounce rounded-full bg-primary-400 [animation-delay:0ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-primary-400 [animation-delay:150ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-primary-400 [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}
