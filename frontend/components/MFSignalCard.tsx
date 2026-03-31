import { Card, CardTitle } from "./Card";
import { ScoreGauge } from "./ScoreGauge";
import { type MFSignal } from "@/lib/api";
import { fmt, signalColor, signalBg, fmtCurrency, cn } from "@/lib/utils";

function parseFundHint(raw: MFSignal["fund_allocation_hint"]): Record<string, number> | null {
  if (!raw) return null;
  if (typeof raw === "string") {
    try { return JSON.parse(raw); } catch { return null; }
  }
  return raw;
}

export function MFSignalCard({ signal }: { signal: MFSignal }) {
  const lastUpdated = new Date(signal.computed_at).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

  const hint = parseFundHint(signal.fund_allocation_hint);

  return (
    <Card className={cn("border", signalBg(signal.signal))}>
      <CardTitle>MF Signal — Today</CardTitle>
      <div className="flex items-start gap-6">
        <ScoreGauge score={signal.composite_score} />
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-3">
            <span className={cn("text-2xl font-bold", signalColor(signal.signal))}>
              {signal.signal}
            </span>
            <span className="rounded-full bg-slate-700 px-2 py-0.5 text-xs text-slate-300">
              Deploy {signal.deploy_pct_hint}%
            </span>
          </div>
          <p className="text-sm text-slate-300">{signal.recommendation}</p>
          <div className="flex flex-wrap gap-4 pt-1 text-sm text-slate-400">
            <span>Nifty <strong className="text-slate-200">{fmtCurrency(signal.nifty_price)}</strong></span>
            <span>Drawdown <strong className="text-slate-200">{fmt(signal.drawdown_pct)}%</strong></span>
            {signal.nifty_pe && <span>P/E <strong className="text-slate-200">{fmt(signal.nifty_pe)}</strong></span>}
            {signal.nifty_pb && <span>P/B <strong className="text-slate-200">{fmt(signal.nifty_pb)}</strong></span>}
          </div>
        </div>
      </div>

      {/* Score breakdown */}
      <div className="mt-4 grid grid-cols-3 gap-3">
        {[
          { label: "Drawdown", score: signal.drawdown_score, max: 40 },
          { label: "Valuation", score: signal.valuation_score, max: 40 },
          { label: "Macro", score: signal.macro_score, max: 20 },
        ].map(({ label, score, max }) => (
          <div key={label} className="rounded-lg bg-slate-900/50 p-3">
            <div className="text-xs text-slate-400">{label}</div>
            <div className="mt-1 text-lg font-semibold text-slate-100">
              {fmt(score, 0)}<span className="text-xs text-slate-500">/{max}</span>
            </div>
            <div className="mt-1 h-1 rounded bg-slate-700">
              <div
                className="h-1 rounded bg-sky-500"
                style={{ width: `${(score / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Fund allocation hint */}
      {hint && Object.keys(hint).length > 0 && (
        <div className="mt-4">
          <div className="mb-2 text-xs text-slate-400">Suggested allocation of new money</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(hint).map(([fundType, pct]) => (
              <span key={fundType} className="rounded-full bg-sky-900/40 px-3 py-1 text-xs text-sky-300">
                {fundType.replace("_", " ")}: {pct}%
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-3 text-right text-xs text-slate-500">Updated {lastUpdated} IST</div>
    </Card>
  );
}
