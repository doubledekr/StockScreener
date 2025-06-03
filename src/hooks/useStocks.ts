import { useState, useEffect, useCallback } from 'react';
import ApiService from '../services/api';
import { StockWithScreening, MarketMover, ApiResponse } from '../types';

export const useStocks = () => {
  const [stocks, setStocks] = useState<StockWithScreening[]>([]);
  const [marketMovers, setMarketMovers] = useState<MarketMover[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadMarketMovers = useCallback(async () => {
    try {
      setError(null);
      const response = await ApiService.getMarketMovers();
      
      if (response.success && response.data) {
        setMarketMovers(response.data);
      } else {
        setError(response.error || 'Failed to load market movers');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load market movers');
    }
  }, []);

  const loadScreenedStocks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await ApiService.screenStocks();
      
      if (response.success && response.data) {
        setStocks(response.data);
      } else {
        setError(response.error || 'Failed to screen stocks');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to screen stocks');
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshData = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([
      loadMarketMovers(),
      loadScreenedStocks(),
    ]);
    setRefreshing(false);
  }, [loadMarketMovers, loadScreenedStocks]);

  const getStockDetails = useCallback(async (symbol: string): Promise<StockWithScreening | null> => {
    try {
      setError(null);
      const response = await ApiService.getStockDetails(symbol);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        setError(response.error || 'Failed to get stock details');
        return null;
      }
    } catch (err: any) {
      setError(err.message || 'Failed to get stock details');
      return null;
    }
  }, []);

  useEffect(() => {
    loadMarketMovers();
    loadScreenedStocks();
  }, [loadMarketMovers, loadScreenedStocks]);

  return {
    stocks,
    marketMovers,
    loading,
    error,
    refreshing,
    refreshData,
    getStockDetails,
    loadScreenedStocks,
    loadMarketMovers,
  };
};