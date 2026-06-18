import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "outline";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  children: ReactNode;
}

const variants = {
  primary:
    "bg-gradient-primary text-white shadow-sm shadow-primary-500/20 hover:shadow-md hover:shadow-primary-500/30 active:shadow-sm active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-primary-500/40 focus-visible:ring-offset-2 ring-offset-white",
  secondary:
    "bg-surface-100 text-surface-700 hover:bg-surface-200 hover:text-surface-900 active:bg-surface-300 focus-visible:ring-2 focus-visible:ring-surface-400/30 focus-visible:ring-offset-2 ring-offset-white",
  ghost:
    "bg-transparent text-surface-600 hover:bg-surface-100 hover:text-surface-900 active:bg-surface-200 focus-visible:ring-2 focus-visible:ring-surface-400/30",
  danger:
    "bg-gradient-danger text-white shadow-sm shadow-rose-500/20 hover:shadow-md hover:shadow-rose-500/30 active:shadow-sm active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-rose-500/40 focus-visible:ring-offset-2 ring-offset-white",
  outline:
    "border border-surface-200 bg-white text-surface-700 hover:border-primary-300 hover:text-primary-700 hover:bg-primary-50/50 active:bg-primary-50 focus-visible:ring-2 focus-visible:ring-primary-500/30 focus-visible:ring-offset-2 ring-offset-white",
};

const sizes = {
  sm: "px-3.5 py-2 text-xs font-medium gap-1.5",
  md: "px-5 py-2.5 text-sm font-semibold gap-2",
  lg: "px-7 py-3.5 text-base font-semibold gap-2.5",
};

export function Button({
  variant = "primary",
  size = "md",
  isLoading = false,
  disabled,
  children,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || isLoading}
      className={`inline-flex items-center justify-center rounded-xl font-semibold transition-all duration-200 ease-spring disabled:cursor-not-allowed disabled:opacity-50 disabled:scale-100 ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {isLoading && (
        <svg
          className="h-4 w-4 animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
