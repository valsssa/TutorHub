interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  color?: "primary" | "white";
}

export default function LoadingSpinner({
  size = "md",
  color = "primary",
}: LoadingSpinnerProps) {
  const sizeClass = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  }[size];

  const colorClass = color === "white" 
    ? "border-white/30 border-t-white" 
    : "border-emerald-200 dark:border-emerald-800 border-t-emerald-600 dark:border-t-emerald-400";

  return (
    <div className="flex items-center justify-center" role="status" aria-label="Loading">
      <div
        className={`animate-spin rounded-full ${sizeClass} border-2 ${colorClass}`}
      ></div>
      <span className="sr-only">Loading...</span>
    </div>
  );
}
