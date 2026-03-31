import { api } from "@/lib/api";
import { MFSignalCard } from "@/components/MFSignalCard";
import { Card, CardTitle } from "@/components/Card";
import { SignalHistoryChart } from "@/components/SignalHistoryChart";
import { TriggerButton } from "./TriggerButton";

export const dynamic = "force-dynamic";

export default async function SignalsPage() {
  const [mfSignal, history] = await Promise.allSettled([
    api.mfLatest(),
    api.mfHistory(90),
  ]);

  const mf = mfSignal.status === "fulfilled" ? mfSignal.value : null;
  const hist = history.status === "fulfilled" ? history.value : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-100">MF Signals</h1>
        <TriggerButton />
      </div>

      {mf ? (
        <MFSignalCard signal={mf} />
      ) : (
        <Card>
          <p className="text-sm text-slate-400">No signal computed yet. Click Recompute to run the pipeline.</p>
        </Card>
      )}

      {hist.length > 0 && (
        <Card>
          <CardTitle>Score History — 90 Days</CardTitle>
          <SignalHistoryChart data={hist} />
          <div className="mt-3 flex gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-0.5 w-4 bg-yellow-400" /> 60 = Consider threshold
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-0.5 w-4 bg-green-400" /> 70 = Strong signal
            </span>
          </div>
        </Card>
      )}

      {hist.length > 0 && (
        <Card>
          <CardTitle>Signal Log</CardTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 text-left text-xs text-slate-400">
                  <th className="pb-2 pr-4">Date (IST)</th>
                  <th className="pb-2 pr-4">Signal</th>
                  <th className="pb-2 pr-4 text-right">Score</th>
                  <th className="pb-2 text-right">Nifty</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {hist.slice(0, 30).map((h, i) => (
                  <tr key={i} className="hover:bg-slate-800/40">
                    <td className="py-2.5 pr-4 text-slate-400">
                      {new Date(h.computed_at).toLocaleDateString("en-IN", {
                        timeZone: "Asia/Kolkata",
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })}
                    </td>
                    <td className="py-2.5 pr-4 font-semibold text-slate-200">{h.signal}</td>
                    <td className="py-2.5 pr-4 text-right font-bold text-sky-400">{h.composite_score.toFixed(1)}</td>
                    <td className="py-2.5 text-right text-slate-300">₹{Math.round(h.nifty_price).toLocaleString("en-IN")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
