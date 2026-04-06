import { cn } from "./StatusBadge";

export function ProgressBar({
  value,
  max,
  threshold,
  className,
}: {
  value: number;
  max: number;
  threshold: number;
  className?: string;
}) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const isCritical = value <= threshold;

  return (
    <div className={cn("flex flex-col gap-1 w-full", className)}>
      <div className="flex justify-between text-xs text-gray-500 font-medium">
        <span>
          {value} / {max}
        </span>
        {isCritical && <span className="text-red-500">Low</span>}
      </div>
      <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300",
            isCritical ? "bg-red-500" : "bg-green-500",
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
