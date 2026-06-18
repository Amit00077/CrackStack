import type { ChatSession, ChatMessage, ChatRequest, ChatResponse } from "../types/chat";
import { client } from "./client";

export const chatApi = {
  sendMessage: (data: ChatRequest) =>
    client.post<ChatResponse>("/chat/message", data).then((r) => r.data),

  getSessions: () =>
    client.get<ChatSession[]>("/chat/sessions").then((r) => r.data),

  getSession: (id: string) =>
    client.get<ChatSession & { messages: ChatMessage[] }>(`/chat/sessions/${id}`).then((r) => r.data),

  deleteSession: (id: string) =>
    client.delete(`/chat/sessions/${id}`).then((r) => r.data),
};
