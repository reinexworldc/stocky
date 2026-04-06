import { TrendingUp } from "lucide-react";

import { formatNumber } from "../../lib/format";
import type { ForecastResponse } from "../../lib/types";

export function ForecastCard({ forecast }: { forecast: ForecastResponse }) {
  const fc = forecast.forecast;
  const s7 = forecast.inputs.sales_7d;
  const s30 = forecast.inputs.sales_30d;

  return (
    <div className="mb-4 mt-2 w-full overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50 p-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-indigo-500" />
          <span className="text-sm font-semibold text-gray-900">Demand forecast</span>
        </div>
        <span className="text-xs font-medium text-gray-500">{forecast.sku}</span>
      </div>

      <div className="p-3">
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          {forecast.name}
        </h4>

        <div className="mb-3 grid grid-cols-3 gap-2">
          <div className="rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-center">
            <span className="block text-[10px] font-semibold uppercase tracking-wide text-indigo-600">7 days</span>
            <span className="text-lg font-bold text-indigo-700">{formatNumber(fc.forecast_7d, 1)}</span>
          </div>
          <div className="rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-center">
            <span className="block text-[10px] font-semibold uppercase tracking-wide text-indigo-600">14 days</span>
            <span className="text-lg font-bold text-indigo-700">{formatNumber(fc.forecast_14d, 1)}</span>
          </div>
          <div className="rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-center">
            <span className="block text-[10px] font-semibold uppercase tracking-wide text-indigo-600">30 days</span>
            <span className="text-lg font-bold text-indigo-700">{formatNumber(fc.forecast_30d, 1)}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
            <span className="block text-[10px] font-semibold uppercase tracking-wide text-gray-500">Daily avg (7d)</span>
            <span className="font-bold text-gray-900">{formatNumber(s7.avg_daily_sales, 2)}</span>
          </div>
          <div className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
            <span className="block text-[10px] font-semibold uppercase tracking-wide text-gray-500">Daily avg (30d)</span>
            <span className="font-bold text-gray-900">{formatNumber(s30.avg_daily_sales, 2)}</span>
          </div>
        </div>
      </div>

      <div className="flex items-start gap-1.5 border-t border-indigo-100 bg-indigo-50/50 p-2.5 text-xs text-indigo-700">
        <TrendingUp className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <span className="leading-relaxed">
          Blended sales velocity: {formatNumber(fc.blended_velocity, 3)}/day. {forecast.method.comment}
        </span>
      </div>
    </div>
  );
}
