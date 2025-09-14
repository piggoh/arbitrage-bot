"""
Logging utility for the arbitrage bot
"""
import logging
import json
from datetime import datetime
import os
import pandas as pd

class ArbitrageLogger:
    def __init__(self, log_dir="logs"):
        # Create logs directory if it doesn't exist
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up price logging
        self.price_data = []
        self.trades_data = []
        
        # Set up file handlers
        self.setup_loggers()
    
    def setup_loggers(self):
        # Main logger
        self.logger = logging.getLogger('arbitrage_bot')
        self.logger.setLevel(logging.INFO)
        
        # Create handlers
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fh = logging.FileHandler(f'{self.log_dir}/bot_{timestamp}.log')
        fh.setLevel(logging.INFO)
        
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(fh)
    
    def log_prices(self, token_pair: tuple, uni_price: float, sushi_price: float):
        """Log price data for analysis"""
        timestamp = datetime.now().isoformat()
        price_entry = {
            'timestamp': timestamp,
            'token_pair': f"{token_pair[0]}/{token_pair[1]}",
            'uniswap_price': uni_price,
            'sushiswap_price': sushi_price,
            'price_difference': abs(uni_price - sushi_price),
            'price_difference_percent': abs(uni_price - sushi_price) / min(uni_price, sushi_price) * 100
        }
        self.price_data.append(price_entry)
        
        # Save to CSV every 100 entries
        if len(self.price_data) >= 100:
            self.save_price_data()
    
    def log_trade(self, trade_data: dict):
        """Log executed trade data"""
        timestamp = datetime.now().isoformat()
        trade_data['timestamp'] = timestamp
        self.trades_data.append(trade_data)
        self.save_trade_data()
    
    def save_price_data(self):
        """Save price data to CSV"""
        df = pd.DataFrame(self.price_data)
        filename = f'{self.log_dir}/price_data_{datetime.now().strftime("%Y%m%d")}.csv'
        df.to_csv(filename, mode='a', header=not os.path.exists(filename), index=False)
        self.price_data = []  # Clear after saving
    
    def save_trade_data(self):
        """Save trade data to CSV"""
        df = pd.DataFrame(self.trades_data)
        filename = f'{self.log_dir}/trade_data_{datetime.now().strftime("%Y%m%d")}.csv'
        df.to_csv(filename, mode='a', header=not os.path.exists(filename), index=False)
        self.trades_data = []  # Clear after saving
    
    def log_info(self, message: str):
        """Log informational message"""
        self.logger.info(message)
    
    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)