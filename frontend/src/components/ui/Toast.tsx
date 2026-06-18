import { create } from "zustand";
import { useCallback, useEffect, useState } from "react";

type ToastVariant = "success" | "error" | "info";

interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastStore {
  toasts: ToastItem[];
  addToast: (message: string, variant?: ToastVariant) => void;
  removeToast: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (message, variant = "info") => {
    const id = crypto.randomUUID();
    set((s) => ({ toasts: [...s.toasts, { id, message, variant }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 5000);
  },
  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

const variantStyles: Record<ToastVariant, string> = {
  success: "from-emerald-500 to-emerald-600 shadow-emerald-500/30",
  error: "from-rose-500 to-rose-600 shadow-rose-500/30",
  info: "from-primary-500 to-primary-600 shadow-primary-500/30",
};

const variantIcons: Record<ToastVariant, string> = {
  success: "M5 13l4 4L19 7",
  error: "M6 18L18 6M6 6l12 12",
  info: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
};

function ToastItem({ toast }: { toast: ToastItem }) {
  const removeToast = useToastStore((s) => s.removeToast);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  return (
    <div
      className={`flex items-center gap-3 rounded-2xl bg-gradient-to-r px-5 py-3.5 shadow-lg backdrop-blur-sm transition-all duration-300 ${variantStyles[toast.variant]} ${visible ? "translate-x-0 opacity-100" : "translate-x-full opacity-0"}`}
    >
      <svg className="h-5 w-5 flex-shrink-0 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={variantIcons[toast.variant]} />
      </svg>
      <span className="flex-1 text-sm font-medium text-white">{toast.message}</span>
      <button
        onClick={() => removeToast(toast.id)}
        className="flex h-6 w-6 items-center justify-center rounded-lg text-white/60 hover:bg-white/10 hover:text-white transition-all"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2.5 max-w-sm">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} />
      ))}
    </div>
  );
}

export function useToast() {
  const addToast = useToastStore((s) => s.addToast);
  const success = useCallback(
    (message: string) => addToast(message, "success"),
    [addToast],
  );
  const error = useCallback(
    (message: string) => addToast(message, "error"),
    [addToast],
  );
  const info = useCallback(
    (message: string) => addToast(message, "info"),
    [addToast],
  );
  return { success, error, info };
}
