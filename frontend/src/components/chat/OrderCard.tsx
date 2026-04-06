import { CheckCircle2, FileText } from "lucide-react";

import { formatCurrency, formatDate, formatNumber } from "../../lib/format";
import type { PurchaseOrderGroup } from "../../lib/types";

export function OrderCard({ order }: { order: PurchaseOrderGroup }) {
  return (
    <div className="mb-4 mt-2 w-full overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50 p-3">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-semibold text-gray-900">
            Draft supplier order
          </span>
        </div>
        <span className="text-xs font-medium text-gray-500">
          Supplier: {order.supplier.supplier_name}
        </span>
      </div>

      <div className="p-3">
        <div className="space-y-3">
          {order.items.slice(0, 4).map((item) => (
            <div key={item.product_id} className="flex items-center justify-between text-sm">
              <div className="flex flex-col">
                <span className="font-medium text-gray-900">{item.name}</span>
                <span className="text-xs text-gray-500">{item.sku}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-gray-500">
                  {formatNumber(item.order_qty)} {item.unit ?? "pcs"}
                </span>
                <span className="font-medium text-gray-900">
                  {formatCurrency(item.line_total)}
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-3">
          <span className="text-sm font-medium text-gray-500">
            Total ({formatNumber(order.totals.lines_count)} items)
          </span>
          <span className="text-base font-bold text-gray-900">
            {formatCurrency(order.totals.total_amount)}
          </span>
        </div>

        <button className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-gray-900 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-gray-800 focus:ring-2 focus:ring-gray-900 focus:ring-offset-2">
          <CheckCircle2 className="h-4 w-4" />
          Confirm order
        </button>
      </div>

      <div className="flex items-start gap-1.5 border-t border-blue-100 bg-blue-50/50 p-2.5 text-xs text-blue-700">
        <span className="font-semibold">Assistant comment:</span>
        <span className="leading-relaxed">
          Expected delivery: {formatDate(order.supplier.expected_delivery_date)}. Payment terms: {order.supplier.payment_terms ?? "not specified"}. Minimum order quantities and lead times have been accounted for.
        </span>
      </div>
    </div>
  );
}
