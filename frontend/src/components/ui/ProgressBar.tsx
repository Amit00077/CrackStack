interface ProgressBarProps {
  percentage: number;
  color?: "primary" | "green" | "yellow" | "red";
  label?: string;
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
}

const gradients: Record<string, string> = {
  primary: "bg-gradient-primary",
  green: "bg-gradient-success",
  yellow: "bg-gradient-accent",
  red: "bg-gradient-danger",
};

const sizeClasses = {
  sm: "h-2",
  md: "h-3",
  lg: "h-4",
};

export function ProgressBar({
  percentage,
  color = "primary",
  label,
  showLabel = false,
  size = "md",
}: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, percentage));

  return (
    <div className="w-full">
      {(label || showLabel) && (
        <div className="mb-1.5 flex items-center justify-between">
          {label && (
            <span className="text-xs font-medium text-surface-600">{label}</span>
          )}
          {showLabel && (
            <span className="text-xs font-semibold text-surface-500">{Math.round(clamped)}%</span>
          )}
        </div>
      )}
      <div className={`w-full overflow-hidden rounded-full bg-surface-100 ${sizeClasses[size]}`}>
        <div
          className={`${sizeClasses[size]} rounded-full transition-all duration-700 ease-smooth shadow-sm ${gradients[color]}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
