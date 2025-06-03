import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { 
  Stock, 
  StockFundamentals, 
  MarketMover, 
  ApiResponse, 
  StockWithScreening,
  ChartData,
  PriceHistory 
} from '../types';

const TWELVEDATA_API_KEY = 'aed44b1a333842c2952e92c85453f24a';
const BASE_URL = 'https://api.twelvedata.com';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

class ApiService {
  private apiKey: string;
  
  constructor() {
    this.apiKey = TWELVEDATA_API_KEY;
  }

  private async makeRequest<T>(url: string, params: Record<string, any> = {}): Promise<ApiResponse<T>> {
    try {
      const response = await axios.get(url, {
        params: {
          ...params,
          apikey: this.apiKey,
        },
        timeout: 10000,
      });

      return {
        data: response.data as T,
        success: true,
      };
    } catch (error: any) {
      console.error('API request failed:', error);
      return {
        error: error.response?.data?.message || error.message || 'Network error',
        success: false,
      };
    }
  }

  private async getCachedData(key: string): Promise<any | null> {
    try {
      const cached = await AsyncStorage.getItem(key);
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_DURATION) {
          return data;
        }
      }
    } catch (error) {
      console.error('Cache read error:', error);
    }
    return null;
  }

  private async setCachedData(key: string, data: any): Promise<void> {
    try {
      await AsyncStorage.setItem(key, JSON.stringify({
        data,
        timestamp: Date.now(),
      }));
    } catch (error) {
      console.error('Cache write error:', error);
    }
  }

  async getMarketMovers(): Promise<ApiResponse<MarketMover[]>> {
    const cacheKey = 'market_movers';
    const cachedData = await this.getCachedData(cacheKey);
    
    if (cachedData) {
      return { data: cachedData, success: true };
    }

    const response = await this.makeRequest<any>(`${BASE_URL}/market_movers/stocks`, {
      outputsize: 10,
    });

    if (response.success && response.data) {
      const movers: MarketMover[] = response.data.values?.map((item: any) => ({
        symbol: item.symbol,
        name: item.name,
        price: parseFloat(item.price),
        change: parseFloat(item.change),
        change_percent: parseFloat(item.percent_change),
        volume: parseInt(item.volume),
      })) || [];

      await this.setCachedData(cacheKey, movers);
      return { data: movers, success: true };
    }

    return response;
  }

  async getStockQuote(symbol: string): Promise<ApiResponse<Stock>> {
    const response = await this.makeRequest<any>(`${BASE_URL}/quote`, {
      symbol,
    });

    if (response.success && response.data) {
      const stock: Stock = {
        symbol: response.data.symbol,
        company_name: response.data.name,
        current_price: parseFloat(response.data.close),
        price_change: parseFloat(response.data.change),
        price_change_percent: parseFloat(response.data.percent_change),
        volume: parseInt(response.data.volume),
        high_52w: parseFloat(response.data.fifty_two_week?.high),
        low_52w: parseFloat(response.data.fifty_two_week?.low),
      };

      return { data: stock, success: true };
    }

    return response;
  }

  async getStockTimeSeries(symbol: string, interval: string = '1day', outputsize: number = 365): Promise<ApiResponse<PriceHistory[]>> {
    const response = await this.makeRequest<any>(`${BASE_URL}/time_series`, {
      symbol,
      interval,
      outputsize,
    });

    if (response.success && response.data?.values) {
      const priceHistory: PriceHistory[] = response.data.values.map((item: any) => ({
        date: item.datetime,
        open: parseFloat(item.open),
        high: parseFloat(item.high),
        low: parseFloat(item.low),
        close: parseFloat(item.close),
        volume: parseInt(item.volume),
      }));

      return { data: priceHistory, success: true };
    }

    return response;
  }

  async getStockFundamentals(symbol: string): Promise<ApiResponse<StockFundamentals>> {
    const [profileResponse, earningsResponse, growthResponse] = await Promise.all([
      this.makeRequest<any>(`${BASE_URL}/profile`, { symbol }),
      this.makeRequest<any>(`${BASE_URL}/earnings`, { symbol }),
      this.makeRequest<any>(`${BASE_URL}/growth_estimates`, { symbol }),
    ]);

    if (profileResponse.success && profileResponse.data) {
      const profile = profileResponse.data;
      const earnings = earningsResponse.data;
      const growth = growthResponse.data;

      const fundamentals: StockFundamentals = {
        market_cap: parseFloat(profile.market_cap),
        pe_ratio: parseFloat(profile.pe_ratio),
        price_to_book: parseFloat(profile.price_to_book),
        eps: parseFloat(profile.eps),
        dividend_yield: parseFloat(profile.dividend_yield),
        beta: parseFloat(profile.beta),
        quarterly_revenue_growth: earnings?.quarterly_revenue_growth,
        quarterly_eps_growth: earnings?.quarterly_eps_growth,
        estimated_sales_growth: growth?.sales_growth,
        estimated_eps_growth: growth?.eps_growth,
      };

      return { data: fundamentals, success: true };
    }

    return profileResponse;
  }

  async getStockDetails(symbol: string): Promise<ApiResponse<StockWithScreening>> {
    const [quoteResponse, fundamentalsResponse, timeSeriesResponse] = await Promise.all([
      this.getStockQuote(symbol),
      this.getStockFundamentals(symbol),
      this.getStockTimeSeries(symbol, '1day', 200),
    ]);

    if (quoteResponse.success && quoteResponse.data) {
      const stockDetails: StockWithScreening = {
        ...quoteResponse.data,
        fundamentals: fundamentalsResponse.data,
        price_history: timeSeriesResponse.data,
      };

      return { data: stockDetails, success: true };
    }

    return quoteResponse;
  }

  async screenStocks(): Promise<ApiResponse<StockWithScreening[]>> {
    // Get popular stock symbols to screen
    const symbols = [
      'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 
      'CRM', 'ADBE', 'ORCL', 'IBM', 'INTC', 'AMD', 'QCOM', 'AVGO',
      'JPM', 'BAC', 'GS', 'MS', 'WFC', 'C', 'AXP', 'V', 'MA', 'PYPL'
    ];

    try {
      const stockPromises = symbols.slice(0, 10).map(symbol => 
        this.getStockDetails(symbol)
      );

      const results = await Promise.allSettled(stockPromises);
      const stocks: StockWithScreening[] = [];

      results.forEach((result, index) => {
        if (result.status === 'fulfilled' && result.value.success && result.value.data) {
          const stock = result.value.data;
          
          // Apply basic screening criteria
          if (stock.price_history && stock.price_history.length >= 200) {
            const prices = stock.price_history.map(p => p.close);
            const sma200 = this.calculateSMA(prices, 200);
            const sma50 = this.calculateSMA(prices, 50);
            const sma100 = this.calculateSMA(prices, 100);
            
            const currentPrice = stock.current_price || 0;
            const meetsScreening = 
              currentPrice > sma200[sma200.length - 1] &&
              sma50[sma50.length - 1] > sma200[sma200.length - 1] &&
              sma100[sma100.length - 1] > sma200[sma200.length - 1];

            if (meetsScreening) {
              stock.screening_result = {
                price_above_sma200: currentPrice > sma200[sma200.length - 1],
                sma50_above_sma200: sma50[sma50.length - 1] > sma200[sma200.length - 1],
                sma100_above_sma200: sma100[sma100.length - 1] > sma200[sma200.length - 1],
                current_price: currentPrice,
                sma50: sma50[sma50.length - 1],
                sma100: sma100[sma100.length - 1],
                sma200: sma200[sma200.length - 1],
                passes_all_criteria: true,
                meets_all_criteria: true,
                score: this.calculateScore(stock),
              };
              
              stocks.push(stock);
            }
          }
        }
      });

      // Sort by score descending
      stocks.sort((a, b) => (b.screening_result?.score || 0) - (a.screening_result?.score || 0));

      return { data: stocks, success: true };
    } catch (error: any) {
      return {
        error: error.message || 'Failed to screen stocks',
        success: false,
      };
    }
  }

  private calculateSMA(prices: number[], period: number): number[] {
    const sma: number[] = [];
    for (let i = period - 1; i < prices.length; i++) {
      const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      sma.push(sum / period);
    }
    return sma;
  }

  private calculateScore(stock: StockWithScreening): number {
    let score = 0;
    
    // Price momentum (20% weight)
    if (stock.price_change_percent && stock.price_change_percent > 0) {
      score += stock.price_change_percent * 0.2;
    }
    
    // Volume (10% weight)
    if (stock.volume && stock.volume > 1000000) {
      score += 10;
    }
    
    // PE ratio (20% weight)
    if (stock.fundamentals?.pe_ratio) {
      const pe = stock.fundamentals.pe_ratio;
      if (pe > 0 && pe < 25) {
        score += (25 - pe) * 2;
      }
    }
    
    // Growth metrics (30% weight)
    if (stock.fundamentals?.quarterly_revenue_growth && stock.fundamentals.quarterly_revenue_growth > 0) {
      score += stock.fundamentals.quarterly_revenue_growth * 0.3;
    }
    
    if (stock.fundamentals?.quarterly_eps_growth && stock.fundamentals.quarterly_eps_growth > 0) {
      score += stock.fundamentals.quarterly_eps_growth * 0.3;
    }
    
    // Market cap preference (20% weight)
    if (stock.fundamentals?.market_cap) {
      const marketCap = stock.fundamentals.market_cap;
      if (marketCap > 10000000000) { // > 10B
        score += 20;
      } else if (marketCap > 2000000000) { // > 2B
        score += 10;
      }
    }
    
    return Math.max(0, score);
  }

  async getChartData(symbol: string): Promise<ApiResponse<ChartData>> {
    const timeSeriesResponse = await this.getStockTimeSeries(symbol, '1day', 200);
    
    if (timeSeriesResponse.success && timeSeriesResponse.data) {
      const priceHistory = timeSeriesResponse.data;
      const prices = priceHistory.map(p => p.close);
      const dates = priceHistory.map(p => p.date);
      
      const chartData: ChartData = {
        dates: dates.reverse(),
        prices: prices.reverse(),
        sma50: this.calculateSMA(prices, 50),
        sma100: this.calculateSMA(prices, 100),
        sma200: this.calculateSMA(prices, 200),
      };
      
      return { data: chartData, success: true };
    }
    
    return { error: 'Failed to get chart data', success: false };
  }
}

export default new ApiService();