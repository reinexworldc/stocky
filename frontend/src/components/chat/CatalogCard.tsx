import { BarChart3 } from "lucide-react";

import { formatNumber } from "../../lib/format";
import type { CatalogItem, CatalogSummary } from "../../lib/types";
import { StatusBadge } from "../ui/StatusBadge";

interface CatalogCardProps {
  summary: CatalogSummary;
  trafficLight: { red: number; yellow: number; green: number };
  topCritical: CatalogItem[];
}

export function CatalogCard({ summary, trafficLight, topCritical }: CatalogCardProps) {
  return (
    <div className="mb-4 mt-2 w-full overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50 p-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-gray-700" />
          <span className="text-sm font-semibold text-gray-900">Catalog overview</span>
        </div>
        <span className="text-xs font-medium text-gray-500">{summary.total_skus} SKU</span>
      </div>

      <div className="p-3">
        <div className="mb-3 flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="inline-block h-3 w-3 rounded-full bg-red-500" />
            <span className="text-xs font-semibold text-gray-700">{trafficLight.red}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="inline-block h-3 w-3 rounded-full bg-amber-400" />
            <span className="text-xs font-semibold text-gray-700">{trafficLight.yellow}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="inline-block h-3 w-3 rounded-full bg-green-500" />
            <span className="text-xs font-semibold text-gray-700">{trafficLight.green}</span>
          </div>

          {/* simple bar */}
          <div className="flex h-2.5 flex-1 overflow-hidden rounded-full bg-gray-100">
            {trafficLight.red > 0 ? (
              <div
                className="bg-red-500"
                style={{ width: `${(trafficLight.red / summary.total_skus) * 100}%` }}
              />
            ) : null}
            {trafficLight.yellow > 0 ? (
              <div
                className="bg-amber-400"
                style={{ width: `${(trafficLight.yellow / summary.total_skus) * 100}%` }}
              />
            ) : null}
            {trafficLight.green > 0 ? (
              <div
                className="bg-green-500"
                style={{ width: `${(trafficLight.green / summary.total_skus) * 100}%` }}
              />
            ) : null}
          </div>
        </div>

        {topCritical.length > 0 ? (
          <div className="divide-y divide-gray-100">
            <h4 className="pb-2 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
              Critical items
            </h4>
            {topCritical.slice(0, 5).map((item) => (
              <div key={item.product_id} className="flex items-center justify-between py-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900 truncate">{item.name}</span>
                    <StatusBadge status={item.status} />
                  </div>
                  <span className="text-xs text-gray-500">{item.sku}</span>
                </div>
                <div className="shrink-0 text-right">
                  <span className="block text-xs font-semibold text-gray-900">
                    {item.days_of_stock != null ? `${formatNumber(item.days_of_stock, 1)} d.` : "-"}
                  </span>
                  <span className="text-[10px] text-gray-500">coverage</span>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
