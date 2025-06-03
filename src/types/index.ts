export interface Stock {
  id?: number;
  symbol: string;
  company_name?: string;
  last_updated?: string;
  current_price?: number;
  price_change?: number;
  price_change_percent?: number;
  volume?: number;
  market_cap?: number;
  pe_ratio?: number;
  eps?: number;
  dividend_yield?: number;
  high_52w?: number;
  low_52w?: number;
}

export interface StockFundamentals {
  id?: number;
  stock_id?: number;
  last_updated?: string;
  market_cap?: number;
  pe_ratio?: number;
  peg_ratio?: number;
  price_to_book?: number;
  price_to_sales?: number;
  eps?: number;
  dividend_yield?: number;
  beta?: number;
  roa?: number;
  roe?: number;
  debt_to_equity?: number;
  current_ratio?: number;
  quick_ratio?: number;
  revenue_growth?: number;
  earnings_growth?: number;
  gross_margin?: number;
  operating_margin?: number;
  net_margin?: number;
  quarterly_revenue?: number;
  quarterly_revenue_growth?: number;
  quarterly_eps?: number;
  quarterly_eps_growth?: number;
  estimated_sales_growth?: number;
  estimated_eps_growth?: number;
  price_target_low?: number;
  price_target_avg?: number;
  price_target_high?: number;
  price_target_upside?: number;
  analyst_count?: number;
  buy_ratings?: number;
  hold_ratings?: number;
  sell_ratings?: number;
  detailed_ratings?: string;
}

export interface PriceHistory {
  id?: number;
  stock_id?: number;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ScreeningResult {
  id?: number;
  stock_id?: number;
  screening_date?: string;
  price_above_sma200?: boolean;
  sma200_slope_positive?: boolean;
  sma50_above_sma200?: boolean;
  sma100_above_sma200?: boolean;
  quarterly_sales_growth_positive?: boolean;
  quarterly_eps_growth_positive?: boolean;
  estimated_sales_growth_positive?: boolean;
  estimated_eps_growth_positive?: boolean;
  current_price?: number;
  sma50?: number;
  sma100?: number;
  sma200?: number;
  sma200_slope?: number;
  score?: number;
  passes_all_criteria?: boolean;
  meets_all_criteria?: boolean;
  chart_data?: string;
}

export interface StockWithScreening extends Stock {
  screening_result?: ScreeningResult;
  fundamentals?: StockFundamentals;
  price_history?: PriceHistory[];
}

export interface MarketMover {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
}

export interface ChartData {
  dates: string[];
  prices: number[];
  sma50?: number[];
  sma100?: number[];
  sma200?: number[];
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  success: boolean;
}

export interface ScreeningCriteria {
  price_above_sma200: boolean;
  sma200_slope_positive: boolean;
  sma50_above_sma200: boolean;
  sma100_above_sma200: boolean;
  quarterly_sales_growth_positive: boolean;
  quarterly_eps_growth_positive: boolean;
  estimated_sales_growth_positive: boolean;
  estimated_eps_growth_positive: boolean;
}