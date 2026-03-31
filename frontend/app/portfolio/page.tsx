import { api } from "@/lib/api";
import { Card, CardTitle } from "@/components/Card";
import { AllocationChart } from "@/components/AllocationChart";
import { fmtCurrency, fmtPct, fundTypeLabel } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function PortfolioPage() {
  const [healthResult, cashResult] = await Promise.allSettled([
    api.portfolioHealth(),
    api.cashState(),
  ]);

  const health = healthResult.status === "fulfilled" ? healthResult.value : null;
  const cash = cashResult.status === "fulfilled" ? cashResult.value : null;

  if (!health) {
    return (
      <div className="space-y-6">
        <h1 className="text-xl font-bold text-slate-100">Portfolio</h1>
        <Card>
          <p className="text-sm text-slate-400">
            No portfolio data yet. Add holdings via{" "}
            <code className="rounded bg-slate-700 px-1 py-0.5 text-xs">POST /portfolio/holdings</code>{" "}
            or upload a CAMS statement.
          </p>
        </Card>
      </div>
    );
  }

  const gainPositive = health.total_gain_pct >= 0;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-slate-100">Portfolio</h1>

      {/* Summary row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <div className="text-xs text-slate-400">Invested</div>
          <div className="mt-1 text-xl font-bold text-slate-100">{fmtCurrency(health.total_invested)}</div>
        </Card>
        <Card>
          <div className="text-xs text-slate-400">Current Value</div>
          <div className="mt-1 text-xl font-bold text-slate-100">{fmtCurrency(health.total_current)}</div>
        </Card>
        <Card>
          <div className="text-xs text-slate-400">Total Return</div>
          <div className={`mt-1 flex items-center gap-1 text-xl font-bold ${gainPositive ? "text-emerald-400" : "text-red-400"}`}>
            {gainPositive ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
            {fmtPct(health.total_gain_pct)}
          </div>
        </Card>
        {cash && (
          <Card>
            <div className="text-xs text-slate-400">Deployable Cash</div>
            <div className="mt-1 text-xl font-bold text-sky-400">{fmtCurrency(cash.deployable_cash)}</div>
          </Card>
        )}
      </div>

      {/* Allocation chart */}
      {Object.keys(health.allocation).length > 0 && (
        <Card>
          <CardTitle>Allocation by Category</CardTitle>
          <AllocationChart allocation={health.allocation} />
        </Card>
      )}

      {/* Holdings table */}
      <Card>
        <CardTitle>Holdings</CardTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700 text-left text-xs text-slate-400">
                <th className="pb-2 pr-4">Fund</th>
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4 text-right">Invested</th>
                <th className="pb-2 pr-4 text-right">Current</th>
                <th className="pb-2 text-right">Return</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {health.holdings.map((h) => (
                <tr key={h.isin} className="hover:bg-slate-800/40">
                  <td className="py-3 pr-4">
                    <div className="font-medium text-slate-100">{h.fund_name}</div>
                    <div className="text-xs text-slate-500">{h.isin}</div>
                  </td>
                  <td className="py-3 pr-4 text-slate-400">{fundTypeLabel(h.fund_type)}</td>
                  <td className="py-3 pr-4 text-right text-slate-300">{fmtCurrency(h.invested_amount)}</td>
                  <td className="py-3 pr-4 text-right text-slate-200">
                    {h.current_value !== null ? fmtCurrency(h.current_value) : "—"}
                  </td>
                  <td className="py-3 text-right">
                    {h.gain_pct !== null ? (
                      <span className={h.gain_pct >= 0 ? "text-emerald-400" : "text-red-400"}>
                        {fmtPct(h.gain_pct)}
                      </span>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
