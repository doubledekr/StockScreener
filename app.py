import os
import logging
from flask import Flask, render_template, jsonify
from stock_screener import StockScreener

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Initialize stock screener
screener = StockScreener(api_key=os.environ.get("TWELVEDATA_API_KEY", ""))

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/screen')
def screen_stocks():
    """Run the stock screening process and return results"""
    try:
        logger.debug("Starting stock screening process")
        # Get top stocks based on criteria
        top_stocks = screener.get_top_stocks()
        return jsonify({"success": True, "stocks": top_stocks})
    except Exception as e:
        logger.error(f"Error in stock screening: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/stock/<symbol>')
def get_stock_data(symbol):
    """Get detailed data for a specific stock"""
    try:
        logger.debug(f"Fetching data for stock: {symbol}")
        stock_data = screener.get_stock_details(symbol)
        return jsonify({"success": True, "data": stock_data})
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
