export type StatusType = "critical" | "warning" | "ok" | "dead_stock" | "overstock";

export interface CatalogSummary {
  total_skus: number;
  critical_count: number;
  warning_count: number;
  ok_count: number;
}

export interface CatalogItem {
  product_id: string;
  sku: string;
  name: string;
  category: string;
  supplier_name: string;
  available_qty: number;
  total_qty: number;
  reserved_qty: number;
  velocity_7d: number;
  days_of_stock: number | null;
  reorder_point: number | null;
  reorder_qty: number | null;
  status: StatusType;
  priority_score: number;
}

export interface CatalogResponse {
  summary: CatalogSummary;
  top_critical: CatalogItem[];
  ranked_items: CatalogItem[];
  traffic_light: {
    red: number;
    yellow: number;
    green: number;
  };
}

export interface DeadStockItem {
  product_id: string;
  sku: string;
  name: string;
  category: string | null;
  supplier_name: string | null;
  available_qty: number;
  purchase_price: number;
  stock_value: number;
  days_of_stock: number | null;
  last_sale_date: string | null;
  dead_stock_days: number;
  status: string;
  severity: "critical" | "warning" | "info";
  recommended_action: string;
  reason: string;
}

export interface DeadStockResponse {
  summary: {
    items_count: number;
    critical_count: number;
    warning_count: number;
    info_count: number;
    total_stock_value: number;
  };
  items: DeadStockItem[];
}

export interface DeepDiveResponse {
  product: {
    id: string;
    sku: string;
    name: string;
    category: string | null;
    subcategory: string | null;
    unit: string | null;
    supplier_name: string | null;
    purchase_price: number | null;
    selling_price: number | null;
    lead_time_days: number;
    min_order_qty: number;
    safety_stock_days: number;
    max_stock_qty: number | null;
  };
  stock: {
    total_qty: number;
    reserved_qty: number;
    available_qty: number;
    days_of_stock: number | null;
    status: StatusType | null;
    reorder_point: number | null;
  };
  sales: {
    sales_7d: { total_quantity: number; avg_daily_sales: number };
    sales_30d: { total_quantity: number; avg_daily_sales: number };
    sales_90d: { total_quantity: number; avg_daily_sales: number };
    last_sale_date: string | null;
    dead_stock_days: number | null;
  };
  trend: {
    trend_ratio: number;
    label: string;
  };
  forecast: {
    blended_velocity: number;
    forecast_7d: number;
    forecast_14d: number;
    forecast_30d: number;
  };
  recommendation: {
    target_stock: number;
    raw_order_qty: number;
    recommended_order_qty: number;
  };
  explanation: {
    source: string;
    provider: string | null;
    model: string | null;
    text: string;
    fallback_text?: string;
  };
}

export interface PurchaseOrderItem {
  product_id: string;
  sku: string;
  name: string;
  category: string | null;
  unit: string | null;
  status: string;
  available_qty: number;
  forecast_14d: number;
  target_stock: number;
  raw_order_qty: number;
  order_qty: number;
  min_order_qty: number;
  purchase_price: number;
  line_total: number;
  lead_time_days: number;
  reason: string;
}

export interface PurchaseOrderGroup {
  supplier: {
    supplier_id: string;
    supplier_name: string;
    payment_terms: string | null;
    min_order_amount: number;
    expected_delivery_date: string;
  };
  items: PurchaseOrderItem[];
  totals: {
    lines_count: number;
    total_amount: number;
    below_min_order_amount: boolean;
  };
}

export interface PurchaseOrderResponse {
  summary: {
    suppliers_count: number;
    items_count: number;
    grand_total: number;
  };
  purchase_orders: PurchaseOrderGroup[];
}

export interface ForecastResponse {
  sku: string;
  name: string;
  inputs: {
    sales_7d: { days: number; total_quantity: number; avg_daily_sales: number; total_revenue: number };
    sales_30d: { days: number; total_quantity: number; avg_daily_sales: number; total_revenue: number };
    sales_90d: { days: number; total_quantity: number; avg_daily_sales: number; total_revenue: number };
  };
  forecast: {
    blended_velocity: number;
    forecast_7d: number;
    forecast_14d: number;
    forecast_30d: number;
  };
  method: {
    formula: string;
    comment: string;
  };
}

export interface ChatReply {
  source: string;
  provider: string | null;
  model: string | null;
  text: string;
  fallback_text?: string;
}

export interface ChatToolCall {
  tool_name: string;
  args: Record<string, string | number | boolean | null>;
  result: unknown;
}

export interface ChatResponse {
  conversation_id: string;
  message: string;
  resolved_sku: string | null;
  reply: ChatReply;
  tool_calls: ChatToolCall[];
}
