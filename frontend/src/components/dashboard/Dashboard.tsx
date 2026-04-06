import { useDashboardData } from "../../hooks/useDashboardData";
import { AgentChat } from "../chat/AgentChat";
import { AlertsFeed } from "./AlertsFeed";
import { MetricCards } from "./MetricCards";
import { SkuTable } from "./SkuTable";

function LoadingState() {
  return (
    <div className="flex h-full items-center justify-center bg-white text-sm text-gray-400 uppercase tracking-widest font-medium">
      <div className="flex items-center gap-3 px-6 py-4">
        Loading data...
      </div>
    </div>
  );
}

function ErrorState({ error }: { error: string }) {
  return (
    <div className="flex h-full items-center justify-center bg-white p-8">
      <div className="max-w-md p-6">
        <div className="mb-4 flex items-center gap-3">
          <span className="h-2 w-2 rounded-full bg-red-500"></span>
          <span className="text-sm font-bold text-gray-900 uppercase tracking-wide">Loading error</span>
        </div>
        <p className="text-sm leading-relaxed text-gray-500">{error}</p>
      </div>
    </div>
  );
}

export function Dashboard() {
  const { catalog, deadStock, purchasePlan, loading, error } =
    useDashboardData();

  if (loading) {
    return <LoadingState />;
  }

  if (error || !catalog || !deadStock || !purchasePlan) {
    return <ErrorState error={error ?? "API data unavailable."} />;
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-1 overflow-hidden bg-gray-50">
      <div className="flex min-w-0 flex-1 overflow-y-auto p-6">
        <div className="mx-auto flex w-full max-w-[1520px] min-w-0 flex-1 flex-col">
          <div className="mb-1">
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              Warehouse summary
            </h1>
          </div>

          <MetricCards
            catalog={catalog}
            deadStock={deadStock}
            purchasePlan={purchasePlan}
          />

          <div className="flex min-h-[500px] flex-1 gap-6 xl:[&>*:nth-child(1)]:basis-[58%] xl:[&>*:nth-child(2)]:basis-[42%]">
            <div className="flex min-w-0 flex-1">
              <SkuTable items={catalog.ranked_items} />
            </div>
            <div className="hidden min-w-[320px] xl:block xl:w-[360px] 2xl:w-[400px]">
              <AlertsFeed items={deadStock.items} />
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 w-[380px] shrink-0 border-l border-gray-200 bg-white xl:w-[420px] 2xl:w-[440px]">
        <AgentChat />
      </div>
    </div>
  );
}
