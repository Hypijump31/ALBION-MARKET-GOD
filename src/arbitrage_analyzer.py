import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ArbitrageAnalyzer:
    """Analyseur d'arbitrage pour trouver les meilleures opportunités d'achat/vente."""
    
    def __init__(self, config=None, calculator=None):
        # Use configuration to get allowed cities, respecting exclusions
        if config:
            self.cities = config.get_allowed_cities()
            self.config = config
        else:
            # Fallback to default cities if no config provided
            self.cities = [
                'Thetford', 'Fort Sterling', 'Lymhurst', 
                'Bridgewatch', 'Martlock'
            ]
            self.config = None
        
        if not calculator:
            logger.warning("ArbitrageAnalyzer initialized without a RefiningCalculator. Refining arbitrage analysis will be disabled.")
        self.calculator = calculator
    
    def analyze_opportunities(self, price_data: Dict, tier: str, resource_type: str) -> Dict:
        """Analyser les opportunités d'arbitrage."""
        
        # Filtrer les villes selon la configuration
        if hasattr(self, 'config') and self.config:
            allowed_cities = self.config.get_allowed_cities()
            filtered_cities = [city for city in price_data.keys() if city in allowed_cities]
        else:
            filtered_cities = list(price_data.keys())
        
        # Extraire les prix pour les villes autorisées uniquement
        raw_prices = {}
        prev_refined_prices = {}
        refined_prices = {}
        
        for city in filtered_cities:
            city_data = price_data.get(city, {})
            
            if 'raw' in city_data and city_data['raw']['buy_max'] > 0:
                raw_prices[city] = {
                    'buy_price': city_data['raw']['buy_max'],
                    'sell_price': city_data['raw']['sell_min'],
                    'item_id': city_data['raw']['item_id']
                }
            
            if 'prev_refined' in city_data and city_data['prev_refined']['buy_max'] > 0:
                prev_refined_prices[city] = {
                    'buy_price': city_data['prev_refined']['buy_max'],
                    'sell_price': city_data['prev_refined']['sell_min'],
                    'item_id': city_data['prev_refined']['item_id']
                }
            
            if 'refined' in city_data and city_data['refined']['sell_min'] > 0:
                refined_prices[city] = {
                    'buy_price': city_data['refined']['buy_max'],
                    'sell_price': city_data['refined']['sell_min'],
                    'item_id': city_data['refined']['item_id']
                }
        
        # Analyser les opportunités
        results = {
            'raw_recommendations': self._find_best_buy_sell(raw_prices, 'raw', tier, resource_type),
            'prev_refined_recommendations': self._find_best_buy_sell(prev_refined_prices, 'prev_refined', tier, resource_type),
            'refined_recommendations': self._find_best_buy_sell(refined_prices, 'refined', tier, resource_type),
            'refining_opportunities': self._analyze_refining_arbitrage(raw_prices, prev_refined_prices, refined_prices, tier, resource_type)
        }
        
        return results
    
    def _find_best_buy_sell(self, prices: Dict, item_type: str, tier: str, resource_type: str) -> Dict:
        """Trouve les meilleures villes pour acheter et vendre."""
        if not prices:
            return {}
        
        # Trouver la meilleure ville pour acheter (prix de vente le plus bas)
        best_buy_city = None
        best_buy_price = float('inf')
        
        # Trouver la meilleure ville pour vendre (prix d'achat le plus haut)
        best_sell_city = None
        best_sell_price = 0
        
        for city, data in prices.items():
            sell_price = data['sell_price']
            buy_price = data['buy_price']
            
            # Meilleur endroit pour acheter (prix de vente le plus bas et > 0)
            if sell_price > 0 and sell_price < best_buy_price:
                best_buy_price = sell_price
                best_buy_city = city
            
            # Meilleur endroit pour vendre (prix d'achat le plus haut)
            if buy_price > best_sell_price:
                best_sell_price = buy_price
                best_sell_city = city
        
        # Calculer le profit potentiel
        profit = 0
        profit_margin = 0
        
        if best_buy_price < float('inf') and best_sell_price > 0:
            profit = best_sell_price - best_buy_price
            profit_margin = (profit / best_buy_price) * 100 if best_buy_price > 0 else 0
        
        return {
            'item_type': item_type,
            'tier': tier,
            'resource_type': resource_type,
            'buy_recommendation': {
                'city': best_buy_city,
                'price': best_buy_price if best_buy_price < float('inf') else 0,
                'action': 'ACHETER ICI'
            },
            'sell_recommendation': {
                'city': best_sell_city,
                'price': best_sell_price,
                'action': 'VENDRE ICI'
            },
            'arbitrage_profit': {
                'profit_per_unit': profit,
                'profit_margin_percent': profit_margin,
                'is_profitable': profit > 0 and profit_margin > 5  # Au moins 5% de marge
            }
        }
    
    def _analyze_refining_arbitrage(self, raw_prices: Dict, prev_refined_prices: Dict, refined_prices: Dict, tier: str, resource_type: str) -> Dict:
        """Analyse l'arbitrage de raffinage entre villes en utilisant le RefiningCalculator."""
        if not all([self.calculator, raw_prices, refined_prices, self.config]):
            logger.info("Refining arbitrage analysis skipped: missing calculator, price data, or config.")
            return {}

        opportunities = []
        
        # Find the best city to buy raw and previous refined materials
        try:
            best_raw_buy_city = min(raw_prices, key=lambda city: raw_prices[city]['sell_price'] if raw_prices[city]['sell_price'] > 0 else float('inf'))
            raw_buy_price = raw_prices[best_raw_buy_city]['sell_price']
        except (ValueError, KeyError):
            logger.warning("Could not determine best city to buy raw materials.")
            return {} # Not enough data to analyze

        prev_refined_buy_price = 0
        best_prev_refined_buy_city = None
        if prev_refined_prices:
            try:
                best_prev_refined_buy_city = min(prev_refined_prices, key=lambda city: prev_refined_prices[city]['sell_price'] if prev_refined_prices[city]['sell_price'] > 0 else float('inf'))
                prev_refined_buy_price = prev_refined_prices[best_prev_refined_buy_city]['sell_price']
            except (ValueError, KeyError):
                logger.warning("Could not determine best city to buy previous refined materials, assuming 0 cost.")
                prev_refined_buy_price = 0 # Continue analysis without it

        # Refining should happen in the optimal city for that resource
        optimal_refining_city = self.calculator.get_optimal_refining_city(resource_type)

        # Get player settings from config
        premium = self.config.premium
        use_focus = self.config.use_focus
        spec_key = f"{resource_type.lower()}_refining"
        specialization = self.config.get_specialization_level(spec_key)

        for sell_city, refined_data in refined_prices.items():
            refined_sell_price = refined_data['buy_price']
            
            if raw_buy_price > 0 and refined_sell_price > 0:
                # Calculate profit using the full calculator
                profit_result = self.calculator.calculate_refining_profit(
                    tier=tier,
                    resource_type=resource_type,
                    city=optimal_refining_city,
                    raw_price=raw_buy_price,
                    refined_price=refined_sell_price,
                    quantity=100,  # Use a standard quantity for comparison
                    specialization=specialization,
                    premium=premium,
                    use_focus=use_focus,
                    prev_refined_price=prev_refined_buy_price
                )
                
                if profit_result.net_profit > 0:
                    strategy = (f"Acheter brut à {best_raw_buy_city}, "
                                f"Raffiner à {optimal_refining_city}, "
                                f"Vendre raffiné à {sell_city}")
                    if best_prev_refined_buy_city:
                        strategy = (f"Acheter brut à {best_raw_buy_city} & T-1 à {best_prev_refined_buy_city}, "
                                    f"Raffiner à {optimal_refining_city}, "
                                    f"Vendre raffiné à {sell_city}")

                    opportunities.append({
                        'raw_city': best_raw_buy_city,
                        'refined_city': sell_city,
                        'refine_city': optimal_refining_city,
                        'raw_price': raw_buy_price,
                        'refined_price': refined_sell_price,
                        'estimated_profit': profit_result.net_profit,
                        'profit_margin': profit_result.profit_margin,
                        'strategy': strategy
                    })

        # Sort by profit descending
        opportunities.sort(key=lambda x: x['estimated_profit'], reverse=True)
        
        return {
            'best_opportunities': opportunities[:5],
            'total_opportunities': len(opportunities)
        }
    
    def display_recommendations(self, analysis: Dict, tier: str, resource_type: str):
        """Affiche les recommandations d'arbitrage dans Streamlit."""
        if not analysis:
            st.warning("⚠️ Aucune donnée d'arbitrage disponible")
            return
        
        st.markdown("## 💰 **RECOMMANDATIONS D'ARBITRAGE**")
        
        # Recommandations pour les matières brutes
        if 'raw_recommendations' in analysis and analysis['raw_recommendations']:
            raw_rec = analysis['raw_recommendations']
            st.markdown(f"### 🥉 **Matière Brute ({tier} {resource_type})**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                buy_rec = raw_rec.get('buy_recommendation', {})
                if buy_rec.get('city'):
                    st.success(f"🛒 **ACHETER À {buy_rec['city']}**")
                    st.metric("Prix d'achat", f"{buy_rec['price']:,.0f} 🪙")
            
            with col2:
                sell_rec = raw_rec.get('sell_recommendation', {})
                if sell_rec.get('city'):
                    st.info(f"💰 **VENDRE À {sell_rec['city']}**")
                    st.metric("Prix de vente", f"{sell_rec['price']:,.0f} 🪙")
            
            with col3:
                profit_info = raw_rec.get('arbitrage_profit', {})
                if profit_info.get('is_profitable'):
                    st.success("✅ **PROFITABLE**")
                    st.metric("Profit/unité", f"{profit_info['profit_per_unit']:,.0f} 🪙")
                    st.metric("Marge", f"{profit_info['profit_margin_percent']:.1f}%")
                else:
                    st.error("❌ **PAS RENTABLE**")
        
        # Recommandations pour les matières raffinées
        if 'refined_recommendations' in analysis and analysis['refined_recommendations']:
            refined_rec = analysis['refined_recommendations']
            st.markdown(f"### ⚡ **Matière Raffinée ({tier} {resource_type})**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                buy_rec = refined_rec.get('buy_recommendation', {})
                if buy_rec.get('city'):
                    st.success(f"🛒 **ACHETER À {buy_rec['city']}**")
                    st.metric("Prix d'achat", f"{buy_rec['price']:,.0f} 🪙")
            
            with col2:
                sell_rec = refined_rec.get('sell_recommendation', {})
                if sell_rec.get('city'):
                    st.info(f"💰 **VENDRE À {sell_rec['city']}**")
                    st.metric("Prix de vente", f"{sell_rec['price']:,.0f} 🪙")
            
            with col3:
                profit_info = refined_rec.get('arbitrage_profit', {})
                if profit_info.get('is_profitable'):
                    st.success("✅ **PROFITABLE**")
                    st.metric("Profit/unité", f"{profit_info['profit_per_unit']:,.0f} 🪙")
                    st.metric("Marge", f"{profit_info['profit_margin_percent']:.1f}%")
                else:
                    st.error("❌ **PAS RENTABLE**")
        
        
        st.markdown("---")
    
    def get_price_summary_table(self, price_data: Dict) -> pd.DataFrame:
        """Crée un tableau récapitulatif des prix par ville."""
        if not price_data:
            return pd.DataFrame()
        
        rows = []
        for city, city_data in price_data.items():
            row = {'Ville': city}
            
            if 'raw' in city_data:
                row['Raw_Buy'] = city_data['raw']['buy_max']
                row['Raw_Sell'] = city_data['raw']['sell_min']
            else:
                row['Raw_Buy'] = 0
                row['Raw_Sell'] = 0
            
            if 'refined' in city_data:
                row['Refined_Buy'] = city_data['refined']['buy_max']
                row['Refined_Sell'] = city_data['refined']['sell_min']
            else:
                row['Refined_Buy'] = 0
                row['Refined_Sell'] = 0
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        return df.sort_values('Ville')

# Instance globale (sera réinitialisée avec la config dans refining_analysis.py)
arbitrage_analyzer = None
