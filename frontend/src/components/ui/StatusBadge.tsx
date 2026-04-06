import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import type { StatusType } from "../../lib/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const statusColors: Record<
  StatusType,
  { bg: string; text: string; dot: string; label: string }
> = {
  critical: {
    bg: "bg-red-50",
    text: "text-red-700",
    dot: "bg-red-500",
    label: "Critical",
  },
  warning: {
    bg: "bg-yellow-50",
    text: "text-yellow-700",
    dot: "bg-yellow-500",
    label: "Warning",
  },
  ok: {
    bg: "bg-green-50",
    text: "text-green-700",
    dot: "bg-green-500",
    label: "Normal",
  },
  dead_stock: {
    bg: "bg-gray-100",
    text: "text-gray-700",
    dot: "bg-gray-500",
    label: "Dead stock",
  },
  overstock: {
    bg: "bg-blue-50",
    text: "text-blue-700",
    dot: "bg-blue-500",
    label: "Overstock",
  },
};

export const StatusBadge = ({
  status,
  className,
}: {
  status: StatusType;
  className?: string;
}) => {
  const color = statusColors[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-medium",
        color.bg,
        color.text,
        className,
      )}
    >
      <span
        className={cn("h-1.5 w-1.5 rounded-full", color.dot)}
        aria-hidden="true"
      />
      {color.label}
    </span>
  );
};
