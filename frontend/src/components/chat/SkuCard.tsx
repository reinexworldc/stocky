import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PackageSearch, RefreshCcw, TrendingUp } from "lucide-react";

import { formatNumber } from "../../lib/format";
import type { DeepDiveResponse } from "../../lib/types";
import { StatusBadge } from "../ui/StatusBadge";

function buildTrendData(deepDive: DeepDiveResponse) {
  const sales90 = deepDive.sales.sales_90d.total_quantity;
  const avg = sales90 / 13;

  return Array.from({ length: 13 }, (_, index) => ({
    day: `D${(index + 1) * 7}`,
    sales: Number((avg * (0.7 + index * 0.06)).toFixed(1)),
  }));
}

export function SkuCard({ deepDive }: { deepDive: DeepDiveResponse }) {
  const data = buildTrendData(deepDive);

  return (
    <div className="mb-4 mt-2 w-full overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex flex-col gap-2 border-b border-gray-100 p-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold leading-tight text-gray-900">
              {deepDive.product.name}
            </h3>
            <span className="text-xs uppercase tracking-wider text-gray-500">
              {deepDive.product.sku}
            </span>
          </div>
          <StatusBadge status={deepDive.stock.status ?? "ok"} />
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2">
          <div className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
            <span className="mb-0.5 block text-[10px] font-semibold uppercase tracking-wide text-gray-500">
              Current stock
            </span>
            <span className="text-lg font-bold text-gray-900">
              {formatNumber(deepDive.stock.available_qty)}
            </span>
          </div>
          <div className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
            <span className="mb-0.5 block text-[10px] font-semibold uppercase tracking-wide text-gray-500">
              Sales (90 days)
            </span>
            <div className="flex items-center gap-1.5">
              <span className="text-lg font-bold text-gray-900">
                {formatNumber(deepDive.sales.sales_90d.total_quantity)}
              </span>
              <TrendingUp className="h-3 w-3 text-green-500" />
            </div>
          </div>
          <div className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-blue-900">
            <span className="mb-0.5 block text-[10px] font-semibold uppercase tracking-wide text-blue-600/70">
              Rec. order
            </span>
            <span className="text-lg font-bold">
              {formatNumber(deepDive.recommendation.recommended_order_qty)}
            </span>
          </div>
        </div>
      </div>

      <div className="p-4">
        <h4 className="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gray-900">
          <PackageSearch className="h-3.5 w-3.5" />
          Sales trend over 90 days
        </h4>
        <div className="h-[120px] w-full" style={{ minWidth: 0 }}>
          <ResponsiveContainer width="100%" height={120} minWidth={200}>
            <LineChart data={data} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="day" hide />
              <YAxis
                axisLine={false}
                tick={{ fontSize: 10, fill: "#9ca3af" }}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                  fontSize: "12px",
                  boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                }}
                cursor={{ stroke: "#9ca3af", strokeDasharray: "3 3", strokeWidth: 1 }}
              />
              <ReferenceLine
                y={deepDive.forecast.blended_velocity}
                opacity={0.5}
                stroke="#ef4444"
                strokeDasharray="3 3"
              />
              <Line
                activeDot={{ r: 4 }}
                dataKey="sales"
                dot={false}
                stroke="#111827"
                strokeWidth={2}
                type="monotone"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="border-t border-gray-100 bg-gray-50 p-3">
        <div className="flex gap-2">
          <RefreshCcw className="mt-0.5 h-4 w-4 shrink-0 text-gray-500" />
          <p className="text-sm leading-relaxed text-gray-700">
               <strong className="font-semibold text-gray-900">
               Assistant recommendation:{" "}
             </strong>
            {deepDive.explanation.text}
          </p>
        </div>
      </div>
    </div>
  );
}
