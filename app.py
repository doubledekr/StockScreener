import os
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from stock_screener import StockScreener
from models import db, Stock, PriceHistory, StockFundamentals, ScreeningResult, ScreeningSession
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
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
        if 'values' in data and data['values']:
            for item in data['values']:
                market_movers.append({
                    'symbol': item.get('symbol', ''),
                    'name': item.get('name', ''),
                    'last_price': item.get('last', 0),
                    'change': item.get('change', 0),
                    'percent_change': item.get('percent_change', 0)
                })
                
        # Cache the results
        app.cached_market_movers = market_movers
        app.market_movers_timestamp = datetime.utcnow()
        
        return jsonify({"success": True, "market_movers": market_movers})
    except Exception as e:
        logger.error(f"Error fetching market movers: {str(e)}")
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
            cache_date = datetime.utcnow() - timedelta(hours=cache_hours)
            recent_results = ScreeningResult.query.filter(
                ScreeningResult.passes_all_criteria == True,
                ScreeningResult.screening_date >= cache_date
            ).join(Stock).order_by(ScreeningResult.score.desc()).limit(10).all()
            
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
        
        # Get top stocks based on criteria from the API
        logger.debug("No cached results or cache bypass requested, fetching from API")
        top_stocks = screener.get_top_stocks()
        
        # Record screening metrics
        end_time = time.time()
        execution_time = end_time - start_time
        
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
                passes_all_criteria=True
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
        
        return jsonify({"success": True, "stocks": top_stocks, "cached": False})
    except Exception as e:
        logger.error(f"Error in stock screening: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

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
                    stock_data = {
                        "symbol": symbol,
                        "company_name": stock.company_name,
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
                            "quarterly_sales_growth_positive": result.quarterly_sales_growth_positive,
                            "quarterly_eps_growth_positive": result.quarterly_eps_growth_positive,
                            "estimated_sales_growth_positive": result.estimated_sales_growth_positive,
                            "estimated_eps_growth_positive": result.estimated_eps_growth_positive
                        },
                        "chart_data": result.get_chart_data(),
                        "passes_all_criteria": result.passes_all_criteria
                    }
                    
                    # Add fundamental metrics if available
                    fundamental = StockFundamentals.query.filter_by(stock_id=stock.id).first()
                    if fundamental:
                        stock_data["fundamental_data"].update({
                            "quarterly_sales_growth": fundamental.quarterly_revenue_growth,
                            "quarterly_eps_growth": fundamental.quarterly_eps_growth,
                            "estimated_sales_growth": fundamental.estimated_sales_growth,
                            "estimated_eps_growth": fundamental.estimated_eps_growth,
                            "company_name": stock.company_name
                        })
                        
                        # Add additional growth metrics from raw data if available
                        raw_data = fundamental.get_raw_data()
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
                    
                    return jsonify({"success": True, "data": stock_data, "cached": True})
        
        # If no cache or cache miss, fetch from API
        logger.debug(f"Fetching fresh data for {symbol} from API")
        stock_data = screener.get_stock_details(symbol)
        
        # Save to database if successful
        if stock_data:
            # Find or create the stock
            stock = Stock.query.filter_by(symbol=symbol).first()
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
            
            # Create or update technical/fundamental results
            tech_data = stock_data.get("technical_data", {})
            fund_data = stock_data.get("fundamental_data", {})
            
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
                passes_all_criteria=stock_data.get("passes_all_criteria", False)
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
            
            # Commit changes
            db.session.commit()
        
        return jsonify({"success": True, "data": stock_data, "cached": False})
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

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
        
        # Get count of stocks that passed all criteria in the last screening
        if last_session:
            passing_stocks = ScreeningResult.query.filter(
                ScreeningResult.passes_all_criteria == True,
                ScreeningResult.screening_date >= last_session.timestamp
            ).count()
        else:
            passing_stocks = 0
        
        return jsonify({
            "success": True,
            "stats": {
                "stock_count": stock_count,
                "screening_result_count": screening_count,
                "last_screening_time": last_screening_time,
                "last_execution_time": last_execution_time,
                "passing_stocks": passing_stocks
            }
        })
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear database cache"""
    try:
        # Delete all screening results
        if request.args.get('all', 'false').lower() == 'true':
            ScreeningResult.query.delete()
            db.session.commit()
            logger.debug("Cleared all screening results")
            return jsonify({"success": True, "message": "Cleared all screening results"})
        
        # Only delete older than a certain time
        days = int(request.args.get('days', 7))
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        count = ScreeningResult.query.filter(ScreeningResult.screening_date < cutoff_date).delete()
        db.session.commit()
        
        logger.debug(f"Cleared {count} screening results older than {days} days")
        return jsonify({
            "success": True,
            "message": f"Cleared {count} screening results older than {days} days"
        })
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
