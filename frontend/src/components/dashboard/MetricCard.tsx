import type { ReactNode } from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  trend?: { value: number; isUp: boolean };
  color?: "primary" | "green" | "yellow" | "red";
}

const gradients: Record<string, string> = {
  primary: "from-primary-500/10 via-primary-500/5 to-transparent",
  green: "from-emerald-500/10 via-emerald-500/5 to-transparent",
  yellow: "from-amber-500/10 via-amber-500/5 to-transparent",
  red: "from-rose-500/10 via-rose-500/5 to-transparent",
};

const iconBgs: Record<string, string> = {
  primary: "bg-gradient-primary shadow-primary-500/20",
  green: "bg-gradient-success shadow-emerald-500/20",
  yellow: "bg-gradient-accent shadow-amber-500/20",
  red: "bg-gradient-danger shadow-rose-500/20",
};

const trendColors: Record<string, string> = {
  primary: "text-primary-600 bg-primary-50",
  green: "text-emerald-600 bg-emerald-50",
  yellow: "text-amber-600 bg-amber-50",
  red: "text-rose-600 bg-rose-50",
};

const valueColors: Record<string, string> = {
  primary: "text-primary-600",
  green: "text-emerald-600",
  yellow: "text-amber-600",
  red: "text-rose-600",
};

export function MetricCard({
  title,
  value,
  icon,
  trend,
  color = "primary",
}: MetricCardProps) {
  return (
    <div className="group relative overflow-hidden rounded-2xl bg-white border border-surface-100 shadow-soft hover:shadow-elevated transition-all duration-300 hover:-translate-y-0.5">
      <div className={`absolute inset-0 bg-gradient-to-br ${gradients[color]} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
      <div className="relative p-5 sm:p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-surface-500">
              {title}
            </p>
            <p className={`text-2xl sm:text-3xl font-bold tracking-tight ${valueColors[color]}`}>
              {value}
            </p>
            {trend && (
              <div className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${trendColors[color]}`}>
                <svg
                  className={`h-3 w-3 ${trend.isUp ? "" : "rotate-180"}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
                <span>{trend.isUp ? "+" : "-"}{Math.abs(trend.value)}%</span>
              </div>
            )}
          </div>
          <div className={`flex h-12 w-12 items-center justify-center rounded-2xl text-white shadow-lg ${iconBgs[color]} group-hover:scale-110 group-hover:rotate-3 transition-all duration-300`}>
            {icon}
          </div>
        </div>
      </div>
    </div>
  );
}
