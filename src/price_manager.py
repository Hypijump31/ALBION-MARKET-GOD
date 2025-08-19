"""
Price Manager for Albion Online Market Data
Handles API price fetching with caching and fallbacks
"""

import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Tuple
from src.data_collector import AlbionMarketData
from src.item_mapping import get_raw_item_id, get_refined_item_id, get_display_name
import logging

logger = logging.getLogger(__name__)

class PriceManager:
    """Manages price fetching and caching for the application."""
    
    def __init__(self, market_data: AlbionMarketData):
        self.market_data = market_data
    
    def get_refining_prices_cached(self, tier: str, resource_type: str, enchantment: int = 0, cities: List[str] = None, confirm_request: bool = False) -> Dict:
        """Cached version of get_refining_prices to avoid repeated API calls."""
        return self.market_data.get_refining_prices(tier, resource_type, enchantment, cities, confirm_request)
    
    def get_best_prices_for_refining(self, tier: str, resource_type: str, cities: List[str]) -> Dict:
        """
        Get the best buy/sell prices across all cities for refining analysis.
        
        Returns:
            Dict with best prices for raw and refined materials
        """
        try:
            all_prices = self.get_refining_prices_cached(tier, resource_type, 0, cities)
            
            if not all_prices:
                return {}
            
            best_prices = {
                'raw': {
                    'buy_min': float('inf'),
                    'buy_max': 0,
                    'sell_min': float('inf'),
                    'sell_max': 0,
                    'best_buy_city': None,
                    'best_sell_city': None
                },
                'refined': {
                    'buy_min': float('inf'),
                    'buy_max': 0,
                    'sell_min': float('inf'),
                    'sell_max': 0,
                    'best_buy_city': None,
                    'best_sell_city': None
                }
            }
            
            for city, city_data in all_prices.items():
                # Process raw material prices
                if 'raw' in city_data:
                    raw_data = city_data['raw']
                    if raw_data['buy_price_min'] > 0 and raw_data['buy_price_min'] < best_prices['raw']['buy_min']:
                        best_prices['raw']['buy_min'] = raw_data['buy_price_min']
                        best_prices['raw']['best_buy_city'] = city
                    
                    if raw_data['sell_price_min'] > 0 and raw_data['sell_price_min'] < best_prices['raw']['sell_min']:
                        best_prices['raw']['sell_min'] = raw_data['sell_price_min']
                        best_prices['raw']['best_sell_city'] = city
                
                # Process refined material prices  
                if 'refined' in city_data:
                    refined_data = city_data['refined']
                    if refined_data['sell_price_min'] > 0 and refined_data['sell_price_min'] > best_prices['refined']['sell_max']:
                        best_prices['refined']['sell_max'] = refined_data['sell_price_min']
                        best_prices['refined']['best_sell_city'] = city
            
            return best_prices
            
        except Exception as e:
            logger.error(f"Error getting best prices: {e}")
            return {}
    
    def display_price_status(self, tier: str, resource_type: str, city: str, enchantment: int = 0, confirm_request: bool = False) -> Tuple[float, float]:
        """
        Display current price status in sidebar and return prices.
        
        Returns:
            Tuple of (raw_price, refined_price)
        """
        cities = ['Thetford', 'Fort Sterling', 'Lymhurst', 'Bridgewatch', 'Martlock', 'Caerleon', 'Brecilien']
        
        # Fetch prices
        market_prices = self.get_refining_prices_cached(tier, resource_type, enchantment, cities, confirm_request)
        
        # Default fallback prices
        raw_price = 100
        refined_price = 350
        
        st.sidebar.subheader("💰 Prix du Marché (API)")
        
        if market_prices and city in market_prices:
            city_data = market_prices[city]
            
            # Raw material price
            if 'raw' in city_data and city_data['raw']['sell_min'] > 0:
                raw_price = city_data['raw']['sell_min']
                raw_item_name = get_display_name(get_raw_item_id(tier, resource_type))
                st.sidebar.success(f"🔄 {raw_item_name}: {raw_price:,.0f} 🪙")
            else:
                st.sidebar.warning("⚠️ Prix ressource brute indisponible")
                raw_price = st.sidebar.number_input(
                    f"Prix {tier}_{resource_type} (manuel)",
                    min_value=1,
                    value=100,
                    step=10,
                    key=f"raw_price_{tier}_{resource_type}"
                )
            
            # Refined material price
            if 'refined' in city_data and city_data['refined']['sell_min'] > 0:
                refined_price = city_data['refined']['sell_min']
                refined_item_name = get_display_name(get_refined_item_id(tier, resource_type))
                st.sidebar.success(f"🔄 {refined_item_name}: {refined_price:,.0f} 🪙")
            else:
                st.sidebar.warning("⚠️ Prix ressource raffinée indisponible")
                refined_price = st.sidebar.number_input(
                    f"Prix raffiné (manuel)",
                    min_value=1,
                    value=350,
                    step=10,
                    key=f"refined_price_{tier}_{resource_type}"
                )
        else:
            st.sidebar.error("❌ Impossible de récupérer les prix")
            st.sidebar.subheader("Prix Manuels")
            raw_price = st.sidebar.number_input(
                f"Prix {tier}_{resource_type}",
                min_value=1,
                value=100,
                step=10,
                key=f"manual_raw_price_{tier}_{resource_type}"
            )
            refined_price = st.sidebar.number_input(
                f"Prix raffiné",
                min_value=1,
                value=350,
                step=10,
                key=f"manual_refined_price_{tier}_{resource_type}"
            )
        
        # Show best prices across all cities
        if market_prices:
            best_prices = self.get_best_prices_for_refining(tier, resource_type, cities)
            if best_prices:
                st.sidebar.markdown("---")
                st.sidebar.subheader("🎯 Meilleurs Prix")
                
                if best_prices['raw']['best_sell_city']:
                    st.sidebar.info(f"Achat: {best_prices['raw']['sell_min']:,.0f} à {best_prices['raw']['best_sell_city']}")
                
                if best_prices['refined']['best_sell_city']:
                    st.sidebar.info(f"Vente: {best_prices['refined']['sell_max']:,.0f} à {best_prices['refined']['best_sell_city']}")
        
        return raw_price, refined_price
    
    def get_arbitrage_opportunities(self, tier: str, resource_type: str, enchantment: int = 0) -> List[Dict]:
        """
        Find arbitrage opportunities across cities.
        
        Returns:
            List of profitable arbitrage opportunities
        """
        cities = ['Thetford', 'Fort Sterling', 'Lymhurst', 'Bridgewatch', 'Martlock', 'Caerleon', 'Brecilien']
        market_prices = self.get_refining_prices_cached(tier, resource_type, enchantment, cities)
        
        opportunities = []
        
        if not market_prices:
            return opportunities
        
        # Find raw material arbitrage
        raw_prices = {}
        refined_prices = {}
        
        for city, data in market_prices.items():
            if 'raw' in data and data['raw']['sell_min'] > 0:
                raw_prices[city] = data['raw']['sell_min']
            if 'refined' in data and data['refined']['sell_min'] > 0:
                refined_prices[city] = data['refined']['sell_min']
        
        # Find buy low, sell high opportunities
        if raw_prices:
            min_city = min(raw_prices.items(), key=lambda x: x[1])
            max_city = max(raw_prices.items(), key=lambda x: x[1])
            
            if max_city[1] > min_city[1] * 1.1:  # At least 10% margin
                opportunities.append({
                    'type': 'raw_arbitrage',
                    'item': f"{tier}_{resource_type}",
                    'buy_city': min_city[0],
                    'buy_price': min_city[1],
                    'sell_city': max_city[0],
                    'sell_price': max_city[1],
                    'profit_per_unit': max_city[1] - min_city[1],
                    'profit_margin': ((max_city[1] - min_city[1]) / min_city[1]) * 100
                })
        
        return opportunities
