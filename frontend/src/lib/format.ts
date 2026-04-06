export function formatNumber(value: number | null | undefined, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

export function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatDate(value: string | null | undefined) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("en-US", {
    day: "2-digit",
    month: "short",
  }).format(new Date(value));
}

export function formatRelativeDays(value: string | null | undefined) {
  if (!value) {
    return "-";
  }

  const target = new Date(value);
  if (Number.isNaN(target.getTime())) {
    return "-";
  }

  const now = new Date();
  const diffMs = now.getTime() - target.getTime();
  const diffDays = Math.max(0, Math.floor(diffMs / (1000 * 60 * 60 * 24)));

  if (diffDays === 0) {
    return "today";
  }

  if (diffDays === 1) {
    return "1 day ago";
  }

  if (diffDays < 5) {
    return `${diffDays} days ago`;
  }

  return `${diffDays} days ago`;
}

export function titleizeAction(value: string) {
  const actionMap: Record<string, string> = {
    return_to_supplier_or_stop_reorder: "Return to supplier or stop reorder",
    launch_promo_or_bundle: "Launch promotion or create bundle",
    apply_discount: "Apply discount",
    get_item_deep_dive: "Product card",
    build_purchase_order: "Purchase plan",
    forecast_demand: "Demand forecast",
    flag_dead_stock: "Dead stock analysis",
    analyze_full_catalog: "Catalog overview",
  };

  if (actionMap[value]) {
    return actionMap[value];
  }

  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
