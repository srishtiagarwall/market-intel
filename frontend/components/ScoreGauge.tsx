"use client";

import { scoreColor } from "@/lib/utils";

export function ScoreGauge({ score, size = "lg" }: { score: number; size?: "sm" | "lg" }) {
  const r = size === "lg" ? 52 : 32;
  const cx = r + 4;
  const cy = r + 4;
  const strokeWidth = size === "lg" ? 8 : 6;
  const circumference = 2 * Math.PI * r;
  const dash = (score / 100) * circumference;
  const color = score >= 70 ? "#34d399" : score >= 55 ? "#4ade80" : score >= 40 ? "#facc15" : "#f87171";
  const dim = (cx + 4) * 2;

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={dim} height={dim}>
        {/* track */}
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#334155" strokeWidth={strokeWidth} />
        {/* progress */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={`${dash} ${circumference}`}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`}
        />
        <text
          x={cx}
          y={cy}
          textAnchor="middle"
          dominantBaseline="central"
          fill={color}
          fontSize={size === "lg" ? 20 : 13}
          fontWeight="bold"
        >
          {score.toFixed(0)}
        </text>
      </svg>
      <span className={`text-xs font-medium ${scoreColor(score)}`}>/ 100</span>
    </div>
  );
}
