import { AlertTriangle, Archive, Tag } from "lucide-react";

import { formatCurrency, formatNumber, titleizeAction } from "../../lib/format";
import type { DeadStockItem } from "../../lib/types";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "border-red-200 bg-red-50 text-red-700",
  warning: "border-amber-200 bg-amber-50 text-amber-700",
  info: "border-blue-200 bg-blue-50 text-blue-700",
};

interface DeadStockCardProps {
  summary: { items_count: number; total_stock_value: number; critical_count: number; warning_count: number; info_count: number };
  items: DeadStockItem[];
}

export function DeadStockCard({ summary, items }: DeadStockCardProps) {
  return (
    <div className="mb-4 mt-2 w-full overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50 p-3">
        <div className="flex items-center gap-2">
          <Archive className="h-4 w-4 text-amber-500" />
          <span className="text-sm font-semibold text-gray-900">Dead stock report</span>
        </div>
        <span className="text-xs font-medium text-gray-500">
          {summary.items_count} items &middot; {formatCurrency(summary.total_stock_value)} frozen
        </span>
      </div>

      <div className="divide-y divide-gray-100 p-3">
        <div className="mb-3 grid grid-cols-3 gap-2">
          <div className="rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-center">
            <span className="block text-[10px] font-semibold uppercase tracking-wide text-red-600">Critical</span>
            <span className="text-lg font-bold text-red-700">{summary.critical_count}</span>
          </div>
          <div className="rounded-lg border border-amber-100 bg-amber-50 px-3 py-2 text-center">
            <span className="block text-[10px] font-semibold uppercase tracking-wide text-amber-600">Warning</span>
            <span className="text-lg font-bold text-amber-700">{summary.warning_count}</span>
          </div>
          <div className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-center">
            <span className="block text-[10px] font-semibold uppercase tracking-wide text-blue-600">Info</span>
            <span className="text-lg font-bold text-blue-700">{summary.info_count}</span>
          </div>
        </div>

        {items.slice(0, 5).map((item) => (
          <div key={item.product_id} className="flex items-start justify-between py-2.5 first:pt-0">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-900">{item.name}</span>
                <span className={`rounded-full border px-1.5 py-0.5 text-[10px] font-semibold ${SEVERITY_COLORS[item.severity] ?? SEVERITY_COLORS.info}`}>
                  {item.severity === "critical" ? "critical" : item.severity === "warning" ? "warning" : "info"}
                </span>
              </div>
              <span className="text-xs text-gray-500">{item.sku} &middot; {item.dead_stock_days} d. no sales</span>
              <div className="mt-1 flex items-center gap-1.5">
                <Tag className="h-3 w-3 text-gray-400" />
                <span className="text-xs font-medium text-gray-600">{titleizeAction(item.recommended_action)}</span>
              </div>
            </div>
            <div className="shrink-0 text-right">
              <span className="block text-sm font-semibold text-gray-900">{formatCurrency(item.stock_value)}</span>
                <span className="text-xs text-gray-500">{formatNumber(item.available_qty)} pcs</span>
              </div>
            </div>
          ))}

        {items.length > 5 ? (
          <div className="pt-2 text-center text-xs text-gray-400">
            + more {items.length - 5}
          </div>
        ) : null}
      </div>

      <div className="flex items-start gap-1.5 border-t border-amber-100 bg-amber-50/50 p-2.5 text-xs text-amber-700">
        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <span className="leading-relaxed">
          These items have had no significant sales for a long time, freezing {formatCurrency(summary.total_stock_value)} in working capital.
        </span>
      </div>
    </div>
  );
}
