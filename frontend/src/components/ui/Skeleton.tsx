interface SkeletonProps {
  variant?: "text" | "circle" | "rect";
  width?: string | number;
  height?: string | number;
  className?: string;
}

export function Skeleton({
  variant = "text",
  width,
  height,
  className = "",
}: SkeletonProps) {
  const base = "skeleton-pulse";

  if (variant === "circle") {
    return (
      <div
        className={`${base} rounded-full ${className}`}
        style={{
          width: width ?? 40,
          height: height ?? 40,
        }}
      />
    );
  }

  if (variant === "rect") {
    return (
      <div
        className={`${base} ${className}`}
        style={{
          width: width ?? "100%",
          height: height ?? 80,
        }}
      />
    );
  }

  return (
    <div
      className={`${base} rounded-lg ${className}`}
      style={{
        width: width ?? "100%",
        height: height ?? 16,
      }}
    />
  );
}
