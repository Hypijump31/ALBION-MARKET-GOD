import requests
import pandas as pd
import json
import time
import logging
from typing import List, Dict, Optional
from functools import wraps
import streamlit as st
from datetime import datetime, timedelta
from performance_optimizer import PerformanceOptimizer
from api_monitor import api_monitor
from functools import wraps

logger = logging.getLogger(__name__)

# Performance optimizer instance
performance_optimizer = PerformanceOptimizer()

# Decorator for caching
def cached(ttl: int = 300):
    """Simple caching decorator with time-to-live."""
    def decorator(func):
        return performance_optimizer.memory_efficient_cache(ttl)(func)
    return decorator

class AlbionMarketData:
    """Class to handle data collection from Albion Online API."""
    
    # Regional API endpoints
    BASE_URLS = {
        'Europe': 'https://europe.albion-online-data.com/api/v2/stats',
        'Americas': 'https://west.albion-online-data.com/api/v2/stats',
        'Asia': 'https://east.albion-online-data.com/api/v2/stats'
    }
    
    # Major cities in Albion Online
    CITIES = {
        'Thetford': 'Thetford',
        'Fort Sterling': 'Fort Sterling',
        'Lymhurst': 'Lymhurst',
        'Bridgewatch': 'Bridgewatch',
        'Martlock': 'Martlock',
        'Caerleon': 'Caerleon',
        'Brecilien': 'Brecilien'
    }
    
    # Popular items for quick selection
    POPULAR_ITEMS = [
        'T4_ORE', 'T5_ORE', 'T6_ORE', 'T7_ORE', 'T8_ORE',
        'T4_WOOD', 'T5_WOOD', 'T6_WOOD', 'T7_WOOD', 'T8_WOOD',
        'T4_LEATHER', 'T5_LEATHER', 'T6_LEATHER', 'T7_LEATHER', 'T8_LEATHER',
        'T4_CLOTH', 'T5_CLOTH', 'T6_CLOTH', 'T7_CLOTH', 'T8_CLOTH'
    ]
    
    def __init__(self, region: str = 'Europe'):
        """
        Initialize the AlbionMarketData class.
        
        Args:
            region: API region to use ('Europe', 'Americas', or 'Asia')
        """
        if region not in self.BASE_URLS:
            raise ValueError(f"Invalid region. Available regions: {', '.join(self.BASE_URLS.keys())}")
        
        self.region = region
        self.base_url = self.BASE_URLS[region]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AlbionMarketAnalyzer/1.0',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self._last_request_time = 0
        self._request_count = 0
        self._minute_start = time.time()
    
    def get_available_cities(self) -> List[str]:
        """Return list of available cities for market data."""
        return list(self.CITIES.keys())
    
    def get_popular_items(self) -> List[str]:
        """Return list of popular items for quick selection."""
        return self.POPULAR_ITEMS
    
    def _rate_limit(self):
        """Ensure we don't exceed API rate limits (180 per minute)."""
        current_time = time.time()
        
        # Reset counter if minute has passed
        if current_time - self._minute_start >= 60:
            self._minute_start = current_time
            self._request_count = 0
        
        # If we're at the limit, wait
        if self._request_count >= 180:
            wait_time = 60 - (current_time - self._minute_start)
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
                self._minute_start = time.time()
                self._request_count = 0
        
        # Small delay between requests
        if current_time - self._last_request_time < 0.5:
            time.sleep(0.5)
        
        self._last_request_time = time.time()
        self._request_count += 1
    

    @cached(ttl=300)  # Cache for 5 minutes
    def get_refining_prices(self, tier: str, resource_type: str, enchantment: int = 0, locations: List[str] = None, confirm_request: bool = False) -> Dict:
        """
        Get current prices for raw and refined resources for refining calculations.
        
        Args:
            tier: Target refined tier (T4, T5, etc.) 
            resource_type: Type (ORE, WOOD, HIDE, FIBER, ROCK)
            enchantment: Enchantment level (0-3)
            locations: List of city names (optional)
            
        Returns:
            Dictionary with raw, prev_refined and refined prices by city
        """
        from .item_mapping import get_raw_item_id, get_refined_item_id
        
        # Vraie recette Albion: 2x T4 raw + 1x T3 refined = 1x T4 refined
        raw_item = get_raw_item_id(tier, resource_type, enchantment)
        refined_item = get_refined_item_id(tier, resource_type, enchantment)
        
        # Calculer le tier précédent pour le matériau raffiné requis
        tier_num = int(tier[1:])
        prev_tier = f"T{tier_num - 1}" if tier_num > 1 else tier
        # The previous tier refined material has the same enchantment level
        prev_refined_item = get_refined_item_id(prev_tier, resource_type, enchantment)
        
        # Get prices for all items needed for refining, including a fallback for prev_refined
        items_to_fetch = [raw_item, prev_refined_item, refined_item]

        # Add non-enchanted fallback for prev_refined if an enchantment is selected
        if enchantment > 0:
            prev_refined_item_normal = get_refined_item_id(prev_tier, resource_type, 0)
            if prev_refined_item_normal not in items_to_fetch:
                items_to_fetch.append(prev_refined_item_normal)
        
        
        params = {}
        if locations:
            params['locations'] = ','.join(locations)
        
        # Build URL for multiple items - FORMAT CORRECT selon documentation officielle
        items_str = ','.join(items_to_fetch)
        url = f"{self.base_url}/prices/{items_str}"
        
        # Paramètres optionnels pour l'API Albion Online v2
        params = {}
        if locations:
            params['locations'] = ','.join(locations)
        
        # Start API monitoring
        request_id = api_monitor.start_request("GET", url, params)
        
        # Execute API request directly
        
        # Update status to executing
        api_monitor.update_status(request_id, "EXECUTING")
        
        self._rate_limit()
        
        try:
            logger.info(f"Making API request to: {url}")
            logger.info(f"Items to fetch: {items_to_fetch}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"API response received: {len(data) if data else 0} items")
            
            if not data:
                logger.warning(f"No price data found for {tier} {resource_type}")
                return {}
            
            # Update monitor with success
            duration = 1.0  # Simplified duration calculation
            api_monitor.update_status(request_id, "SUCCESS", duration, len(data))
            
            # Data retrieved successfully
            # Log des IDs d'articles récupérés et de la réponse brute de l'API
            retrieved_ids = {item['item_id'] for item in data}
            logger.info(f"[DEBUG] Items fetched successfully: {retrieved_ids}")
            logger.info(f"[DEBUG] Full API response data: {data}")
            
            # Transform data to expected format
            formatted_data = self._format_price_data(data, items_to_fetch, tier, resource_type, enchantment)
            
            # Data formatted successfully
            logger.info(f"Cities with data: {list(formatted_data.keys())}")
            
            return formatted_data
            
        except requests.exceptions.RequestException as e:
            # Update monitor with error
            api_monitor.update_status(request_id, "ERROR", 0, 0, str(e))
            logger.error(f"API request failed: {e}")
            return {}
    
    def _format_price_data(self, data: List[Dict], items_to_fetch: List[str], tier: str, resource_type: str, enchantment: int) -> Dict:
        """
        Format API data into expected structure for arbitrage analysis
        Handles multiple quality levels per item/city
        
        Args:
            data: Raw data from API
            items_to_fetch: List of item IDs that were requested
            tier: Target refined tier (T4, T5, etc.) 
            resource_type: Type (ORE, WOOD, HIDE, FIBER, ROCK)
            enchantment: Enchantment level (0-3)
            
        Returns:
            Dict with formatted price data by city
        """
        from .item_mapping import get_refined_item_id
        result = {}
        
        if not data:
            return result
            
        # Identify which items we have (raw, prev_refined, refined)
        raw_item = items_to_fetch[0] if len(items_to_fetch) > 0 else None
        prev_refined_item = items_to_fetch[1] if len(items_to_fetch) > 1 else None
        refined_item = items_to_fetch[2] if len(items_to_fetch) > 2 else None
        
        # Group data by city and item_id to handle multiple qualities
        grouped_prices = {}
        for item in data:
            city = item.get('city')
            item_id = item.get('item_id')
            if not city or not item_id:
                continue

            key = (city, item_id)
            if key not in grouped_prices:
                grouped_prices[key] = []
            grouped_prices[key].append(item)

        # Find the best price for each item in each city
        best_prices = {}
        for key, items in grouped_prices.items():
            city, item_id = key
            # For sell price, we want the minimum; for buy price, the maximum.
            # Filter out entries where prices are 0.
            valid_sell_prices = [i['sell_price_min'] for i in items if i['sell_price_min'] > 0]
            valid_buy_prices = [i['buy_price_max'] for i in items if i['buy_price_max'] > 0]

            best_prices[key] = {
                'sell_price_min': min(valid_sell_prices) if valid_sell_prices else 0,
                'buy_price_max': max(valid_buy_prices) if valid_buy_prices else 0,
            }

        # Build the final result dictionary
        all_cities = {item.get('city') for item in data if item.get('city')}
        for city in all_cities:
            result[city] = {}
            raw_price_info = best_prices.get((city, raw_item), {})
            prev_refined_price_info = best_prices.get((city, prev_refined_item), {})
            refined_price_info = best_prices.get((city, refined_item), {})

            # Raw material prices
            if raw_price_info.get('sell_price_min', 0) > 0:
                result[city]['raw'] = {
                    'sell_min': raw_price_info['sell_price_min'],
                    'buy_max': raw_price_info.get('buy_price_max', 0), # buy_max is less critical
                    'item_id': raw_item
                }

            # Previous tier refined material prices (with fallback)
            if prev_refined_price_info.get('sell_price_min', 0) > 0:
                result[city]['prev_refined'] = {
                    'sell_min': prev_refined_price_info['sell_price_min'],
                    'buy_max': prev_refined_price_info.get('buy_price_max', 0),
                    'item_id': prev_refined_item
                }
            elif enchantment > 0: # Fallback for enchanted items
                tier_num = int(tier[1:])
                prev_tier = f"T{tier_num - 1}" if tier_num > 1 else tier
                prev_refined_item_normal = get_refined_item_id(prev_tier, resource_type, 0)
                fallback_price_info = best_prices.get((city, prev_refined_item_normal), {})
                if fallback_price_info.get('sell_price_min', 0) > 0:
                    logger.info(f"[FALLBACK] Using price of {prev_refined_item_normal} for {prev_refined_item} in {city}")
                    result[city]['prev_refined'] = {
                        'sell_min': fallback_price_info['sell_price_min'],
                        'buy_max': fallback_price_info.get('buy_price_max', 0),
                        'item_id': prev_refined_item_normal
                    }

            # Final refined product prices
            if refined_price_info.get('buy_price_max', 0) > 0:
                result[city]['refined'] = {
                    'buy_max': refined_price_info['buy_price_max'],
                    'sell_min': refined_price_info.get('sell_price_min', 0), # sell_min is less critical here
                    'item_id': refined_item
                }
        
        # Price data formatted successfully
        
        return result
    
    @cached(ttl=180)  # Cache for 3 minutes (shorter for current prices)
    def get_current_prices(self, item_ids: List[str], locations: List[str] = None, qualities: List[int] = None, confirm_request: bool = False) -> pd.DataFrame:
        """
        Fetch current market prices for items.
        
        Args:
            item_ids: List of item IDs to fetch prices for
            locations: List of city names (optional)
            qualities: List of item qualities (optional)
            
        Returns:
            DataFrame containing current market prices
        """
        # Build URL
        items_str = ','.join(item_ids)
        url = f"{self.base_url}/prices/{items_str}.json"
        
        params = {}
        if locations:
            params['locations'] = ','.join(locations)
        if qualities:
            params['qualities'] = ','.join(map(str, qualities))
        
        # Execute request directly
        
        self._rate_limit()
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                logger.warning(f"No current price data found for {item_ids}")
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            df = performance_optimizer.optimize_dataframe(df)
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching current prices: {e}")
            return pd.DataFrame()
    
    def get_market_data(self, item_id: str, location: str, days: int = 7, confirm_request: bool = False) -> pd.DataFrame:
        """
        Fetch historical market data for a specific item and location.
        
        Args:
            item_id: The ID of the item to fetch data for
            location: The city to get data from
            days: Number of days of history to fetch
            
        Returns:
            DataFrame containing the market data
        """
        if location not in self.CITIES:
            raise ValueError(f"Invalid location. Available locations: {', '.join(self.CITIES)}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'date': start_date.strftime('%m-%d-%Y'),
            'end_date': end_date.strftime('%m-%d-%Y'),
            'locations': self.CITIES[location],
            'time-scale': '24'  # Daily data
        }
        
        url = f"{self.base_url}/history/{item_id}.json"
        
        # Execute request directly
        
        self._rate_limit()
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                logger.warning(f"No data found for {item_id} in {location}")
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Convert timestamps to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
            
            # Rename columns to match our expected format
            if 'avg_price' in df.columns:
                df = df.rename(columns={'avg_price': 'price'})
            
            # Optimize DataFrame for memory efficiency
            df = performance_optimizer.optimize_dataframe(df)
            
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching market data: {e}")
            return pd.DataFrame()
    
    def search_item(self, query: str) -> List[Dict]:
        """
        Search for items by name.
        
        Args:
            query: Search term
            
        Returns:
            List of matching items with their IDs and names
        """
        # This is a simplified implementation
        # In a real application, you would query Albion's item database
        return [{'id': item, 'name': item} for item in self.POPULAR_ITEMS 
                if query.lower() in item.lower()]

    def get_gold_prices(self, days: int = 7, confirm_request: bool = False) -> pd.DataFrame:
        """
        Fetch gold prices over time.
        
        Args:
            days: Number of days of history to fetch
            
        Returns:
            DataFrame containing gold price data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'date': start_date.strftime('%m-%d-%Y'),
            'end_date': end_date.strftime('%m-%d-%Y')
        }
        
        url = f"{self.base_url}/gold.json"
        
        # Execute request directly
        
        self._rate_limit()
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                logger.warning("No gold price data found")
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            
            # Convert timestamps to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
            
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching gold prices: {e}")
            return pd.DataFrame()

# Example usage
if __name__ == "__main__":
    market = AlbionMarketData(region='Europe')
    print("Available cities:", market.get_available_cities())
    print("\nPopular items:", market.get_popular_items())
    
    # Example: Get current prices for T4 bags in major cities
    current_prices = market.get_current_prices(['T4_BAG'], ['Caerleon', 'Bridgewatch'])
    if not current_prices.empty:
        print("\nCurrent prices:")
        print(current_prices.head())
    
    # Example: Get historical data for T4 ore in Thetford
    historical_data = market.get_market_data('T4_ORE', 'Thetford', 7)
    if not historical_data.empty:
        print("\nHistorical data:")
        print(historical_data.head())
