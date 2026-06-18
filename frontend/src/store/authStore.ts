import { create } from "zustand";

import { authApi } from "../api/auth";
import type { User } from "../types/auth";
import { queryClient } from "../main";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  setUser: (user: User | null) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  setUser: (user) =>
    set({ user, isAuthenticated: !!user, isLoading: false }),

  login: async (email, password) => {
    const tokens = await authApi.login({ email, password });
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    queryClient.clear();
    const user = await authApi.getMe();
    set({ user, isAuthenticated: true, isLoading: false });
  },

  register: async (email, password, fullName) => {
    const tokens = await authApi.register({ email, password, full_name: fullName });
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    queryClient.clear();
    const user = await authApi.getMe();
    set({ user, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    queryClient.clear();
    set({ user: null, isAuthenticated: false, isLoading: false });
  },

  loadUser: async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }
    try {
      const user = await authApi.getMe();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        queryClient.clear();
        set({ user: null, isAuthenticated: false, isLoading: false });
      } else {
        console.warn("loadUser non-auth error, keeping tokens:", err);
        set({ isLoading: false });
      }
    }
  },
}));
