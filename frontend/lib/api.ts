const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { next: { revalidate: 300 } });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface MFSignal {
  id: string;
  computed_at: string;
  nifty_price: number;
  nifty_52w_high: number;
  drawdown_pct: number;
  nifty_pe: number | null;
  nifty_pb: number | null;
  drawdown_score: number;
  valuation_score: number;
  macro_score: number;
  composite_score: number;
  signal: string;
  recommendation: string;
  deploy_pct_hint: number;
  fund_allocation_hint: Record<string, number> | string | null;
}

export interface MFHistoryItem {
  computed_at: string;
  composite_score: number;
  signal: string;
  nifty_price: number;
  drawdown_pct: number;
}

export interface StockSignal {
  ticker: string;
  company_name: string | null;
  signal_label: "strong_buy" | "buy" | "hold" | "sell";
  composite_score: number;
  current_price: number;
  rsi: number | null;
  vs_200dma_pct: number | null;
  // Only present on full StockSignalResponse
  id?: string;
  computed_at?: string;
  fundamental_score?: number | null;
  technical_score?: number | null;
  event_score?: number | null;
  pe_ratio?: number | null;
  reasoning?: string | null;
}

export interface PortfolioHolding {
  isin: string;
  fund_name: string;
  fund_type: string;
  invested_amount: number;
  units: number;
  buy_nav: number;
  current_nav: number | null;
  current_value: number | null;
  gain_pct: number | null;
}

export interface PortfolioHealth {
  total_invested: number;
  total_current: number;
  total_gain_pct: number;
  allocation: Record<string, number>;
  holdings: PortfolioHolding[];
}

export interface CashState {
  deployable_cash: number;
  updated_at: string;
}

// ── API calls ──────────────────────────────────────────────────────────────

export const api = {
  mfLatest: () => get<MFSignal>("/signals/mf/latest"),
  mfHistory: (days = 30) => get<MFHistoryItem[]>(`/signals/mf/history?days=${days}`),
  stockSignals: () => get<StockSignal[]>("/signals/stocks"),
  portfolioHealth: () => get<PortfolioHealth>("/portfolio/health"),
  cashState: () => get<CashState>("/portfolio/cash"),
};
