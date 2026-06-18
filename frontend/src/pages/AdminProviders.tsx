import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminApi, type AIProvider } from "../api/admin";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { useToast } from "../components/ui/Toast";

const PROVIDER_LOGOS: Record<string, string> = {
  groq: "⚡",
  openai: "🤖",
  claude: "🟣",
  deepseek: "🔍",
  gemini: "🔮",
};

function ActiveBadge({ active }: { active: boolean }) {
  return active ? (
    <span className="badge-success">Active</span>
  ) : (
    <span className="badge-secondary">Inactive</span>
  );
}

function EnabledBadge({ enabled }: { enabled: boolean }) {
  return enabled ? (
    <span className="badge-primary">Enabled</span>
  ) : (
    <span className="badge-warning">Disabled</span>
  );
}

export function AdminProviders() {
  const toast = useToast();
  const queryClient = useQueryClient();

  const [editProvider, setEditProvider] = useState<AIProvider | null>(null);
  const [editForm, setEditForm] = useState({
    api_key: "",
    base_url: "",
    active_model: "",
    models: "",
    is_enabled: true,
  });

  const { data: providersData, isLoading } = useQuery({
    queryKey: ["admin-providers"],
    queryFn: adminApi.listProviders,
  });

  const providers = providersData?.items ?? [];

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      adminApi.updateProvider(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-providers"] });
      toast.success("Provider updated");
      setEditProvider(null);
    },
    onError: () => toast.error("Failed to update provider"),
  });

  const setActiveMutation = useMutation({
    mutationFn: (provider_id: string) =>
      adminApi.setActiveProvider({ provider_id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-providers"] });
      toast.success("Active provider changed");
    },
    onError: () => toast.error("Failed to set active provider"),
  });

  function handleEdit(provider: AIProvider) {
    setEditProvider(provider);
    setEditForm({
      api_key: "",
      base_url: provider.base_url || "",
      active_model: provider.active_model,
      models: provider.models.join(", "),
      is_enabled: provider.is_enabled,
    });
  }

  function handleSave() {
    if (!editProvider) return;
    const data: Record<string, unknown> = {};
    if (editForm.api_key.trim()) data.api_key = editForm.api_key.trim();
    if (editForm.base_url.trim()) data.base_url = editForm.base_url.trim();
    data.active_model = editForm.active_model.trim();
    data.models = editForm.models.split(",").map((m) => m.trim()).filter(Boolean);
    data.is_enabled = editForm.is_enabled;
    updateMutation.mutate({ id: editProvider.id, data });
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-in">
      <div>
        <h2 className="section-title">AI Providers</h2>
        <p className="section-subtitle">
          Manage your AI provider configurations. The active provider is used for all AI features.
        </p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
        </div>
      ) : (
        <div className="grid gap-4">
          {providers.map((provider) => (
            <div
              key={provider.id}
              className={`card p-5 transition-all duration-200 ${
                provider.is_active
                  ? "ring-2 ring-primary-400 shadow-lg shadow-primary-500/10"
                  : "hover:shadow-md"
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0 flex-1">
                  <span className="text-2xl flex-shrink-0 mt-0.5">
                    {PROVIDER_LOGOS[provider.name] || "🤖"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-base font-bold text-surface-900">
                        {provider.display_name}
                      </h3>
                      <ActiveBadge active={provider.is_active} />
                      <EnabledBadge enabled={provider.is_enabled} />
                    </div>
                    <div className="mt-1.5 space-y-1 text-sm text-surface-500">
                      <p>
                        <span className="font-medium text-surface-700">Model:</span>{" "}
                        {provider.active_model}
                      </p>
                      <p>
                        <span className="font-medium text-surface-700">API Key:</span>{" "}
                        <span className="font-mono text-xs">{provider.api_key_preview}</span>
                      </p>
                      {provider.base_url && (
                        <p className="truncate">
                          <span className="font-medium text-surface-700">Base URL:</span>{" "}
                          {provider.base_url}
                        </p>
                      )}
                      <p>
                        <span className="font-medium text-surface-700">Models:</span>{" "}
                        {provider.models.length > 0
                          ? provider.models.join(", ")
                          : "Not configured"}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {!provider.is_active && provider.is_enabled && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setActiveMutation.mutate(provider.id)}
                      isLoading={setActiveMutation.isPending}
                    >
                      Activate
                    </Button>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleEdit(provider)}
                  >
                    Edit
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {editProvider && (
        <Modal
          open={true}
          onClose={() => setEditProvider(null)}
          title={`Edit ${editProvider.display_name}`}
        >
          <div className="space-y-4">

            <div>
              <label className="label">API Key</label>
              <input
                value={editForm.api_key}
                onChange={(e) => setEditForm({ ...editForm, api_key: e.target.value })}
                className="input-field"
                placeholder="Leave empty to keep current key"
                type="password"
              />
              <p className="mt-1 text-xs text-surface-400">
                Current: {editProvider.api_key_preview} — enter a new key to change it
              </p>
            </div>

            <div>
              <label className="label">Base URL</label>
              <input
                value={editForm.base_url}
                onChange={(e) => setEditForm({ ...editForm, base_url: e.target.value })}
                className="input-field"
                placeholder="https://api.openai.com/v1"
              />
            </div>

            <div>
              <label className="label">Active Model</label>
              <input
                value={editForm.active_model}
                onChange={(e) => setEditForm({ ...editForm, active_model: e.target.value })}
                className="input-field"
                placeholder="gpt-4o-mini"
              />
            </div>

            <div>
              <label className="label">Models (comma-separated)</label>
              <input
                value={editForm.models}
                onChange={(e) => setEditForm({ ...editForm, models: e.target.value })}
                className="input-field"
                placeholder="gpt-4o, gpt-4o-mini"
              />
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setEditForm({ ...editForm, is_enabled: !editForm.is_enabled })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-200 ${
                  editForm.is_enabled ? "bg-gradient-primary shadow-sm shadow-primary-500/20" : "bg-surface-200"
                }`}
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${
                    editForm.is_enabled ? "translate-x-[22px]" : "translate-x-[2px]"
                  }`}
                />
              </button>
              <span className="text-sm font-medium text-surface-700">Enabled</span>
            </div>

            <div className="flex gap-3 pt-2">
              <Button
                variant="primary"
                onClick={handleSave}
                isLoading={updateMutation.isPending}
              >
                Save Changes
              </Button>
              <Button variant="ghost" onClick={() => setEditProvider(null)}>
                Cancel
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
