"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { fundTypeLabel } from "@/lib/utils";

const COLORS = ["#38bdf8", "#818cf8", "#34d399", "#fb923c", "#f472b6", "#a78bfa"];

export function AllocationChart({ allocation }: { allocation: Record<string, number> }) {
  const data = Object.entries(allocation).map(([key, value]) => ({
    name: fundTypeLabel(key),
    value: Math.round(value * 10) / 10,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={3}
          dataKey="value"
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
          formatter={(v) => [`${v ?? 0}%`, ""]}
          labelStyle={{ color: "#cbd5e1" }}
        />
        <Legend
          formatter={(v) => <span style={{ color: "#94a3b8", fontSize: 12 }}>{v}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
