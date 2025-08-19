import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Class for analyzing Albion Online market data."""
    
    def __init__(self, window: int = 3):
        """
        Initialize the MarketAnalyzer.
        
        Args:
            window: Moving average window size for smoothing price data
        """
        self.window = window
    
    def calculate_price_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate basic price statistics.
        
        Args:
            df: DataFrame containing price data
            
        Returns:
            Dictionary containing price statistics
        """
        if df.empty:
            return {}
            
        stats = {
            'current_price': df['price'].iloc[-1] if 'price' in df.columns else None,
            'min_price': df['price'].min() if 'price' in df.columns else None,
            'max_price': df['price'].max() if 'price' in df.columns else None,
            'avg_price': df['price'].mean() if 'price' in df.columns else None,
            'price_std': df['price'].std() if 'price' in df.columns else None,
            'price_change_24h': self._calculate_price_change(df, hours=24) if 'price' in df.columns else None,
            'price_change_7d': self._calculate_price_change(df, hours=168) if 'price' in df.columns else None,
            'volume_24h': self._calculate_volume(df, hours=24) if 'item_count' in df.columns else None,
            'volume_7d': self._calculate_volume(df, hours=168) if 'item_count' in df.columns else None
        }
        
        return stats
    
    def _calculate_price_change(self, df: pd.DataFrame, hours: int) -> Optional[float]:
        """Calculate price change over a specified number of hours."""
        if 'timestamp' not in df.columns or 'price' not in df.columns:
            return None
            
        df = df.sort_values('timestamp')
        if len(df) < 2:
            return None
            
        # Get the most recent price
        current_price = df['price'].iloc[-1]
        
        # Find the price 'hours' hours ago
        cutoff = df['timestamp'].iloc[-1] - pd.Timedelta(hours=hours)
        past_prices = df[df['timestamp'] <= cutoff]
        
        if past_prices.empty:
            return None
            
        past_price = past_prices['price'].iloc[-1]
        
        if past_price == 0:
            return None
            
        return ((current_price - past_price) / past_price) * 100
    
    def _calculate_volume(self, df: pd.DataFrame, hours: int) -> Optional[int]:
        """Calculate trading volume over a specified number of hours."""
        if 'timestamp' not in df.columns or 'item_count' not in df.columns:
            return None
            
        df = df.sort_values('timestamp')
        if df.empty:
            return 0
            
        # Filter data for the specified time period
        cutoff = df['timestamp'].iloc[-1] - pd.Timedelta(hours=hours)
        recent_df = df[df['timestamp'] >= cutoff]
        
        return int(recent_df['item_count'].sum())
    
    def calculate_price_trend(self, df: pd.DataFrame) -> str:
        """
        Determine the price trend based on recent price movements.
        
        Args:
            df: DataFrame containing price data
            
        Returns:
            String indicating the trend ('up', 'down', or 'stable')
        """
        if df.empty or 'price' not in df.columns or 'timestamp' not in df.columns:
            return 'unknown'
            
        df = df.sort_values('timestamp')
        if len(df) < 2:
            return 'stable'
            
        # Calculate short-term and long-term trends
        short_term = self._calculate_price_change(df, hours=24) or 0
        long_term = self._calculate_price_change(df, hours=168) or 0
        
        # Determine trend based on both timeframes
        if short_term > 2 and long_term > 1:
            return 'strong_up'
        elif short_term > 1 or (short_term > 0 and long_term > 0):
            return 'up'
        elif short_term < -2 and long_term < -1:
            return 'strong_down'
        elif short_term < -1 or (short_term < 0 and long_term < 0):
            return 'down'
        else:
            return 'stable'
    
    def get_best_sell_location(self, item_id: str, cities: List[str]) -> Optional[Dict]:
        """
        Find the best city to sell an item based on current prices.
        
        Args:
            item_id: The ID of the item to analyze
            cities: List of cities to compare
            
        Returns:
            Dictionary with the best city to sell in and its price,
            or None if data is not available
        """
        best_city = None
        best_price = 0
        
        for city in cities:
            try:
                # In a real implementation, you would fetch current prices
                # This is a placeholder for demonstration
                price = 100  # This would be fetched from the API
                if price > best_price:
                    best_price = price
                    best_city = city
            except Exception as e:
                logger.error(f"Error getting price for {item_id} in {city}: {e}")
                continue
        
        if best_city:
            return {'city': best_city, 'price': best_price}
        return None
    
    def detect_arbitrage_opportunities(self, item_id: str) -> List[Dict]:
        """
        Detect potential arbitrage opportunities for an item across cities.
        
        Args:
            item_id: The ID of the item to analyze
            
        Returns:
            List of potential arbitrage opportunities
        """
        # In a real implementation, this would compare prices across cities
        # This is a placeholder for demonstration
        return []

# Example usage
if __name__ == "__main__":
    # Example DataFrame with dummy data
    dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='D')
    prices = [100 + i*2 + np.random.normal(0, 5) for i in range(30)]
    volumes = [int(1000 + i*10 + np.random.normal(0, 50)) for i in range(30)]
    
    df = pd.DataFrame({
        'timestamp': dates,
        'price': prices,
        'item_count': volumes
    })
    
    analyzer = MarketAnalyzer()
    stats = analyzer.calculate_price_statistics(df)
    trend = analyzer.calculate_price_trend(df)
    
    print("Price Statistics:", stats)
    print("Price Trend:", trend)
