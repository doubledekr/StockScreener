import os
import logging
import requests
import json
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from stock_screener import StockScreener
from models import db, Stock, PriceHistory, StockFundamentals, ScreeningResult, ScreeningSession
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle non-serializable types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle numpy types
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, (np.bool_)):
            return bool(obj)
        # Handle datetime objects
        elif isinstance(obj, datetime):
            return obj.isoformat()
        # Let the base class handle other types or raise TypeError
        return super(CustomJSONEncoder, self).default(obj)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")
app.json_encoder = CustomJSONEncoder  # Use our custom encoder for all JSON responses

# Configure database with proper connection settings for stability
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,  # Test connection before use to prevent stale connections
    "pool_recycle": 300,    # Recycle connections after 5 minutes
    "pool_timeout": 30,     # Connection timeout after 30 seconds
    "pool_size": 10,        # Maximum number of connections in the pool
    "max_overflow": 20      # Maximum number of overflow connections
}
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Initialize stock screener
screener = StockScreener(api_key=os.environ.get("TWELVEDATA_API_KEY", ""))

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')
    
@app.route('/api/market_movers')
def get_market_movers():
    """Get the current market movers"""
    try:
        logger.debug("Fetching market movers")
        
        # Check if we have cached results that are less than 15 mins old
        cache_date = datetime.utcnow() - timedelta(minutes=15)
        if hasattr(app, 'cached_market_movers') and hasattr(app, 'market_movers_timestamp'):
            if app.market_movers_timestamp >= cache_date:
                logger.debug("Using cached market movers")
                return jsonify({"success": True, "market_movers": app.cached_market_movers})
            
        # Fetch market movers directly from API
        params = {
            "outputsize": 10,  # Limit to top 10
            "apikey": os.environ.get('TWELVEDATA_API_KEY')
        }
        response = requests.get("https://api.twelvedata.com/market_movers/stocks", params=params, timeout=10)
        data = response.json()
        
        # Format the results for display
        market_movers = []
        symbols_to_prefetch = []
        
        if 'values' in data and data['values']:
            for item in data['values']:
                symbol = item.get('symbol', '')
                market_movers.append({
                    'symbol': symbol,
                    'name': item.get('name', ''),
                    'last_price': item.get('last', 0),
                    'change': item.get('change', 0),
                    'percent_change': item.get('percent_change', 0)
                })
                
                # Add to prefetch list
                if symbol:
                    symbols_to_prefetch.append(symbol)
                    
        # Prefetch data for all market movers to ensure detailed views work
        if symbols_to_prefetch:
            logger.debug(f"Pre-fetching data for {len(symbols_to_prefetch)} market mover symbols")
            
            # Always fetch fresh data for market movers to ensure we have the latest
            for symbol in symbols_to_prefetch:
                try:
                    # Check if we already have data for this stock
                    stock = Stock.query.filter_by(symbol=symbol).first()
                    
                    # For market movers, always get fresh data if older than 1 hour
                    needs_refresh = True
                    if stock:
                        # Check if we have recent data (last hour)
                        recent_result = ScreeningResult.query.filter(
                            ScreeningResult.stock_id == stock.id,
                            ScreeningResult.screening_date >= (datetime.utcnow() - timedelta(hours=1))
                        ).first()
                        if recent_result:
                            needs_refresh = False
                    
                    if needs_refresh:
                        # Fetch detailed data for this symbol
                        logger.debug(f"Pre-fetching details for {symbol}")
                        stock_data = screener.get_stock_details(symbol)
                        
                        # Save to database
                        if stock_data:
                            # Find or create the stock
                            if not stock:
                                stock = Stock(
                                    symbol=symbol,
                                    company_name=stock_data.get("company_name", symbol)
                                )
                                db.session.add(stock)
                                db.session.flush()
                            else:
                                stock.company_name = stock_data.get("company_name", symbol)
                                stock.last_updated = datetime.utcnow()
                            
                            # Create technical/fundamental results - convert numpy values to native Python types
                            tech_data = stock_data.get("technical_data", {})
                            fund_data = stock_data.get("fundamental_data", {})
                            
                            # Get values with proper type conversion
                            current_price = float(tech_data.get("current_price", 0)) if tech_data.get("current_price") is not None else None
                            sma50 = float(tech_data.get("sma50", 0)) if tech_data.get("sma50") is not None else None
                            sma100 = float(tech_data.get("sma100", 0)) if tech_data.get("sma100") is not None else None
                            sma200 = float(tech_data.get("sma200", 0)) if tech_data.get("sma200") is not None else None
                            sma200_slope = float(tech_data.get("sma200_slope", 0)) if tech_data.get("sma200_slope") is not None else None
                            
                            result = ScreeningResult(
                                stock_id=stock.id,
                                current_price=current_price,
                                sma50=sma50,
                                sma100=sma100,
                                sma200=sma200,
                                sma200_slope=sma200_slope,
                                price_above_sma200=tech_data.get("price_above_sma200", False),
                                sma200_slope_positive=tech_data.get("sma200_slope_positive", False),
                                sma50_above_sma200=tech_data.get("sma50_above_sma200", False),
                                sma100_above_sma200=tech_data.get("sma100_above_sma200", False),
                                quarterly_sales_growth_positive=fund_data.get("quarterly_sales_growth_positive", False),
                                quarterly_eps_growth_positive=fund_data.get("quarterly_eps_growth_positive", False),
                                estimated_sales_growth_positive=fund_data.get("estimated_sales_growth_positive", False),
                                estimated_eps_growth_positive=fund_data.get("estimated_eps_growth_positive", False)
                            )
                            
                            # Set chart data
                            if "chart_data" in stock_data:
                                result.set_chart_data(stock_data["chart_data"])
                            
                            db.session.add(result)
                            
                            # Store fundamental data
                            if fund_data:
                                fundamental = StockFundamentals.query.filter_by(stock_id=stock.id).first()
                                if not fundamental:
                                    fundamental = StockFundamentals(stock_id=stock.id)
                                    db.session.add(fundamental)
                                
                                # Convert any numpy values to Python native types
                                quarterly_revenue_growth = float(fund_data.get("quarterly_sales_growth", 0)) if fund_data.get("quarterly_sales_growth") is not None else None
                                quarterly_eps_growth = float(fund_data.get("quarterly_eps_growth", 0)) if fund_data.get("quarterly_eps_growth") is not None else None
                                estimated_sales_growth = float(fund_data.get("estimated_sales_growth", 0)) if fund_data.get("estimated_sales_growth") is not None else None
                                estimated_eps_growth = float(fund_data.get("estimated_eps_growth", 0)) if fund_data.get("estimated_eps_growth") is not None else None
                                
                                fundamental.quarterly_revenue_growth = quarterly_revenue_growth
                                fundamental.quarterly_eps_growth = quarterly_eps_growth
                                fundamental.estimated_sales_growth = estimated_sales_growth
                                fundamental.estimated_eps_growth = estimated_eps_growth
                                fundamental.last_updated = datetime.utcnow()
                                
                                # Store the raw data for advanced metrics
                                raw_data = {
                                    'general': {'name': stock.company_name},
                                    'estimates': {'annual': {}}
                                }
                                
                                # Include all available growth metrics in the raw data - convert to native Python types
                                annual_estimates = raw_data['estimates']['annual']
                                annual_estimates['eps_growth'] = float(fund_data.get("estimated_eps_growth", 0)) if fund_data.get("estimated_eps_growth") is not None else 0
                                annual_estimates['revenue_growth'] = float(fund_data.get("estimated_sales_growth", 0)) if fund_data.get("estimated_sales_growth") is not None else 0
                                
                                if 'current_quarter_growth' in fund_data:
                                    annual_estimates['current_quarter_growth'] = float(fund_data.get("current_quarter_growth", 0)) if fund_data.get("current_quarter_growth") is not None else 0
                                if 'next_quarter_growth' in fund_data:
                                    annual_estimates['next_quarter_growth'] = float(fund_data.get("next_quarter_growth", 0)) if fund_data.get("next_quarter_growth") is not None else 0
                                if 'current_year_growth' in fund_data:
                                    annual_estimates['current_year_growth'] = float(fund_data.get("current_year_growth", 0)) if fund_data.get("current_year_growth") is not None else 0
                                if 'next_5_years_growth' in fund_data:
                                    annual_estimates['next_5_years_growth'] = float(fund_data.get("next_5_years_growth", 0)) if fund_data.get("next_5_years_growth") is not None else 0
                                    
                                # Save the raw data
                                fundamental.set_raw_data(raw_data)
                except Exception as e:
                    logger.warning(f"Error pre-fetching details for {symbol}: {str(e)}")
                    # Continue with the next symbol
                    continue
            
            # Commit all database changes
            db.session.commit()
                
        # Cache the results
        app.cached_market_movers = market_movers
        app.market_movers_timestamp = datetime.utcnow()
        
        return jsonify({"success": True, "market_movers": market_movers})
    except Exception as e:
        logger.error(f"Error fetching market movers: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/screen')
def screen_stocks():
    """Run the stock screening process and return results"""
    try:
        logger.debug("Starting stock screening process")
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        cache_hours = int(request.args.get('cache_hours', 24))  # Default cache validity: 24 hours
        
        # Check if we have recent cached results
        if use_cache:
            try:
                cache_date = datetime.utcnow() - timedelta(hours=cache_hours)
                
                # Use a subquery to get the most recent screening result for each stock
                subquery = db.session.query(
                    ScreeningResult.stock_id,
                    db.func.max(ScreeningResult.screening_date).label('max_date')
                ).filter(
                    ScreeningResult.passes_all_criteria == True,
                    ScreeningResult.screening_date >= cache_date
                ).group_by(ScreeningResult.stock_id).subquery()
                
                # Join with the subquery to get only the most recent result per stock
                recent_results = ScreeningResult.query.join(
                    subquery,
                    db.and_(
                        ScreeningResult.stock_id == subquery.c.stock_id,
                        ScreeningResult.screening_date == subquery.c.max_date
                    )
                ).join(Stock).order_by(ScreeningResult.score.desc()).limit(50).all()
            except Exception as e:
                logger.error(f"Error getting cached screening results: {str(e)}")
                # Fallback to a more basic query if the subquery approach fails
                recent_results = []
            
            if recent_results:
                logger.debug(f"Using cached screening results from database ({len(recent_results)} stocks)")
                top_stocks = []
                
                for result in recent_results:
                    stock = result.stock
                    chart_data = result.get_chart_data()
                    
                    stock_data = {
                        "symbol": stock.symbol,
                        "company_name": stock.company_name,
                        "score": result.score,
                        "technical_data": {
                            "current_price": result.current_price,
                            "sma50": result.sma50,
                            "sma100": result.sma100,
                            "sma200": result.sma200,
                            "sma200_slope": result.sma200_slope,
                            "price_above_sma200": result.price_above_sma200,
                            "sma200_slope_positive": result.sma200_slope_positive,
                            "sma50_above_sma200": result.sma50_above_sma200,
                            "sma100_above_sma200": result.sma100_above_sma200
                        },
                        "fundamental_data": {
                            "quarterly_sales_growth": 0,
                            "quarterly_eps_growth": 0,
                            "estimated_sales_growth": 0,
                            "estimated_eps_growth": 0,
                            "quarterly_sales_growth_positive": result.quarterly_sales_growth_positive,
                            "quarterly_eps_growth_positive": result.quarterly_eps_growth_positive,
                            "estimated_sales_growth_positive": result.estimated_sales_growth_positive,
                            "estimated_eps_growth_positive": result.estimated_eps_growth_positive
                        },
                        "chart_data": chart_data
                    }
                    
                    # If we have fundamental data, use it
                    fundamentals = StockFundamentals.query.filter_by(stock_id=stock.id).first()
                    if fundamentals:
                        stock_data["fundamental_data"].update({
                            "quarterly_sales_growth": fundamentals.quarterly_revenue_growth,
                            "quarterly_eps_growth": fundamentals.quarterly_eps_growth,
                            "estimated_sales_growth": fundamentals.estimated_sales_growth,
                            "estimated_eps_growth": fundamentals.estimated_eps_growth
                        })
                        
                        # Add additional growth metrics from raw data if available
                        raw_data = fundamentals.get_raw_data()
                        if raw_data and 'estimates' in raw_data and 'annual' in raw_data['estimates']:
                            annual_estimates = raw_data['estimates']['annual']
                            if 'current_quarter_growth' in annual_estimates:
                                stock_data["fundamental_data"]["current_quarter_growth"] = annual_estimates['current_quarter_growth']
                            if 'next_quarter_growth' in annual_estimates:
                                stock_data["fundamental_data"]["next_quarter_growth"] = annual_estimates['next_quarter_growth']
                            if 'current_year_growth' in annual_estimates:
                                stock_data["fundamental_data"]["current_year_growth"] = annual_estimates['current_year_growth']
                            if 'next_5_years_growth' in annual_estimates:
                                stock_data["fundamental_data"]["next_5_years_growth"] = annual_estimates['next_5_years_growth']
                    
                    top_stocks.append(stock_data)
                
                return jsonify({"success": True, "stocks": top_stocks, "cached": True})
                
        # Start timing the screening process
        start_time = time.time()
        
        # Get top stocks based on criteria from the API with improved batch processing
        logger.debug("No cached results or cache bypass requested, fetching from API")
        symbol_limit = int(request.args.get('symbol_limit', 200))  # Allow overriding the symbol limit
        top_stocks = screener.get_top_stocks(limit=50)  # Increased to get top 50 stocks
        
        # Record screening metrics
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"Screening completed in {execution_time:.2f} seconds, found {len(top_stocks)} qualified stocks")
        
        # Create a new screening session record
        session = ScreeningSession(
            qualified_count=len(top_stocks),
            execution_time=execution_time
        )
        db.session.add(session)
        
        # Save the results to the database
        for stock_data in top_stocks:
            symbol = stock_data["symbol"]
            
            # Find or create the stock
            stock = Stock.query.filter_by(symbol=symbol).first()
            if not stock:
                stock = Stock(
                    symbol=symbol,
                    company_name=stock_data["company_name"]
                )
                db.session.add(stock)
                db.session.flush()  # Get the stock ID without committing
            else:
                # Update company name if it changed
                stock.company_name = stock_data["company_name"]
                stock.last_updated = datetime.utcnow()
            
            # Create or update screening result
            tech_data = stock_data["technical_data"]
            fund_data = stock_data["fundamental_data"]
            
            # Create a new screening result
            result = ScreeningResult(
                stock_id=stock.id,
                current_price=tech_data.get("current_price"),
                sma50=tech_data.get("sma50"),
                sma100=tech_data.get("sma100"),
                sma200=tech_data.get("sma200"),
                sma200_slope=tech_data.get("sma200_slope"),
                price_above_sma200=tech_data.get("price_above_sma200", False),
                sma200_slope_positive=tech_data.get("sma200_slope_positive", False),
                sma50_above_sma200=tech_data.get("sma50_above_sma200", False),
                sma100_above_sma200=tech_data.get("sma100_above_sma200", False),
                quarterly_sales_growth_positive=fund_data.get("quarterly_sales_growth_positive", False),
                quarterly_eps_growth_positive=fund_data.get("quarterly_eps_growth_positive", False),
                estimated_sales_growth_positive=fund_data.get("estimated_sales_growth_positive", False),
                estimated_eps_growth_positive=fund_data.get("estimated_eps_growth_positive", False),
                score=stock_data.get("score", 0),
                passes_all_criteria=True,
                meets_all_criteria=stock_data.get("meets_all_criteria", False)
            )
            
            # Set chart data
            if "chart_data" in stock_data:
                result.set_chart_data(stock_data["chart_data"])
            
            db.session.add(result)
            
            # Store fundamental data
            if fund_data:
                fundamental = StockFundamentals.query.filter_by(stock_id=stock.id).first()
                if not fundamental:
                    fundamental = StockFundamentals(stock_id=stock.id)
                    db.session.add(fundamental)
                
                fundamental.quarterly_revenue_growth = fund_data.get("quarterly_sales_growth")
                fundamental.quarterly_eps_growth = fund_data.get("quarterly_eps_growth")
                fundamental.estimated_sales_growth = fund_data.get("estimated_sales_growth")
                fundamental.estimated_eps_growth = fund_data.get("estimated_eps_growth")
                fundamental.last_updated = datetime.utcnow()
                
                # Store the raw data for advanced metrics
                raw_data = {
                    'general': {'name': stock.company_name},
                    'estimates': {'annual': {}}
                }
                
                # Include all available growth metrics in the raw data
                annual_estimates = raw_data['estimates']['annual']
                annual_estimates['eps_growth'] = fund_data.get("estimated_eps_growth", 0)
                annual_estimates['revenue_growth'] = fund_data.get("estimated_sales_growth", 0)
                
                if 'current_quarter_growth' in fund_data:
                    annual_estimates['current_quarter_growth'] = fund_data.get("current_quarter_growth")
                if 'next_quarter_growth' in fund_data:
                    annual_estimates['next_quarter_growth'] = fund_data.get("next_quarter_growth")
                if 'current_year_growth' in fund_data:
                    annual_estimates['current_year_growth'] = fund_data.get("current_year_growth")
                if 'next_5_years_growth' in fund_data:
                    annual_estimates['next_5_years_growth'] = fund_data.get("next_5_years_growth")
                    
                # Save the raw data
                fundamental.set_raw_data(raw_data)
        
        # Commit all database changes
        db.session.commit()
        
        # Process top_stocks to ensure all boolean values are properly converted
        for stock in top_stocks:
            if "technical_data" in stock:
                for key, value in stock["technical_data"].items():
                    if isinstance(value, bool):
                        stock["technical_data"][key] = bool(value)
            if "fundamental_data" in stock:
                for key, value in stock["fundamental_data"].items():
                    if isinstance(value, bool):
                        stock["fundamental_data"][key] = bool(value)
        
        # Use the custom encoder for this response
        return json.dumps({"success": True, "stocks": top_stocks, "cached": False}, cls=CustomJSONEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Error in stock screening: {str(e)}")
        db.session.rollback()
        return json.dumps({"success": False, "error": str(e)}, cls=CustomJSONEncoder), 500, {'Content-Type': 'application/json'}

@app.route('/api/stock/<symbol>')
def get_stock_data(symbol):
    """Get detailed data for a specific stock"""
    try:
        logger.debug(f"Fetching data for stock: {symbol}")
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        cache_hours = int(request.args.get('cache_hours', 12))  # Default cache validity: 12 hours
        
        # Check if we have recent cached data for this stock
        if use_cache:
            cache_date = datetime.utcnow() - timedelta(hours=cache_hours)
            stock = Stock.query.filter_by(symbol=symbol).first()
            
            if stock:
                result = ScreeningResult.query.filter(
                    ScreeningResult.stock_id == stock.id,
                    ScreeningResult.screening_date >= cache_date
                ).order_by(ScreeningResult.screening_date.desc()).first()
                
                if result:
                    logger.debug(f"Using cached data for {symbol} from database")
                    # Convert all data to JSON-serializable formats
                    stock_data = {
                        "symbol": symbol,
                        "company_name": stock.company_name,
                        "technical_data": {
                            "current_price": float(result.current_price) if result.current_price is not None else None,
                            "sma50": float(result.sma50) if result.sma50 is not None else None, 
                            "sma100": float(result.sma100) if result.sma100 is not None else None,
                            "sma200": float(result.sma200) if result.sma200 is not None else None,
                            "sma200_slope": float(result.sma200_slope) if result.sma200_slope is not None else None,
                            "price_above_sma200": bool(result.price_above_sma200),
                            "sma200_slope_positive": bool(result.sma200_slope_positive),
                            "sma50_above_sma200": bool(result.sma50_above_sma200),
                            "sma100_above_sma200": bool(result.sma100_above_sma200)
                        },
                        "fundamental_data": {
                            "quarterly_sales_growth_positive": bool(result.quarterly_sales_growth_positive),
                            "quarterly_eps_growth_positive": bool(result.quarterly_eps_growth_positive),
                            "estimated_sales_growth_positive": bool(result.estimated_sales_growth_positive),
                            "estimated_eps_growth_positive": bool(result.estimated_eps_growth_positive)
                        },
                        "chart_data": result.get_chart_data(),
                        "passes_all_criteria": bool(result.passes_all_criteria),
                        "meets_all_criteria": bool(result.meets_all_criteria)
                    }
                    
                    # Add fundamental metrics if available
                    fundamental = StockFundamentals.query.filter_by(stock_id=stock.id).first()
                    if fundamental:
                        stock_data["fundamental_data"].update({
                            "quarterly_sales_growth": float(fundamental.quarterly_revenue_growth) if fundamental.quarterly_revenue_growth is not None else None,
                            "quarterly_eps_growth": float(fundamental.quarterly_eps_growth) if fundamental.quarterly_eps_growth is not None else None,
                            "estimated_sales_growth": float(fundamental.estimated_sales_growth) if fundamental.estimated_sales_growth is not None else None,
                            "estimated_eps_growth": float(fundamental.estimated_eps_growth) if fundamental.estimated_eps_growth is not None else None,
                            "company_name": stock.company_name
                        })
                        
                        # Add additional growth metrics from raw data if available
                        raw_data = fundamental.get_raw_data()
                        if raw_data and 'estimates' in raw_data and 'annual' in raw_data['estimates']:
                            annual_estimates = raw_data['estimates']['annual']
                            if 'current_quarter_growth' in annual_estimates:
                                stock_data["fundamental_data"]["current_quarter_growth"] = float(annual_estimates['current_quarter_growth']) if annual_estimates['current_quarter_growth'] is not None else None
                            if 'next_quarter_growth' in annual_estimates:
                                stock_data["fundamental_data"]["next_quarter_growth"] = float(annual_estimates['next_quarter_growth']) if annual_estimates['next_quarter_growth'] is not None else None
                            if 'current_year_growth' in annual_estimates:
                                stock_data["fundamental_data"]["current_year_growth"] = float(annual_estimates['current_year_growth']) if annual_estimates['current_year_growth'] is not None else None
                            if 'next_5_years_growth' in annual_estimates:
                                stock_data["fundamental_data"]["next_5_years_growth"] = float(annual_estimates['next_5_years_growth']) if annual_estimates['next_5_years_growth'] is not None else None
                    
                    # Use the custom encoder for this response
                    return json.dumps({"success": True, "data": stock_data, "cached": True}, cls=CustomJSONEncoder), 200, {'Content-Type': 'application/json'}
        
        # If no cache or cache miss, fetch from API
        logger.debug(f"Fetching fresh data for {symbol} from API")
        api_stock_data = screener.get_stock_details(symbol)
        
        # Ensure all values are JSON serializable before returning
        stock_data = {}
        if api_stock_data:
            # Make a deep copy with all native Python types
            stock_data = {
                "symbol": symbol,
                "company_name": api_stock_data.get("company_name", symbol),
                "technical_data": {},
                "fundamental_data": {},
                "passes_all_criteria": bool(api_stock_data.get("passes_all_criteria", False)),
                "meets_all_criteria": bool(api_stock_data.get("meets_all_criteria", False))
            }
            
            # Copy and convert technical data
            tech_data = api_stock_data.get("technical_data", {})
            if tech_data:
                for key, value in tech_data.items():
                    if key in ["price_above_sma200", "sma200_slope_positive", "sma50_above_sma200", "sma100_above_sma200"]:
                        stock_data["technical_data"][key] = bool(value)
                    elif value is not None:
                        stock_data["technical_data"][key] = float(value)
                    else:
                        stock_data["technical_data"][key] = None
            
            # Copy and convert fundamental data
            fund_data = api_stock_data.get("fundamental_data", {})
            if fund_data:
                for key, value in fund_data.items():
                    if key.endswith("_positive"):
                        stock_data["fundamental_data"][key] = bool(value)
                    elif value is not None:
                        stock_data["fundamental_data"][key] = float(value)
                    else:
                        stock_data["fundamental_data"][key] = None
            
            # Copy chart data - ensure it's always available
            if "chart_data" in api_stock_data and api_stock_data["chart_data"]:
                stock_data["chart_data"] = api_stock_data["chart_data"]
            else:
                # If no chart data available, create a fallback request right now
                logger.debug(f"Chart data missing for {symbol}, fetching directly")
                chart_data = screener._prepare_chart_data(symbol)
                stock_data["chart_data"] = chart_data
        
            # Save to database if successful
            try:
                # Find or create the stock
                db_stock = Stock.query.filter_by(symbol=symbol).first()
                if not db_stock:
                    db_stock = Stock(
                        symbol=symbol,
                        company_name=stock_data.get("company_name", symbol)
                    )
                    db.session.add(db_stock)
                    db.session.flush()
                else:
                    db_stock.company_name = stock_data.get("company_name", symbol)
                    db_stock.last_updated = datetime.utcnow()
                
                # Create or update technical/fundamental results
                # Convert any numpy values to Python native types
                result = ScreeningResult(
                    stock_id=db_stock.id,
                    current_price=stock_data["technical_data"].get("current_price"),
                    sma50=stock_data["technical_data"].get("sma50"),
                    sma100=stock_data["technical_data"].get("sma100"),
                    sma200=stock_data["technical_data"].get("sma200"),
                    sma200_slope=stock_data["technical_data"].get("sma200_slope"),
                    price_above_sma200=stock_data["technical_data"].get("price_above_sma200", False),
                    sma200_slope_positive=stock_data["technical_data"].get("sma200_slope_positive", False),
                    sma50_above_sma200=stock_data["technical_data"].get("sma50_above_sma200", False),
                    sma100_above_sma200=stock_data["technical_data"].get("sma100_above_sma200", False),
                    quarterly_sales_growth_positive=stock_data["fundamental_data"].get("quarterly_sales_growth_positive", False),
                    quarterly_eps_growth_positive=stock_data["fundamental_data"].get("quarterly_eps_growth_positive", False),
                    estimated_sales_growth_positive=stock_data["fundamental_data"].get("estimated_sales_growth_positive", False),
                    estimated_eps_growth_positive=stock_data["fundamental_data"].get("estimated_eps_growth_positive", False),
                    passes_all_criteria=stock_data.get("passes_all_criteria", False),
                    meets_all_criteria=stock_data.get("meets_all_criteria", False)
                )
                
                # Set chart data
                if "chart_data" in stock_data:
                    result.set_chart_data(stock_data["chart_data"])
                
                db.session.add(result)
                
                # Store fundamental data if we have any
                fund_data = api_stock_data.get("fundamental_data", {})
                if fund_data:
                    fundamental = StockFundamentals.query.filter_by(stock_id=db_stock.id).first()
                    if not fundamental:
                        fundamental = StockFundamentals(stock_id=db_stock.id)
                        db.session.add(fundamental)
                    
                    fundamental.quarterly_revenue_growth = stock_data["fundamental_data"].get("quarterly_sales_growth")
                    fundamental.quarterly_eps_growth = stock_data["fundamental_data"].get("quarterly_eps_growth")
                    fundamental.estimated_sales_growth = stock_data["fundamental_data"].get("estimated_sales_growth")
                    fundamental.estimated_eps_growth = stock_data["fundamental_data"].get("estimated_eps_growth")
                    fundamental.last_updated = datetime.utcnow()
                    
                    # Store the raw data for advanced metrics
                    raw_data = {
                        'general': {'name': db_stock.company_name},
                        'estimates': {'annual': {}}
                    }
                    
                    # Include all available growth metrics in the raw data - convert values to native types
                    annual_estimates = raw_data['estimates']['annual']
                    annual_estimates['eps_growth'] = stock_data["fundamental_data"].get("estimated_eps_growth", 0)
                    annual_estimates['revenue_growth'] = stock_data["fundamental_data"].get("estimated_sales_growth", 0)
                    
                    if 'current_quarter_growth' in stock_data["fundamental_data"]:
                        annual_estimates['current_quarter_growth'] = stock_data["fundamental_data"]["current_quarter_growth"]
                    if 'next_quarter_growth' in stock_data["fundamental_data"]:
                        annual_estimates['next_quarter_growth'] = stock_data["fundamental_data"]["next_quarter_growth"]
                    if 'current_year_growth' in stock_data["fundamental_data"]:
                        annual_estimates['current_year_growth'] = stock_data["fundamental_data"]["current_year_growth"]
                    if 'next_5_years_growth' in stock_data["fundamental_data"]:
                        annual_estimates['next_5_years_growth'] = stock_data["fundamental_data"]["next_5_years_growth"]
                        
                    # Save the raw data
                    fundamental.set_raw_data(raw_data)
                
                # Commit changes
                db.session.commit()
            except Exception as e:
                logger.error(f"Error saving stock data to database: {str(e)}")
                db.session.rollback()
                # Continue with returning the data even if database save fails
        
        # Use the custom encoder for this response
        return json.dumps({"success": True, "data": stock_data, "cached": False}, cls=CustomJSONEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
        db.session.rollback()
        return json.dumps({"success": False, "error": str(e)}, cls=CustomJSONEncoder), 500, {'Content-Type': 'application/json'}

@app.route('/api/stats')
def get_database_stats():
    """Get statistics about the database"""
    try:
        stock_count = Stock.query.count()
        screening_count = ScreeningResult.query.count()
        
        # Get last screening session info
        last_session = ScreeningSession.query.order_by(ScreeningSession.timestamp.desc()).first()
        last_screening_time = None
        last_execution_time = None
        if last_session:
            last_screening_time = last_session.timestamp.isoformat()
            last_execution_time = last_session.execution_time
        
        # Get counts for stocks passing different criteria in the last screening
        passing_stocks = 0
        strict_passing_stocks = 0
        
        if last_session:
            # Count stocks that passed with relaxed criteria
            passing_stocks = ScreeningResult.query.filter(
                ScreeningResult.passes_all_criteria == True,
                ScreeningResult.screening_date >= last_session.timestamp
            ).count()
            
            # Count stocks that passed with strict criteria (all criteria must be met)
            strict_passing_stocks = ScreeningResult.query.filter(
                ScreeningResult.meets_all_criteria == True,
                ScreeningResult.screening_date >= last_session.timestamp
            ).count()
        
        stats_data = {
            "success": True,
            "stats": {
                "stock_count": stock_count,
                "screening_result_count": screening_count,
                "last_screening_time": last_screening_time,
                "last_execution_time": last_execution_time,
                "passing_stocks": passing_stocks,
                "strict_passing_stocks": strict_passing_stocks
            }
        }
        return json.dumps(stats_data, cls=CustomJSONEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return json.dumps({"success": False, "error": str(e)}, cls=CustomJSONEncoder), 500, {'Content-Type': 'application/json'}

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear database cache"""
    try:
        # Delete all screening results
        if request.args.get('all', 'false').lower() == 'true':
            ScreeningResult.query.delete()
            db.session.commit()
            logger.debug("Cleared all screening results")
            return json.dumps({"success": True, "message": "Cleared all screening results"}, cls=CustomJSONEncoder), 200, {'Content-Type': 'application/json'}
        
        # Only delete older than a certain time
        days = int(request.args.get('days', 7))
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        count = ScreeningResult.query.filter(ScreeningResult.screening_date < cutoff_date).delete()
        db.session.commit()
        
        logger.debug(f"Cleared {count} screening results older than {days} days")
        return json.dumps({
            "success": True,
            "message": f"Cleared {count} screening results older than {days} days"
        }, cls=CustomJSONEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        db.session.rollback()
        return json.dumps({"success": False, "error": str(e)}, cls=CustomJSONEncoder), 500, {'Content-Type': 'application/json'}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
