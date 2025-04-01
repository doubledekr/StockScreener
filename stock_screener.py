import logging
import requests
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

# Custom JSON encoder to handle non-serializable types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        # Handle numpy types
        if isinstance(o, (np.integer, np.int64, np.int32)):
            return int(o)
        elif isinstance(o, (np.floating, np.float64, np.float32)):
            return float(o)
        elif isinstance(o, (np.ndarray,)):
            return o.tolist()
        elif isinstance(o, (np.bool_)):
            return bool(o)
        # Handle datetime objects
        elif isinstance(o, datetime):
            return o.isoformat()
        # Handle native Python bool (for redundancy)
        elif isinstance(o, bool):
            return bool(o)
        # Let the base class handle other types or raise TypeError
        return super(CustomJSONEncoder, self).default(o)

class StockScreener:
    def __init__(self, api_key):
        """Initialize the stock screener with API key and base URLs"""
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.cache = {}
        self.cache_timeout = 3600  # 1 hour cache to avoid excessive API calls

    def _get_market_movers(self):
        """Get market movers from TwelveData API"""
        try:
            # Check if we already have market movers in cache
            cache_key = "market_movers"
            if cache_key in self.cache and (time.time() - self.cache[cache_key]['timestamp'] < self.cache_timeout):
                return self.cache[cache_key]['data']
                
            # Try to get market movers
            params = {
                "outputsize": 20,  # Get top 20 gainers
                "apikey": self.api_key
            }
            response = requests.get(f"{self.base_url}/market_movers/stocks", params=params, timeout=10)
            data = response.json()
            
            # Check for valid response
            if 'values' not in data or not data['values']:
                logger.warning("No market movers data available, using fallback list")
                return self._get_fallback_symbols()
                
            # Extract symbols from market movers
            symbols = [item['symbol'] for item in data['values'] if 'symbol' in item]
            
            # Add these symbols to cache
            self.cache[cache_key] = {
                'data': symbols,
                'timestamp': time.time()
            }
            
            return symbols
        except Exception as e:
            logger.warning(f"Error fetching market movers: {str(e)}, using fallback list")
            return self._get_fallback_symbols()
            
    def _get_sp500_symbols(self):
        """Get list of S&P 500 symbols"""
        try:
            # Only attempt to get symbols from Wikipedia if lxml is available
            try:
                # Using Wikipedia as a reliable source for S&P 500 constituents
                tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
                sp500 = tables[0]
                return sp500['Symbol'].str.replace('.', '-').tolist()
            except ImportError:
                # If lxml is not available, fallback to the hardcoded list
                logger.warning("lxml not available, falling back to hardcoded symbol list")
                raise Exception("Using fallback list")
        except Exception as e:
            logger.warning(f"Using fallback symbol list: {str(e)}")
            return self._get_fallback_symbols()
            
    def _get_nasdaq100_symbols(self):
        """Get list of Nasdaq 100 symbols"""
        try:
            try:
                # Using Wikipedia as a source for Nasdaq 100 constituents
                tables = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')
                nasdaq100 = tables[4]  # The table with the current constituents
                return nasdaq100['Ticker'].tolist()
            except (ImportError, IndexError):
                # If lxml is not available or table structure changed
                logger.warning("Could not get Nasdaq 100 symbols, using additional fallback")
                raise Exception("Using extended fallback list")
        except Exception as e:
            logger.warning(f"Using extended fallback list: {str(e)}")
            return self._get_extended_fallback_symbols()
            
    def _get_extended_fallback_symbols(self):
        """Return an extended fallback list of popular stocks"""
        return [
            # Tech stocks
            "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "NVDA", "AMD", "INTC", 
            "ADBE", "CSCO", "ORCL", "CRM", "PYPL", "NFLX", "IBM", "QCOM", "TXN", "AVGO",
            # Consumer stocks
            "PG", "KO", "PEP", "WMT", "COST", "TGT", "HD", "LOW", "MCD", "SBUX", 
            "NKE", "DIS", "CMCSA", "VZ", "T", "AMGN", "GILD", "ABT", "TMO", "DHR",
            # Financial stocks
            "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK", 
            "BRK-B", "USB", "PNC", "TFC", "COF", "SCHW", "CME", "ICE", "SPGI", "MCO",
            # Industrial stocks
            "GE", "HON", "MMM", "CAT", "DE", "BA", "LMT", "RTX", "UNP", "UPS", 
            "FDX", "CSX", "NSC", "ETN", "EMR", "ITW", "ROK", "GD", "NOC", "WM",
            # Energy stocks
            "XOM", "CVX", "COP", "EOG", "SLB", "PXD", "OXY", "MPC", "PSX", "VLO"
        ]
            
    def _get_fallback_symbols(self):
        """Return a fallback list of popular stocks"""
        return ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "AMD", "INTC", 
                "ADBE", "CSCO", "PYPL", "NFLX", "PEP", "KO", "DIS", "CMCSA", "T", "VZ", 
                "WMT", "HD", "MCD", "SBUX", "NKE", "PG", "JNJ", "PFE", "UNH", "V", "MA"]

    def _fetch_time_series_batch(self, symbols, interval="1day", outputsize=365, max_batch_size=8):
        """Fetch time series data for multiple symbols in batches"""
        results = {}
        
        # Process symbols in batches
        for i in range(0, len(symbols), max_batch_size):
            batch = symbols[i:i+max_batch_size]
            batch_results = self._fetch_time_series_for_batch(batch, interval, outputsize)
            if batch_results:
                results.update(batch_results)
                
        return results
    
    def _fetch_time_series_for_batch(self, symbols, interval="1day", outputsize=365):
        """Fetch time series data for a batch of symbols"""
        if not symbols:
            return {}
            
        # Initialize results dictionary - fixes unbound variable issue
        results = {}
            
        try:
            # Check if we're already rate limited
            if 'rate_limited' in self.cache and self.cache['rate_limited']:
                logger.warning(f"Skipping API call for batch of {len(symbols)} symbols due to rate limit")
                return {}
            
            # Convert symbols list to comma-separated string
            symbols_str = ','.join(symbols)
            logger.debug(f"Processing batch of {len(symbols)} symbols: {symbols_str}")
            
            # Try to use cached data first for each symbol
            all_cached = True
            
            for symbol in symbols:
                cache_key = f"timeseries_{symbol}_{interval}_{outputsize}"
                if cache_key in self.cache and (time.time() - self.cache[cache_key]['timestamp'] < self.cache_timeout):
                    results[symbol] = self.cache[cache_key]['data']
                else:
                    all_cached = False
            
            # If all symbols are cached, return the cached results
            if all_cached:
                logger.debug(f"Using cached data for all {len(symbols)} symbols in batch")
                return results
            
            # Make batch API request
            params = {
                "symbol": symbols_str,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": self.api_key
            }
            response = requests.get(f"{self.base_url}/time_series", params=params, timeout=15)
            data = response.json()
            
            # Check for rate limit error
            if isinstance(data, dict) and data.get('code') == 429:
                logger.warning(f"Rate limit exceeded: {data.get('message')}")
                # Mark that we've hit the rate limit to avoid further calls
                self.cache['rate_limited'] = True
                # Reset the rate limit flag after 60 seconds (typical rate limit window)
                self.cache['rate_limit_reset'] = time.time() + 60
                return results
            
            # Process the data - if single symbol, convert to expected format
            if len(symbols) == 1 and 'values' in data:
                symbol = symbols[0]
                try:
                    # Process single-symbol response
                    df = pd.DataFrame(data['values'])
                    # Convert columns to numeric
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col])
                    
                    # Reverse the dataframe to get ascending order by date
                    df = df.iloc[::-1].reset_index(drop=True)
                    
                    # Save to cache
                    cache_key = f"timeseries_{symbol}_{interval}_{outputsize}"
                    self.cache[cache_key] = {
                        'data': df,
                        'timestamp': time.time()
                    }
                    
                    results[symbol] = df
                except Exception as e:
                    logger.error(f"Error processing time series for {symbol}: {str(e)}")
            else:
                # Process multi-symbol response
                for symbol in symbols:
                    if symbol in data:
                        symbol_data = data[symbol]
                        
                        if 'values' not in symbol_data:
                            logger.warning(f"No time series data for {symbol}")
                            continue
                            
                        try:
                            df = pd.DataFrame(symbol_data['values'])
                            # Convert columns to numeric
                            for col in ['open', 'high', 'low', 'close', 'volume']:
                                if col in df.columns:
                                    df[col] = pd.to_numeric(df[col])
                            
                            # Reverse the dataframe to get ascending order by date
                            df = df.iloc[::-1].reset_index(drop=True)
                            
                            # Save to cache
                            cache_key = f"timeseries_{symbol}_{interval}_{outputsize}"
                            self.cache[cache_key] = {
                                'data': df,
                                'timestamp': time.time()
                            }
                            
                            results[symbol] = df
                        except Exception as e:
                            logger.error(f"Error processing time series for {symbol}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching time series batch: {str(e)}")
            return results
    
    def _fetch_time_series(self, symbol, interval="1day", outputsize=365):
        """Fetch time series data for a single symbol"""
        try:
            # Check if we're already rate limited
            if 'rate_limited' in self.cache and self.cache['rate_limited']:
                logger.warning(f"Skipping API call for {symbol} due to rate limit")
                return None
                
            # Try to use cached data first
            cache_key = f"timeseries_{symbol}_{interval}_{outputsize}"
            if cache_key in self.cache and (time.time() - self.cache[cache_key]['timestamp'] < self.cache_timeout):
                return self.cache[cache_key]['data']
            
            # Make API request
            params = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": self.api_key
            }
            response = requests.get(f"{self.base_url}/time_series", params=params, timeout=10)
            data = response.json()
            
            # Check for rate limit error
            if isinstance(data, dict) and data.get('code') == 429:
                logger.warning(f"Rate limit exceeded: {data.get('message')}")
                # Mark that we've hit the rate limit to avoid further calls
                self.cache['rate_limited'] = True
                # Reset the rate limit flag after 60 seconds (typical rate limit window)
                self.cache['rate_limit_reset'] = time.time() + 60
                return None
                
            # Check for valid data
            if 'values' not in data:
                logger.warning(f"No time series data for {symbol}: {data}")
                return None
                
            # Process the data
            df = pd.DataFrame(data['values'])
            # Convert columns to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col])
            
            # Reverse the dataframe to get ascending order by date
            df = df.iloc[::-1].reset_index(drop=True)
            
            # Save to cache
            self.cache[cache_key] = {
                'data': df,
                'timestamp': time.time()
            }
            
            return df
        except Exception as e:
            logger.error(f"Error fetching time series for {symbol}: {str(e)}")
            return None

    def _fetch_fundamentals(self, symbol):
        """Fetch fundamental data for a symbol"""
        try:
            # Check if we're already rate limited
            if 'rate_limited' in self.cache and self.cache['rate_limited']:
                logger.warning(f"Skipping fundamental API calls for {symbol} due to rate limit")
                return None
                
            # Check cache first
            cache_key = f"fundamentals_{symbol}"
            if cache_key in self.cache and (time.time() - self.cache[cache_key]['timestamp'] < self.cache_timeout):
                return self.cache[cache_key]['data']
            
            # Create a synthetic fundamental data object based on earnings and statistics
            # This is needed because the full 'fundamentals' endpoint may not be available in all API subscription levels
            fund_data = {
                'general': {'name': symbol},
                'income_statement': {'quarterly': []},
                'estimates': {'annual': {}}
            }
            
            # Try to get the company name from profile endpoint
            try:
                params = {
                    "symbol": symbol,
                    "apikey": self.api_key
                }
                response = requests.get(f"{self.base_url}/profile", params=params, timeout=10)
                data = response.json()
                
                # Check for rate limit
                if isinstance(data, dict) and data.get('code') == 429:
                    logger.warning(f"Rate limit exceeded: {data.get('message')}")
                    self.cache['rate_limited'] = True
                    self.cache['rate_limit_reset'] = time.time() + 60
                    return None
                
                if response.status_code == 200 and isinstance(data, dict) and 'name' in data:
                    fund_data['general']['name'] = data['name']
            except Exception as e:
                logger.warning(f"Could not get profile data for {symbol}: {str(e)}")
            
            # Check if we hit the rate limit
            if 'rate_limited' in self.cache and self.cache['rate_limited']:
                return None
                
            # Try to get growth estimates data - this provides more accurate growth numbers
            try:
                params = {
                    "symbol": symbol,
                    "apikey": self.api_key
                }
                response = requests.get(f"{self.base_url}/growth_estimates", params=params, timeout=10)
                growth_data = response.json()
                
                # Check for rate limit
                if isinstance(growth_data, dict) and growth_data.get('code') == 429:
                    logger.warning(f"Rate limit exceeded: {growth_data.get('message')}")
                    self.cache['rate_limited'] = True
                    self.cache['rate_limit_reset'] = time.time() + 60
                    return None
                
                # Extract growth estimates from the response
                if response.status_code == 200 and 'growth_estimates' in growth_data:
                    estimates = growth_data['growth_estimates']
                    # Convert from decimal to percentage
                    fund_data['estimates']['annual'] = {
                        'eps_growth': estimates.get('next_year', 0.05) * 100,
                        'revenue_growth': estimates.get('next_year', 0.05) * 100,
                        'current_quarter_growth': estimates.get('current_quarter', 0) * 100,
                        'next_quarter_growth': estimates.get('next_quarter', 0) * 100,
                        'current_year_growth': estimates.get('current_year', 0) * 100,
                        'next_5_years_growth': estimates.get('next_5_years_pa', 0) * 100
                    }
                    logger.debug(f"Successfully got growth estimates for {symbol}")
                else:
                    # Default values if growth estimates are not available
                    fund_data['estimates']['annual'] = {
                        'eps_growth': 5.0,
                        'revenue_growth': 5.0
                    }
            except Exception as e:
                logger.warning(f"Could not get growth estimates for {symbol}: {str(e)}")
                # Set default values if there's an error
                fund_data['estimates']['annual'] = {
                    'eps_growth': 5.0,
                    'revenue_growth': 5.0
                }
            
            # Check if we hit the rate limit
            if 'rate_limited' in self.cache and self.cache['rate_limited']:
                return None
                
            # Try to get earnings data
            try:
                params = {
                    "symbol": symbol,
                    "apikey": self.api_key
                }
                response = requests.get(f"{self.base_url}/earnings", params=params, timeout=10)
                earnings_data = response.json()
                
                # Check for rate limit
                if isinstance(earnings_data, dict) and earnings_data.get('code') == 429:
                    logger.warning(f"Rate limit exceeded: {earnings_data.get('message')}")
                    self.cache['rate_limited'] = True
                    self.cache['rate_limit_reset'] = time.time() + 60
                    return None
                
                if response.status_code == 200:
                    # Structure quarterly data
                    if earnings_data and 'earnings' in earnings_data and len(earnings_data['earnings']) >= 2:
                        quarterly = []
                        for i, quarter in enumerate(earnings_data['earnings'][:2]):
                            quarterly.append({
                                'revenue': quarter.get('revenue', 0),
                                'eps': quarter.get('eps', 0)
                            })
                        fund_data['income_statement']['quarterly'] = quarterly
            except Exception as e:
                logger.warning(f"Could not get earnings data for {symbol}: {str(e)}")
            
            # Check if we hit the rate limit
            if 'rate_limited' in self.cache and self.cache['rate_limited']:
                return None
                
            # Try to get statistics data for forecasts (as a fallback if growth estimates fails)
            if 'eps_growth' not in fund_data['estimates']['annual']:
                try:
                    params = {
                        "symbol": symbol,
                        "apikey": self.api_key
                    }
                    response = requests.get(f"{self.base_url}/statistics", params=params, timeout=10)
                    stats_data = response.json()
                    
                    # Check for rate limit
                    if isinstance(stats_data, dict) and stats_data.get('code') == 429:
                        logger.warning(f"Rate limit exceeded: {stats_data.get('message')}")
                        self.cache['rate_limited'] = True
                        self.cache['rate_limit_reset'] = time.time() + 60
                        return None
                    
                    if response.status_code == 200:
                        # Extract growth estimates
                        if stats_data and isinstance(stats_data, dict):
                            # These fields might not exist in all API plans
                            annual = fund_data['estimates']['annual']
                            if 'eps_estimate_next_year' in stats_data and 'eps_actual_previous_year' in stats_data:
                                est = float(stats_data.get('eps_estimate_next_year', 0) or 0)
                                prev = float(stats_data.get('eps_actual_previous_year', 0) or 0)
                                if prev != 0:
                                    annual['eps_growth'] = ((est / prev) - 1) * 100
                                else:
                                    annual['eps_growth'] = 0
                            
                            fund_data['estimates']['annual'] = annual
                except Exception as e:
                    logger.warning(f"Could not get statistics data for {symbol}: {str(e)}")
            
            # Even without all fundamental data, return what we have if we at least have growth estimates
            if len(fund_data['estimates']['annual']) > 0 or ('quarterly' in fund_data['income_statement'] and len(fund_data['income_statement']['quarterly']) >= 1):
                # Save to cache
                self.cache[cache_key] = {
                    'data': fund_data,
                    'timestamp': time.time()
                }
                return fund_data
            else:
                logger.warning(f"Insufficient fundamental data for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {str(e)}")
            return None

    def _calculate_sma(self, df, period):
        """Calculate simple moving average on DataFrame"""
        if df is None or len(df) < period:
            return None
        return df['close'].rolling(window=period).mean()

    def _calculate_sma_slope(self, sma_data, window=14):
        """Calculate the slope of the SMA over the last window periods"""
        if sma_data is None or len(sma_data) < window + 1:
            return None
        
        # Get the last window + 1 values (to calculate window slopes)
        recent_sma = sma_data.dropna().tail(window + 1).values
        
        if len(recent_sma) < window + 1:
            return None
            
        # Calculate the average rate of change per day
        slopes = [(recent_sma[i] - recent_sma[i-1]) for i in range(1, len(recent_sma))]
        avg_slope = np.mean(slopes)
        
        return avg_slope

    def _check_technical_criteria_batch(self, symbols, max_batch_size=8):
        """Check technical criteria for multiple symbols in batches"""
        results = {}
        
        # Fetch time series data for all symbols in batches
        time_series_data = self._fetch_time_series_batch(symbols, interval="1day", outputsize=365, max_batch_size=max_batch_size)
        
        # Process each symbol's data
        for symbol, df in time_series_data.items():
            if df is None or len(df) < 200:
                logger.warning(f"Insufficient time series data for {symbol}")
                results[symbol] = (False, {})
                continue
                
            try:
                # Calculate moving averages
                sma50 = self._calculate_sma(df, 50)
                sma100 = self._calculate_sma(df, 100)
                sma200 = self._calculate_sma(df, 200)
                
                if sma50 is None or sma100 is None or sma200 is None:
                    logger.warning(f"Couldn't calculate SMAs for {symbol}")
                    results[symbol] = (False, {})
                    continue
                
                # Get current closing price, SMAs, and SMA200 slope
                current_price = df['close'].iloc[-1]
                current_sma50 = sma50.iloc[-1]
                current_sma100 = sma100.iloc[-1]
                current_sma200 = sma200.iloc[-1]
                sma200_slope = self._calculate_sma_slope(sma200)
                
                # Check technical criteria
                criteria = {
                    "price_above_sma200": current_price > current_sma200,
                    "sma200_slope_positive": sma200_slope is not None and sma200_slope > 0,
                    "sma50_above_sma200": current_sma50 > current_sma200,
                    "sma100_above_sma200": current_sma100 > current_sma200
                }
                
                # Additional data for UI - convert numpy values to Python native floats
                metrics = {
                    "current_price": float(current_price),
                    "sma50": float(current_sma50),
                    "sma100": float(current_sma100),
                    "sma200": float(current_sma200),
                    "sma200_slope": float(sma200_slope) if sma200_slope is not None else None
                }
                
                # Check if all criteria are met
                meets_criteria = all(criteria.values())
                
                results[symbol] = (meets_criteria, {**criteria, **metrics})
            except Exception as e:
                logger.error(f"Error checking technical criteria for {symbol}: {str(e)}")
                results[symbol] = (False, {})
        
        return results
    
    def _check_technical_criteria(self, symbol):
        """Check if a stock meets the technical criteria"""
        df = self._fetch_time_series(symbol)
        if df is None or len(df) < 200:
            logger.warning(f"Insufficient time series data for {symbol}")
            return False, {}
        
        try:
            # Calculate moving averages
            sma50 = self._calculate_sma(df, 50)
            sma100 = self._calculate_sma(df, 100)
            sma200 = self._calculate_sma(df, 200)
            
            if sma50 is None or sma100 is None or sma200 is None:
                logger.warning(f"Couldn't calculate SMAs for {symbol}")
                return False, {}
            
            # Get current closing price, SMAs, and SMA200 slope
            current_price = df['close'].iloc[-1]
            current_sma50 = sma50.iloc[-1]
            current_sma100 = sma100.iloc[-1]
            current_sma200 = sma200.iloc[-1]
            sma200_slope = self._calculate_sma_slope(sma200)
            
            # Check technical criteria
            criteria = {
                "price_above_sma200": current_price > current_sma200,
                "sma200_slope_positive": sma200_slope is not None and sma200_slope > 0,
                "sma50_above_sma200": current_sma50 > current_sma200,
                "sma100_above_sma200": current_sma100 > current_sma200
            }
            
            # Additional data for UI - convert numpy values to Python native floats
            metrics = {
                "current_price": float(current_price),
                "sma50": float(current_sma50),
                "sma100": float(current_sma100),
                "sma200": float(current_sma200),
                "sma200_slope": float(sma200_slope) if sma200_slope is not None else None
            }
            
            # Check if all criteria are met
            meets_criteria = all(criteria.values())
            
            return meets_criteria, {**criteria, **metrics}
        except Exception as e:
            logger.error(f"Error checking technical criteria for {symbol}: {str(e)}")
            return False, {}

    def _check_fundamental_criteria(self, symbol):
        """Check if a stock meets the fundamental criteria"""
        fundamentals = self._fetch_fundamentals(symbol)
        if not fundamentals:
            logger.warning(f"No fundamental data for {symbol}")
            return False, {}
        
        try:
            # Extract needed metrics
            income_statement = fundamentals.get('income_statement', {})
            estimates = fundamentals.get('estimates', {})
            
            # Get quarterly data
            quarterly = income_statement.get('quarterly', [])
            if not quarterly or len(quarterly) < 2:
                logger.warning(f"Insufficient quarterly data for {symbol}")
                return False, {}
                
            # Calculate quarterly growth rates
            current_q = quarterly[0]
            prev_q = quarterly[1]
            
            # Revenue growth
            curr_q_revenue = float(current_q.get('revenue', 0) or 0)
            prev_q_revenue = float(prev_q.get('revenue', 0) or 0)
            q_revenue_growth = ((curr_q_revenue / prev_q_revenue) - 1) * 100 if prev_q_revenue else 0
            
            # EPS growth
            curr_q_eps = float(current_q.get('eps', 0) or 0)
            prev_q_eps = float(prev_q.get('eps', 0) or 0)
            q_eps_growth = ((curr_q_eps / prev_q_eps) - 1) * 100 if prev_q_eps else 0
            
            # Get estimates
            annual_estimates = estimates.get('annual', {})
            sales_growth_est = float(annual_estimates.get('revenue_growth', 0) or 0)
            eps_growth_est = float(annual_estimates.get('eps_growth', 0) or 0)
            
            # Check fundamental criteria - less strict requirements
            # Instead of requiring ALL criteria, we only require at least 3 out of 4 to be positive
            criteria = {
                "quarterly_sales_growth_positive": q_revenue_growth > 0,
                "quarterly_eps_growth_positive": q_eps_growth > 0,
                "estimated_sales_growth_positive": sales_growth_est > 0,
                "estimated_eps_growth_positive": eps_growth_est > 0
            }
            
            # Additional data for UI - convert values to native Python types
            metrics = {
                "quarterly_sales_growth": float(q_revenue_growth),
                "quarterly_eps_growth": float(q_eps_growth),
                "estimated_sales_growth": float(sales_growth_est),
                "estimated_eps_growth": float(eps_growth_est),
                "company_name": fundamentals.get('general', {}).get('name', symbol)
            }
            
            # Add extra growth metrics if available - convert to Python native types
            if 'annual' in estimates:
                annual_data = estimates['annual']
                if 'current_quarter_growth' in annual_data:
                    metrics['current_quarter_growth'] = float(annual_data['current_quarter_growth'] or 0)
                if 'next_quarter_growth' in annual_data:
                    metrics['next_quarter_growth'] = float(annual_data['next_quarter_growth'] or 0)
                if 'current_year_growth' in annual_data:
                    metrics['current_year_growth'] = float(annual_data['current_year_growth'] or 0)
                if 'next_5_years_growth' in annual_data:
                    metrics['next_5_years_growth'] = float(annual_data['next_5_years_growth'] or 0)
            
            # Make criteria even more flexible for screening: 
            # Accept if at least 2 out of 4 criteria are met OR if growth rate shows promise
            positive_count = sum(1 for value in criteria.values() if value)
            
            # Count both exceptional growth and even moderate growth
            exceptional_growth = any([
                q_revenue_growth > 20,       # Exceptional revenue growth
                q_eps_growth > 20,           # Exceptional EPS growth
                sales_growth_est > 15,       # Strong estimated sales growth
                eps_growth_est > 15          # Strong estimated EPS growth
            ])
            
            moderate_growth = any([
                q_revenue_growth > 10,       # Good revenue growth
                q_eps_growth > 10,           # Good EPS growth
                sales_growth_est > 5,        # Decent estimated sales growth
                eps_growth_est > 5           # Decent estimated EPS growth
            ])
            
            # Accept stocks with either:
            # 1. At least 2/4 positive metrics (was 3/4 before)
            # 2. Exceptional growth in any category
            # 3. Moderate growth in ANY category + at least 1 positive metric
            meets_criteria = (positive_count >= 2 or 
                             exceptional_growth or 
                             (moderate_growth and positive_count >= 1))
            
            # Detailed logging to understand which criteria are being met/missed
            logger.debug(
                f"{symbol} metrics: {positive_count}/4 positive, exceptional: {exceptional_growth}, "
                f"moderate: {moderate_growth}, CRITERIA MET: {meets_criteria}, "
                f"q_rev_growth: {q_revenue_growth:.1f}%, q_eps_growth: {q_eps_growth:.1f}%, "
                f"est_sales_growth: {sales_growth_est:.1f}%, est_eps_growth: {eps_growth_est:.1f}%"
            )
            
            return meets_criteria, {**criteria, **metrics}
        except Exception as e:
            logger.error(f"Error checking fundamental criteria for {symbol}: {str(e)}")
            return False, {}

    def _prepare_chart_data(self, symbol):
        """Prepare chart data for a stock"""
        df = self._fetch_time_series(symbol, outputsize=200)
        if df is None:
            return None

        # Calculate moving averages for the chart
        df['sma50'] = self._calculate_sma(df, 50)
        df['sma100'] = self._calculate_sma(df, 100)
        df['sma200'] = self._calculate_sma(df, 200)
        
        # Format data for Chart.js - convert pandas series to Python native types
        chart_data = {
            "dates": [str(d) for d in df['datetime'].tolist()],
            "prices": [float(p) if pd.notna(p) else None for p in df['close'].tolist()],
            "sma50": [float(p) if pd.notna(p) else None for p in df['sma50'].tolist()],
            "sma100": [float(p) if pd.notna(p) else None for p in df['sma100'].tolist()],
            "sma200": [float(p) if pd.notna(p) else None for p in df['sma200'].tolist()]
        }
        
        return chart_data

    def get_stock_details(self, symbol):
        """Get detailed data for a stock"""
        technical_passed, technical_data = self._check_technical_criteria(symbol)
        fundamental_passed, fundamental_data = self._check_fundamental_criteria(symbol)
        chart_data = self._prepare_chart_data(symbol)
        
        return {
            "symbol": symbol,
            "company_name": fundamental_data.get("company_name", symbol),
            "technical_data": technical_data,
            "fundamental_data": fundamental_data,
            "chart_data": chart_data,
            "passes_all_criteria": technical_passed and fundamental_passed
        }

    def get_top_stocks(self, limit=10):
        """Get the top stocks based on the screening criteria using batch processing"""
        # Safety check for API key
        if not self.api_key:
            logger.error("No TwelveData API key provided")
            return []
            
        # First, try to get market movers which are likely to be trending stocks
        market_movers = self._get_market_movers()
        
        # Then get S&P 500 and Nasdaq 100 stocks for a comprehensive coverage
        sp500_symbols = self._get_sp500_symbols()
        nasdaq100_symbols = self._get_nasdaq100_symbols()
        
        # Combine symbols with priority: market movers, then S&P 500, then Nasdaq 100
        combined_symbols = []
        
        # Helper to filter out warrant symbols (typically end with W)
        def is_regular_stock(symbol):
            # Filter out warrants, rights, units, and preferred shares
            if symbol.endswith(('W', 'R', 'U', 'P')):
                return False
            # Also filter out symbols with unusual formats that might be special securities
            if '-' in symbol or '.' in symbol:
                return False
            return True
        
        # Add market movers first (filtered)
        for symbol in market_movers:
            if symbol not in combined_symbols and is_regular_stock(symbol):
                combined_symbols.append(symbol)
                
        # Then add S&P 500 stocks 
        for symbol in sp500_symbols:
            if symbol not in combined_symbols and is_regular_stock(symbol):
                combined_symbols.append(symbol)
                
        # Then add Nasdaq 100 stocks
        for symbol in nasdaq100_symbols:
            if symbol not in combined_symbols and is_regular_stock(symbol):
                combined_symbols.append(symbol)
                
        # With batching we can process more symbols efficiently
        # Increased from 30 to 50 for better coverage while still being API-efficient
        max_symbols = min(50, len(combined_symbols))
        symbols = combined_symbols[:max_symbols]
        logger.debug(f"Got {len(symbols)} symbols for batch screening [{', '.join(symbols[:5])}...]")
        
        qualified_stocks = []
        batch_size = 8  # Maximum symbols per batch for TwelveData free tier
        
        # STEP 1: First batch-screen all symbols for technical criteria
        logger.debug(f"Starting technical batch screening for {len(symbols)} symbols")
        technical_results = self._check_technical_criteria_batch(symbols, max_batch_size=batch_size)
        
        # STEP 2: Filter symbols that passed technical criteria
        technical_passed_symbols = []
        seen_symbols = set()  # Track symbols to prevent duplicates
        for symbol, (passed, tech_data) in technical_results.items():
            if passed and symbol not in seen_symbols:
                technical_passed_symbols.append((symbol, tech_data))
                seen_symbols.add(symbol)
        
        logger.debug(f"{len(technical_passed_symbols)} symbols passed technical criteria")
        
        # If no symbols passed technical criteria, return early
        if not technical_passed_symbols:
            logger.warning("No stocks passed technical criteria")
            return []
        
        # STEP 3: For each symbol that passed technical screening, check fundamentals individually
        # This is necessary because the TwelveData API doesn't support batch fundamentals
        processed_count = 0
        for symbol, technical_data in technical_passed_symbols:
            try:
                logger.debug(f"Checking fundamentals for {symbol}")
                fundamental_passed, fundamental_data = self._check_fundamental_criteria(symbol)
                processed_count += 1
                
                # If a 429 rate limit error occurred, return early with what we have
                if 'rate_limited' in self.cache and self.cache['rate_limited']:
                    logger.warning("API rate limit reached, returning partial results")
                    break
                
                # If both technical and fundamental criteria are met
                if fundamental_passed:
                    chart_data = self._prepare_chart_data(symbol)
                    
                    # Create a score based on growth metrics for ranking
                    score = float(
                        float(fundamental_data.get("quarterly_sales_growth", 0)) +
                        float(fundamental_data.get("quarterly_eps_growth", 0)) +
                        float(fundamental_data.get("estimated_sales_growth", 0)) +
                        float(fundamental_data.get("estimated_eps_growth", 0)) +
                        (float(technical_data.get("sma200_slope", 0)) * 100)  # Give weight to slope
                    )
                    
                    qualified_stocks.append({
                        "symbol": symbol,
                        "company_name": fundamental_data.get("company_name", symbol),
                        "score": score,
                        "technical_data": technical_data,
                        "fundamental_data": fundamental_data,
                        "chart_data": chart_data
                    })
                    
                    logger.debug(f"Stock {symbol} qualified with score {score}")
                    
                    # If we have enough qualifying stocks, we can stop screening
                    if len(qualified_stocks) >= limit:
                        break
            except Exception as e:
                logger.error(f"Error processing fundamentals for {symbol}: {str(e)}")
                continue
        
        # Sort and limit to top stocks
        if qualified_stocks:
            qualified_stocks = sorted(qualified_stocks, key=lambda x: x.get("score", 0), reverse=True)[:limit]
        
        # If we don't have enough qualified stocks, return what we have
        if not qualified_stocks:
            logger.warning("No stocks qualified for the screening criteria")
            
        return qualified_stocks
