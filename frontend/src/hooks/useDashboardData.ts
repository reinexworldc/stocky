import { useEffect, useState } from "react";

import { api } from "../lib/api";
import type {
  CatalogResponse,
  DeadStockResponse,
  PurchaseOrderResponse,
} from "../lib/types";

export interface DashboardState {
  catalog: CatalogResponse | null;
  deadStock: DeadStockResponse | null;
  purchasePlan: PurchaseOrderResponse | null;
  loading: boolean;
  error: string | null;
}

let dashboardPromise: Promise<{
  catalog: CatalogResponse;
  deadStock: DeadStockResponse;
  purchasePlan: PurchaseOrderResponse;
}> | null = null;

function loadDashboardData() {
  if (!dashboardPromise) {
    dashboardPromise = Promise.all([
      api.getCatalog(),
      api.getDeadStock(),
      api.getPurchasePlan(),
    ])
      .then(([catalog, deadStock, purchasePlan]) => ({
        catalog,
        deadStock,
        purchasePlan,
      }))
      .catch((err) => {
        dashboardPromise = null;
        throw err;
      });
  }
  return dashboardPromise;
}

export function useDashboardData() {
  const [state, setState] = useState<DashboardState>({
    catalog: null,
    deadStock: null,
    purchasePlan: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let active = true;

    loadDashboardData()
      .then(({ catalog, deadStock, purchasePlan }) => {
        if (!active) return;
        setState({ catalog, deadStock, purchasePlan, loading: false, error: null });
      })
      .catch((error) => {
        if (!active) return;
        setState((prev) => ({
          ...prev,
          loading: false,
          error:
            error instanceof Error
              ? error.message
              : "Failed to load dashboard data.",
        }));
      });

    return () => {
      active = false;
    };
  }, []);

  return state;
}
