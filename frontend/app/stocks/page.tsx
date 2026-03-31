import { api } from "@/lib/api";
import { StockTable } from "@/components/StockTable";
import { Card, CardTitle } from "@/components/Card";
import { StockTriggerButton } from "./StockTriggerButton";

export const dynamic = "force-dynamic";

export default async function StocksPage() {
  const result = await api.stockSignals().catch(() => null);
  const signals = result ?? [];

  const buySignals = signals.filter(
    (s) => s.signal_label === "strong_buy" || s.signal_label === "buy"
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-100">Stock Watchlist</h1>
        <StockTriggerButton />
      </div>

      {buySignals.length > 0 && (
        <Card className="border-green-700 bg-green-900/20">
          <CardTitle>Buy Signals Today</CardTitle>
          <StockTable signals={buySignals} />
        </Card>
      )}

      <Card>
        <CardTitle>All Watchlist — Ranked by Score</CardTitle>
        {signals.length > 0 ? (
          <StockTable signals={signals} />
        ) : (
          <p className="text-sm text-slate-400">
            No signals yet. Seed the watchlist and trigger a compute.
          </p>
        )}
      </Card>
    </div>
  );
}
