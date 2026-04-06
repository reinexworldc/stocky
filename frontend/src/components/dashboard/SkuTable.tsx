import { useCallback, useMemo, useState } from "react";

import { formatNumber } from "../../lib/format";
import type { CatalogItem, StatusType } from "../../lib/types";
import { cn, statusColors } from "../ui/StatusBadge";

type FilterMode = "all" | "critical" | "warning" | "ok";

interface GroupedItems {
  label: string;
  items: CatalogItem[];
}

const FILTER_OPTIONS: Array<{ value: FilterMode; label: string }> = [
  { value: "all", label: "All" },
  { value: "critical", label: "Critical" },
  { value: "warning", label: "Warning" },
  { value: "ok", label: "Normal" },
];

const STATUS_ORDER: StatusType[] = ["critical", "warning", "ok", "dead_stock", "overstock"];

function getActionLabel(item: CatalogItem) {
  if (item.status === "critical") {
    return "Order";
  }

  if (item.status === "warning") {
    return "Review";
  }

  return "Details";
}

function getProgressColor(status: StatusType) {
  if (status === "critical") return "bg-red-500";
  if (status === "warning") return "bg-yellow-500";
  return "bg-green-500";
}

function getStatusLabel(status: StatusType, count: number) {
  if (status === "critical") return `${count} critical`;
  if (status === "warning") return `${count} at risk`;
  if (status === "ok") return `${count} stable`;
  if (status === "dead_stock") return `${count} dead stock`;
  return `${count} overstock`;
}

function matchesCategory(item: CatalogItem, category: string) {
  if (category === "all") return true;
  return item.category.toLowerCase() === category;
}

function matchesFilter(item: CatalogItem, filter: FilterMode) {
  if (filter === "all") return true;
  return item.status === filter;
}

function groupItems(items: CatalogItem[]) {
  const grouped = new Map<StatusType, CatalogItem[]>();

  for (const status of STATUS_ORDER) {
    grouped.set(status, []);
  }

  for (const item of items) {
    grouped.get(item.status)?.push(item);
  }

  return STATUS_ORDER.reduce<GroupedItems[]>((acc, status) => {
    const group = grouped.get(status) ?? [];
    if (!group.length) return acc;

    acc.push({
      label: getStatusLabel(status, group.length),
      items: group,
    });

    return acc;
  }, []);
}

function InventoryCard({
  item,
  index,
  onOpenDetails,
  onAction,
}: {
  item: CatalogItem;
  index: number;
  onOpenDetails: (item: CatalogItem) => void;
  onAction: (item: CatalogItem) => void;
}) {
  const max = Math.max(item.total_qty, item.available_qty, item.reorder_qty ?? 0, 1);
  const percentage = Math.min(100, Math.max(0, (item.available_qty / max) * 100));
  const progressWidth = percentage > 0 ? `${Math.max(percentage, 2)}%` : "0%";

  return (
    <button
      type="button"
      onClick={() => onOpenDetails(item)}
      className="inventory-card group relative flex h-full w-full flex-col overflow-hidden rounded-[12px] border border-gray-200 bg-white text-left shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-gray-300 hover:shadow-md"
      style={{ animationDelay: `${index * 30}ms` }}
    >
      <div className="flex flex-1 flex-col gap-2.5 p-4 pb-3">
        <div className="min-w-0">
          <div className="truncate text-[14px] font-medium leading-5 text-gray-900">
            {item.name}
          </div>
          <div className="mt-1 text-[11px] font-medium uppercase tracking-[0.08em] text-gray-400">
            {item.sku}
          </div>
        </div>

        <div className="border-t border-gray-100 pt-2.5">
          <div className="flex items-center gap-3">
            <div className="shrink-0 text-[11px] font-medium text-gray-500 tabular-nums">
              {formatNumber(item.available_qty)} / {formatNumber(max)}
            </div>

            <div className="h-1 w-full overflow-hidden rounded-full bg-gray-100">
              <div
                className={cn(
                  "h-full rounded-full transition-[width,background-color] duration-300 ease-out",
                  getProgressColor(item.status),
                )}
                style={{ width: progressWidth }}
              />
            </div>

            <div className="shrink-0 text-[11px] font-medium text-gray-400 tabular-nums">
              {formatNumber(item.velocity_7d, 1)}/d
            </div>
          </div>
        </div>
      </div>

      <div className="mt-auto border-t border-gray-100 px-3 py-2">
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onAction(item);
          }}
          className="flex h-8 w-full items-center justify-center rounded-lg border border-transparent bg-transparent text-[12px] font-medium text-gray-700 transition-colors hover:bg-gray-50 hover:text-gray-900"
        >
          {getActionLabel(item)}
        </button>
      </div>
    </button>
  );
}

function DetailsDrawer({
  item,
  onClose,
}: {
  item: CatalogItem | null;
  onClose: () => void;
}) {
  if (!item) return null;

  const badge = statusColors[item.status];
  const orderAmount = (item.reorder_qty ?? 0) * Math.max(item.priority_score, 1);

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-gray-900/30 px-3 pb-3 pt-10 backdrop-blur-[2px] sm:px-6">
      <button
        type="button"
        aria-label="Close"
        className="absolute inset-0 cursor-default"
        onClick={onClose}
      />

      <div className="details-drawer relative z-10 flex max-h-[70vh] w-full max-w-2xl flex-col overflow-hidden rounded-[20px] bg-white shadow-2xl">
        <div className="flex justify-center pt-3">
          <div className="h-1.5 w-12 rounded-full bg-gray-200" />
        </div>

        <div className="flex items-start justify-between gap-4 px-5 pb-4 pt-4">
          <div className="min-w-0">
            <h3 className="text-base font-semibold text-gray-900">{item.name}</h3>
            <p className="mt-1 text-[11px] uppercase tracking-[0.08em] text-gray-400">
              {item.sku}
            </p>
          </div>

          <span
            className={cn(
              "shrink-0 rounded-full px-2.5 py-1 text-[11px] font-semibold",
              badge.bg,
              badge.text,
            )}
          >
            {badge.label}
          </span>
        </div>

        <div className="overflow-y-auto px-5 pb-5">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-gray-50 px-4 py-3">
              <div className="text-[11px] font-medium uppercase tracking-[0.08em] text-gray-400">
                Category
              </div>
              <div className="mt-1 text-sm font-medium text-gray-900">{item.category}</div>
            </div>

            <div className="rounded-xl bg-gray-50 px-4 py-3">
              <div className="text-[11px] font-medium uppercase tracking-[0.08em] text-gray-400">
                Stock
              </div>
              <div className="mt-1 text-sm font-medium text-gray-900">
                {formatNumber(item.available_qty)} of {formatNumber(item.total_qty)}
              </div>
            </div>

            <div className="rounded-xl bg-gray-50 px-4 py-3">
              <div className="text-[11px] font-medium uppercase tracking-[0.08em] text-gray-400">
                Stock history
              </div>
              <div className="mt-1 text-sm font-medium text-gray-900">
                {item.days_of_stock !== null ? `${formatNumber(item.days_of_stock, 0)} days coverage` : "Insufficient data"}
              </div>
            </div>

            <div className="rounded-xl bg-gray-50 px-4 py-3">
              <div className="text-[11px] font-medium uppercase tracking-[0.08em] text-gray-400">
                Last delivery
              </div>
              <div className="mt-1 text-sm font-medium text-gray-900">No data</div>
            </div>

            <div className="rounded-xl bg-gray-50 px-4 py-3">
              <div className="text-[11px] font-medium uppercase tracking-[0.08em] text-gray-400">
                Sales velocity
              </div>
              <div className="mt-1 text-sm font-medium text-gray-900">
                {formatNumber(item.velocity_7d, 1)}/day
              </div>
            </div>

            <div className="rounded-xl bg-gray-50 px-4 py-3">
              <div className="text-[11px] font-medium uppercase tracking-[0.08em] text-gray-400">
                Order amount
              </div>
              <div className="mt-1 text-sm font-medium text-gray-900">
                {formatNumber(orderAmount)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SkuTable({ items }: { items: CatalogItem[] }) {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<FilterMode>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [selectedItem, setSelectedItem] = useState<CatalogItem | null>(null);

  const categories = useMemo(() => {
    const unique = Array.from(new Set(items.map((item) => item.category.toLowerCase())));
    return unique.sort();
  }, [items]);

  const filteredItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return [...items]
      .filter((item) => matchesFilter(item, statusFilter))
      .filter((item) => matchesCategory(item, categoryFilter))
      .filter((item) => {
        if (!normalizedQuery) return true;
        return (
          item.name.toLowerCase().includes(normalizedQuery) ||
          item.sku.toLowerCase().includes(normalizedQuery)
        );
      })
      .sort((a, b) => {
        const statusDiff = STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status);
        if (statusDiff !== 0) return statusDiff;
        return b.priority_score - a.priority_score;
      });
  }, [categoryFilter, items, query, statusFilter]);

  const groupedItems = useMemo(() => groupItems(filteredItems), [filteredItems]);

  const handleAction = useCallback((item: CatalogItem) => {
    window.alert(`${getActionLabel(item)}: ${item.sku}`);
  }, []);

  return (
    <>
      <div className="flex h-full flex-1 flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 bg-gray-50/60 px-4 py-4 sm:px-5">
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-sm font-bold text-gray-900">Stock overview</h2>
              <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-gray-400">
                {filteredItems.length} items
              </span>
            </div>

            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <input
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search: SKU or product"
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 transition-all placeholder:text-gray-400 focus:border-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-900/10 sm:max-w-xs"
              />

              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as FilterMode)}
                  className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-900/10"
                >
                  {FILTER_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>

                <select
                  value={categoryFilter}
                  onChange={(event) => setCategoryFilter(event.target.value)}
                  className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-900/10"
                >
                  <option value="all">All categories</option>
                  {categories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-3 sm:px-4">
          {groupedItems.length === 0 ? (
            <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50/50 px-6 py-12 text-center text-sm text-gray-500">
              Nothing found. Try adjusting your search or filters.
            </div>
          ) : (
            <div className="space-y-4">
              {groupedItems.map((group) => (
                <section key={group.label} className="space-y-2">
                  <div className="px-1 text-[11px] font-medium uppercase tracking-[0.08em] text-gray-400">
                    {group.label}
                  </div>

                  <div className="grid grid-cols-1 gap-2 min-[700px]:grid-cols-2">
                    {group.items.map((item, index) => (
                      <InventoryCard
                        key={item.product_id}
                        item={item}
                        index={index}
                        onOpenDetails={setSelectedItem}
                        onAction={handleAction}
                      />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      </div>

      <DetailsDrawer item={selectedItem} onClose={() => setSelectedItem(null)} />
    </>
  );
}
