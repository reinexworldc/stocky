import { formatCurrency, formatNumber } from "../../lib/format";
import type {
  CatalogResponse,
  DeadStockResponse,
  PurchaseOrderResponse,
} from "../../lib/types";

export function MetricCards({
  catalog,
  deadStock,
  purchasePlan,
}: {
  catalog: CatalogResponse;
  deadStock: DeadStockResponse;
  purchasePlan: PurchaseOrderResponse;
}) {
  const critical = catalog.summary.critical_count;
  const warning = catalog.summary.warning_count;
  const totalIssues = critical + warning;

  return (
    <div className="mb-6 flex items-center gap-3 flex-wrap text-sm">
      <span className="font-semibold text-gray-900 tabular-nums">
        {formatNumber(catalog.summary.total_skus)} items
      </span>

      <span className="text-gray-300">/</span>

      {totalIssues > 0 ? (
        <span className="inline-flex items-center gap-1.5 text-red-600 font-semibold tabular-nums">
          <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
          {formatNumber(critical)} crit.
          {warning > 0 && (
            <span className="text-yellow-600 font-semibold">
              + {formatNumber(warning)} warn.
            </span>
          )}
        </span>
      ) : (
        <span className="text-green-600 font-semibold">All stable</span>
      )}

      <span className="text-gray-300">/</span>

      <span className="text-gray-500 tabular-nums">
        Dead stock{" "}
        <span className="font-semibold text-gray-900">
          {formatCurrency(deadStock.summary.total_stock_value)}
        </span>
        <span className="text-gray-400 ml-1">
          ({formatNumber(deadStock.summary.items_count)} items)
        </span>
      </span>

      <span className="text-gray-300">/</span>

      <span className="text-gray-500 tabular-nums">
        Order for{" "}
        <span className="font-semibold text-gray-900">
          {formatCurrency(purchasePlan.summary.grand_total)}
        </span>
        <span className="text-gray-400 ml-1">
          from {formatNumber(purchasePlan.summary.suppliers_count)} suppl.
        </span>
      </span>
    </div>
  );
}
