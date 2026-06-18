import { client } from "./client";

export interface AIProvider {
  id: string;
  name: string;
  display_name: string;
  api_key_preview: string;
  base_url: string | null;
  models: string[];
  active_model: string;
  is_active: boolean;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface AIProviderCreate {
  name: string;
  display_name: string;
  api_key: string;
  base_url?: string;
  models: string[];
  active_model: string;
  is_enabled?: boolean;
}

export interface AIProviderUpdate {
  display_name?: string;
  api_key?: string;
  base_url?: string;
  models?: string[];
  active_model?: string;
  is_enabled?: boolean;
}

export interface SetActiveProviderRequest {
  provider_id: string;
  active_model?: string;
}

interface AIProviderListResponse {
  items: AIProvider[];
}

export const adminApi = {
  listProviders: async (): Promise<AIProviderListResponse> => {
    const { data } = await client.get("/admin/providers");
    return data;
  },
  getProvider: async (id: string): Promise<AIProvider> => {
    const { data } = await client.get(`/admin/providers/${id}`);
    return data;
  },
  createProvider: async (body: AIProviderCreate): Promise<AIProvider> => {
    const { data } = await client.post("/admin/providers", body);
    return data;
  },
  updateProvider: async (id: string, body: AIProviderUpdate): Promise<AIProvider> => {
    const { data } = await client.put(`/admin/providers/${id}`, body);
    return data;
  },
  deleteProvider: async (id: string): Promise<void> => {
    await client.delete(`/admin/providers/${id}`);
  },
  setActiveProvider: async (body: SetActiveProviderRequest): Promise<AIProvider> => {
    const { data } = await client.post("/admin/providers/active", body);
    return data;
  },
  getActiveProvider: async (): Promise<AIProvider | null> => {
    const { data } = await client.get("/admin/providers/active/current");
    return data;
  },
};
