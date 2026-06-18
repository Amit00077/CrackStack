import type { LoginRequest, RegisterRequest, TokenResponse, User } from "../types/auth";
import { client } from "./client";

export const authApi = {
  login: (data: LoginRequest) =>
    client.post<TokenResponse>("/auth/login", data).then((r) => r.data),

  register: (data: RegisterRequest) =>
    client.post<TokenResponse>("/auth/register", data).then((r) => r.data),

  refresh: (refreshToken: string) =>
    client
      .post<TokenResponse>("/auth/refresh", { refresh_token: refreshToken })
      .then((r) => r.data),

  getMe: () => client.get<User>("/users/me").then((r) => r.data),
};
