"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import { type MFHistoryItem } from "@/lib/api";

export function SignalHistoryChart({ data }: { data: MFHistoryItem[] }) {
  const sorted = [...data].sort(
    (a, b) => new Date(a.computed_at).getTime() - new Date(b.computed_at).getTime()
  );

  const chartData = sorted.map((d) => ({
    date: new Date(d.computed_at).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      timeZone: "Asia/Kolkata",
    }),
    score: parseFloat(d.composite_score.toFixed(1)),
    signal: d.signal,
    price: Math.round(d.nifty_price),
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <Tooltip
          contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
          labelStyle={{ color: "#cbd5e1" }}
          itemStyle={{ color: "#38bdf8" }}
          formatter={(v) => [`${v ?? "—"}`, "Score"]}
        />
        <ReferenceLine y={60} stroke="#facc15" strokeDasharray="4 4" label={{ value: "60", fill: "#facc15", fontSize: 10 }} />
        <ReferenceLine y={70} stroke="#4ade80" strokeDasharray="4 4" label={{ value: "70", fill: "#4ade80", fontSize: 10 }} />
        <Line
          type="monotone"
          dataKey="score"
          stroke="#38bdf8"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "#38bdf8" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
