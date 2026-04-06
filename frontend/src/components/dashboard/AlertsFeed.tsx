import { useMemo } from "react";

import { formatCurrency, formatDate, formatRelativeDays } from "../../lib/format";
import type { DeadStockItem } from "../../lib/types";
import { cn } from "../ui/StatusBadge";

type AlertType = "critical" | "warning" | "info";

interface FeedAlert {
  id: string;
  type: AlertType;
  eyebrow: string;
  title: string;
  meta: string;
  supporting: string;
  action: string;
}

function pluralizeDays(value: number) {
  if (value === 1) {
    return `${value} day`;
  }

  return `${value} days`;
}

function compactSku(value: string) {
  if (value.length <= 8) {
    return value;
  }

  return `...${value.slice(-7)}`;
}

function buildTimeLabel(item: DeadStockItem) {
  if (item.last_sale_date) {
    return `${formatRelativeDays(item.last_sale_date)} · ${formatDate(item.last_sale_date)}`;
  }

  return `${pluralizeDays(item.dead_stock_days)} without sales`;
}

function buildMockAlert(item: DeadStockItem, index: number): FeedAlert {
  const sku = compactSku(item.sku);
  const stockValue = formatCurrency(item.stock_value);
  const daysWithoutSales = pluralizeDays(item.dead_stock_days);
  const stockCover = item.days_of_stock !== null ? `${Math.round(item.days_of_stock)} days coverage` : "long supply";
  const timeLabel = buildTimeLabel(item);

  const scenarios: FeedAlert[] = [
    {
      id: `${item.product_id}-receipt-risk`,
      type: "critical",
      eyebrow: "Risk",
      title: "SKU already overstocked, but a new shipment has arrived",
      meta: `${sku} · ${stockCover} · ${stockValue}`,
      supporting: `This item has not sold for ${daysWithoutSales}. There is a risk of deepening excess stock after the latest receipt.`,
      action: "Stop reordering",
    },
    {
      id: `${item.product_id}-demand-drop`,
      type: "warning",
      eyebrow: "Needs attention",
      title: "Demand has slowed compared to last week",
      meta: `${sku} · ${stockCover} · ${timeLabel}`,
      supporting: `Sales have weakened, and the item has been sitting in the warehouse longer than normal. Consider reviewing price, placement, and promo support.`,
      action: "Check demand",
    },
    {
      id: `${item.product_id}-stalled-after-receipt`,
      type: "critical",
      eyebrow: "Risk",
      title: "After restocking, the item is still barely moving",
      meta: `${sku} · ${stockValue} · ${timeLabel}`,
      supporting: `Stock is already frozen in inventory, and velocity has not recovered after the delivery. It's best to quickly decide on a clearance sale or bundle.`,
      action: "Launch promotion",
    },
    {
      id: `${item.product_id}-promo-opportunity`,
      type: "info",
      eyebrow: "Opportunity",
      title: "Stock can be cleared with a soft promo scenario",
      meta: `${sku} · ${stockValue} · ${stockCover}`,
      supporting: `This SKU has been idle for a long time, but the situation can still be improved with a discount, bundle, or relocation to a more visible zone.`,
      action: "Apply discount",
    },
  ];

  return scenarios[index % scenarios.length];
}

function getEyebrowTone(type: AlertType) {
  if (type === "critical") return "text-red-700 bg-red-50";
  if (type === "warning") return "text-amber-700 bg-amber-50";
  return "text-sky-700 bg-sky-50";
}

function getAccentTone(type: AlertType) {
  if (type === "critical") return "border-l-red-400";
  if (type === "warning") return "border-l-amber-400";
  return "border-l-sky-400";
}

function getActionTone(type: AlertType) {
  if (type === "critical") return "bg-red-50 text-red-700 hover:bg-red-100";
  if (type === "warning") return "bg-amber-50 text-amber-700 hover:bg-amber-100";
  return "bg-gray-100 text-gray-700 hover:bg-gray-200";
}

export function AlertsFeed({ items }: { items: DeadStockItem[] }) {
  const alerts = useMemo(() => items.map((item, index) => buildMockAlert(item, index)), [items]);

  return (
    <div className="flex h-full w-80 flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 bg-gray-50/50 px-5 py-4">
        <div>
          <h3 className="text-sm font-bold text-gray-900">What changed today</h3>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-hide">
        {alerts.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-400">No events</div>
        ) : null}

        <div className="space-y-3 px-4 py-4">
          {alerts.map((alert) => (
            <article
              key={alert.id}
              className={cn(
                "rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition-colors hover:bg-gray-50/60",
                "border-l-[3px]",
                getAccentTone(alert.type),
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <span
                  className={cn(
                    "inline-flex rounded-full px-2.5 py-1 text-[10px] font-semibold",
                    getEyebrowTone(alert.type),
                  )}
                >
                  {alert.eyebrow}
                </span>
              </div>

              <h4 className="mt-3 text-[14px] font-semibold leading-5 text-gray-900">
                {alert.title}
              </h4>

              <div className="mt-2 text-[11px] text-gray-400">{alert.meta}</div>

              <p className="mt-3 text-[12px] leading-relaxed text-gray-600">
                {alert.supporting}
              </p>

              <div className="mt-4">
                <button
                  type="button"
                  className={cn(
                    "flex h-8 w-full items-center justify-center rounded-lg text-[11px] font-semibold transition-colors",
                    getActionTone(alert.type),
                  )}
                >
                  {alert.action}
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
