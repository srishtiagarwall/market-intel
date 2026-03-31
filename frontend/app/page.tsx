import { api } from "@/lib/api";
import { MFSignalCard } from "@/components/MFSignalCard";
import { StockTable } from "@/components/StockTable";
import { Card, CardTitle } from "@/components/Card";
import { SignalHistoryChart } from "@/components/SignalHistoryChart";
import { RefreshCw } from "lucide-react";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const [mfSignal, history, stocks] = await Promise.allSettled([
    api.mfLatest(),
    api.mfHistory(30),
    api.stockSignals(),
  ]);

  const mf = mfSignal.status === "fulfilled" ? mfSignal.value : null;
  const hist = history.status === "fulfilled" ? history.value : [];
  const stockList = stocks.status === "fulfilled" ? stocks.value : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-100">Dashboard</h1>
        <span className="flex items-center gap-1.5 text-xs text-slate-500">
          <RefreshCw size={12} /> Auto-refreshes every 5 min
        </span>
      </div>

      {mf ? (
        <MFSignalCard signal={mf} />
      ) : (
        <Card>
          <p className="text-sm text-slate-400">
            No MF signal yet.{" "}
            <Link href="/signals" className="text-sky-400 underline">
              Trigger a compute
            </Link>
          </p>
        </Card>
      )}

      {hist.length > 0 && (
        <Card>
          <CardTitle>MF Score — 30 Day History</CardTitle>
          <SignalHistoryChart data={hist} />
        </Card>
      )}

      {stockList.length > 0 && (
        <Card>
          <div className="flex items-center justify-between">
            <CardTitle>Watchlist</CardTitle>
            <Link href="/stocks" className="text-xs text-sky-400 hover:underline">
              View all →
            </Link>
          </div>
          <StockTable signals={stockList.slice(0, 5)} />
        </Card>
      )}
    </div>
  );
}
