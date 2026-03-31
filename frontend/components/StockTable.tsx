import { type StockSignal } from "@/lib/api";
import { fmt, signalColor, signalBg, cn } from "@/lib/utils";

const LABEL_MAP: Record<string, string> = {
  strong_buy: "STRONG BUY",
  buy: "BUY",
  hold: "HOLD",
  sell: "SELL",
};

function SignalBadge({ label }: { label: string }) {
  const text = LABEL_MAP[label] ?? label.toUpperCase();
  return (
    <span
      className={cn(
        "rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        signalBg(label),
        signalColor(label)
      )}
    >
      {text}
    </span>
  );
}

function DmaIcon({ pct }: { pct: number | null }) {
  if (pct === null) return <span className="text-slate-500">—</span>;
  if (pct > 0) return <span className="text-emerald-400">{fmt(pct)}%</span>;
  return <span className="text-red-400">{fmt(pct)}%</span>;
}

export function StockTable({ signals }: { signals: StockSignal[] }) {
  const sorted = [...signals].sort((a, b) => b.composite_score - a.composite_score);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700 text-left text-xs text-slate-400">
            <th className="pb-2 pr-4">Ticker</th>
            <th className="pb-2 pr-4">Signal</th>
            <th className="pb-2 pr-4 text-right">Score</th>
            <th className="pb-2 pr-4 text-right">Price</th>
            <th className="pb-2 pr-4 text-right">RSI</th>
            <th className="pb-2 pr-4 text-right">vs 200DMA</th>
            <th className="pb-2 text-right">P/E</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {sorted.map((s) => (
            <tr key={s.ticker} className="hover:bg-slate-800/50">
              <td className="py-3 pr-4">
                <div className="font-semibold text-slate-100">{s.ticker}</div>
                {s.company_name && (
                  <div className="text-xs text-slate-500 truncate max-w-[140px]">{s.company_name}</div>
                )}
              </td>
              <td className="py-3 pr-4">
                <SignalBadge label={s.signal_label} />
              </td>
              <td className="py-3 pr-4 text-right">
                <span
                  className={cn(
                    "font-bold",
                    s.composite_score >= 70
                      ? "text-emerald-400"
                      : s.composite_score >= 55
                      ? "text-green-400"
                      : s.composite_score >= 40
                      ? "text-yellow-400"
                      : "text-red-400"
                  )}
                >
                  {fmt(s.composite_score, 1)}
                </span>
              </td>
              <td className="py-3 pr-4 text-right text-slate-200">₹{fmt(s.current_price, 0)}</td>
              <td className="py-3 pr-4 text-right">
                {s.rsi !== null ? (
                  <span
                    className={
                      s.rsi < 30 ? "text-emerald-400" : s.rsi > 70 ? "text-red-400" : "text-slate-300"
                    }
                  >
                    {fmt(s.rsi, 0)}
                  </span>
                ) : (
                  <span className="text-slate-500">—</span>
                )}
              </td>
              <td className="py-3 pr-4 text-right">
                <DmaIcon pct={s.vs_200dma_pct} />
              </td>
              <td className="py-3 text-right text-slate-300">
                {s.pe_ratio != null ? fmt(s.pe_ratio, 1) : <span className="text-slate-500">—</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
