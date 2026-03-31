import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function fmt(n: number, decimals = 2) {
  return n.toLocaleString("en-IN", { maximumFractionDigits: decimals });
}

export function fmtCurrency(n: number) {
  return `₹${fmt(n, 0)}`;
}

export function fmtPct(n: number) {
  return `${n >= 0 ? "+" : ""}${n.toFixed(1)}%`;
}

export function signalColor(signal: string): string {
  const s = signal.toUpperCase();
  if (s.includes("STRONG_BUY") || s.includes("INVEST_MORE")) return "text-emerald-400";
  if (s.includes("BUY") || s.includes("CONSIDER")) return "text-green-400";
  if (s.includes("HOLD") || s.includes("WAIT")) return "text-yellow-400";
  if (s.includes("SELL") || s.includes("AVOID")) return "text-red-400";
  return "text-slate-300";
}

export function signalBg(signal: string): string {
  const s = signal.toUpperCase();
  if (s.includes("STRONG_BUY") || s.includes("INVEST_MORE")) return "bg-emerald-900/40 border-emerald-700";
  if (s.includes("BUY") || s.includes("CONSIDER")) return "bg-green-900/30 border-green-700";
  if (s.includes("HOLD") || s.includes("WAIT")) return "bg-yellow-900/30 border-yellow-700";
  if (s.includes("SELL") || s.includes("AVOID")) return "bg-red-900/30 border-red-700";
  return "bg-slate-800 border-slate-700";
}

export function scoreColor(score: number): string {
  if (score >= 70) return "text-emerald-400";
  if (score >= 55) return "text-green-400";
  if (score >= 40) return "text-yellow-400";
  return "text-red-400";
}

export function fundTypeLabel(type: string): string {
  const map: Record<string, string> = {
    large_cap: "Large Cap",
    large_mid: "Large & Mid",
    mid_cap: "Mid Cap",
    small_cap: "Small Cap",
    flexi_cap: "Flexi Cap",
    index: "Index",
  };
  return map[type] ?? type;
}
