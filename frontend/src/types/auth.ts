export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  auth_provider: string;
  auth_provider_id?: string;
  timezone?: string;
  created_at: string;
}

export interface UserUpdate {
  full_name?: string;
  avatar_url?: string;
  timezone?: string;
}
