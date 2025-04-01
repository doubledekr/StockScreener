from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import numpy as np

db = SQLAlchemy()

# Custom JSON encoder for handling non-serializable types
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
        # Handle native Python bool (for redundancy)
        elif isinstance(obj, bool):
            return bool(obj)
        # Let the base class handle other types or raise TypeError
        return super(CustomJSONEncoder, self).default(obj)

class Stock(db.Model):
    """Model for storing basic stock information"""
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    company_name = db.Column(db.String(200))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # One-to-many relationships
    price_history = db.relationship('PriceHistory', backref='stock', lazy=True, cascade='all, delete-orphan')
    fundamentals = db.relationship('StockFundamentals', backref='stock', lazy=True, cascade='all, delete-orphan')
    screening_results = db.relationship('ScreeningResult', backref='stock', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Stock {self.symbol}>'

class PriceHistory(db.Model):
    """Model for storing historical price data"""
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open = db.Column(db.Float)
    high = db.Column(db.Float)
    low = db.Column(db.Float)
    close = db.Column(db.Float)
    volume = db.Column(db.BigInteger)
    
    __table_args__ = (db.UniqueConstraint('stock_id', 'date', name='_stock_date_uc'),)
    
    def __repr__(self):
        return f'<PriceHistory {self.stock.symbol} {self.date}>'

class StockFundamentals(db.Model):
    """Model for storing fundamental data"""
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Quarterly metrics
    quarterly_revenue = db.Column(db.Float)
    quarterly_revenue_growth = db.Column(db.Float)
    quarterly_eps = db.Column(db.Float)
    quarterly_eps_growth = db.Column(db.Float)
    
    # Annual estimates
    estimated_sales_growth = db.Column(db.Float)
    estimated_eps_growth = db.Column(db.Float)
    
    # Raw JSON data for flexibility
    raw_data = db.Column(db.Text)
    
    def get_raw_data(self):
        """Convert the stored JSON string back to a dict"""
        if self.raw_data:
            return json.loads(self.raw_data)
        return {}
    
    def set_raw_data(self, data_dict):
        """Store the raw fundamental data as a JSON string"""
        if data_dict:
            self.raw_data = json.dumps(data_dict, cls=CustomJSONEncoder)
    
    def __repr__(self):
        return f'<StockFundamentals {self.stock.symbol}>'

class ScreeningResult(db.Model):
    """Model for storing stock screening results"""
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    screening_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Technical criteria
    price_above_sma200 = db.Column(db.Boolean, default=False)
    sma200_slope_positive = db.Column(db.Boolean, default=False)
    sma50_above_sma200 = db.Column(db.Boolean, default=False)
    sma100_above_sma200 = db.Column(db.Boolean, default=False)
    
    # Fundamental criteria
    quarterly_sales_growth_positive = db.Column(db.Boolean, default=False)
    quarterly_eps_growth_positive = db.Column(db.Boolean, default=False)
    estimated_sales_growth_positive = db.Column(db.Boolean, default=False)
    estimated_eps_growth_positive = db.Column(db.Boolean, default=False)
    
    # Additional metrics
    current_price = db.Column(db.Float)
    sma50 = db.Column(db.Float)
    sma100 = db.Column(db.Float)
    sma200 = db.Column(db.Float)
    sma200_slope = db.Column(db.Float)
    score = db.Column(db.Float)  # Composite score for ranking
    
    # Results flags
    passes_all_criteria = db.Column(db.Boolean, default=False)  # Relaxed approach (backward compatible)
    meets_all_criteria = db.Column(db.Boolean, default=False)   # Strict approach (all criteria must be met)
    
    # Chart data stored as JSON
    chart_data = db.Column(db.Text)
    
    def get_chart_data(self):
        """Convert the stored JSON string back to a dict"""
        if self.chart_data:
            return json.loads(self.chart_data)
        return None
    
    def set_chart_data(self, data_dict):
        """Store the chart data as a JSON string"""
        if data_dict:
            self.chart_data = json.dumps(data_dict, cls=CustomJSONEncoder)
    
    def __repr__(self):
        return f'<ScreeningResult {self.stock.symbol} {self.screening_date}>'

class ScreeningSession(db.Model):
    """Model for tracking screening sessions"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    symbol_count = db.Column(db.Integer)
    qualified_count = db.Column(db.Integer)
    execution_time = db.Column(db.Float)  # Time in seconds
    
    def __repr__(self):
        return f'<ScreeningSession {self.timestamp}>'