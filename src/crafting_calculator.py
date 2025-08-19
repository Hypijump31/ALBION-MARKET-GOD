import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

logger = logging.getLogger(__name__)

@dataclass
class CraftingResult:
    """Result of crafting profit calculation."""
    net_profit: float
    gross_profit: float
    total_cost: float
    total_revenue: float
    profit_margin: float
    return_rate: float
    focus_cost: int
    tax_amount: float
    material_costs: Dict[str, float]
    items_produced: float
    break_even_price: float

class CraftingCalculator:
    """Calculator for Albion Online crafting profitability."""
    
    def __init__(self):
        """Initialize the crafting calculator with game data."""
        self.data = self._load_crafting_data()
    
    def _load_crafting_data(self) -> Dict:
        """Load crafting data including recipes, return rates, and city bonuses."""
        return {
            # Base return rates for crafting (without focus)
            'base_return_rate': {
                'T4': 0.15,  # 15% return rate
                'T5': 0.20,  # 20% return rate
                'T6': 0.22,  # 22% return rate
                'T7': 0.24,  # 24% return rate
                'T8': 0.26   # 26% return rate
            },
            
            # Focus usage per craft (base values)
            'focus_per_craft': {
                'T4': 10,
                'T5': 20,
                'T6': 40,
                'T7': 80,
                'T8': 160
            },
            
            # Crafting station tax rates by city
            'tax_rates': {
                'Caerleon': 0.035,      # 3.5%
                'Thetford': 0.045,      # 4.5%
                'Fort Sterling': 0.045,  # 4.5%
                'Lymhurst': 0.045,      # 4.5%
                'Bridgewatch': 0.045,   # 4.5%
                'Martlock': 0.045,      # 4.5%
                'Brecilien': 0.045      # 4.5%
            },
            
            # City crafting bonuses (reduces resource requirements)
            'city_bonuses': {
                'Thetford': {
                    'FIBER': 0.15,    # 15% resource reduction for fiber crafting
                    'CLOTH': 0.15
                },
                'Fort Sterling': {
                    'ORE': 0.15,      # 15% resource reduction for ore crafting
                    'METAL': 0.15
                },
                'Lymhurst': {
                    'WOOD': 0.15,     # 15% resource reduction for wood crafting
                },
                'Bridgewatch': {
                    'HIDE': 0.15,     # 15% resource reduction for hide crafting
                    'LEATHER': 0.15
                },
                'Martlock': {
                    'ROCK': 0.15,     # 15% resource reduction for rock crafting
                    'STONE': 0.15
                },
                'Caerleon': {},       # No specific bonuses but lower tax
                'Brecilien': {}       # Ava roads city, no specific bonuses
            },
            
            # Basic crafting recipes (simplified - real game has many more)
            'recipes': {
                # Weapons
                'T4_SWORD': {
                    'materials': {'T4_METAL': 16, 'T3_METAL': 8},
                    'category': 'WEAPON',
                    'crafting_city_bonus': 'METAL'
                },
                'T5_SWORD': {
                    'materials': {'T5_METAL': 16, 'T4_METAL': 8},
                    'category': 'WEAPON', 
                    'crafting_city_bonus': 'METAL'
                },
                'T6_SWORD': {
                    'materials': {'T6_METAL': 16, 'T5_METAL': 8},
                    'category': 'WEAPON',
                    'crafting_city_bonus': 'METAL'
                },
                'T7_SWORD': {
                    'materials': {'T7_METAL': 16, 'T6_METAL': 8},
                    'category': 'WEAPON',
                    'crafting_city_bonus': 'METAL'
                },
                'T8_SWORD': {
                    'materials': {'T8_METAL': 16, 'T7_METAL': 8},
                    'category': 'WEAPON',
                    'crafting_city_bonus': 'METAL'
                },
                
                # Armor pieces
                'T4_ARMOR_CLOTH_ROBE': {
                    'materials': {'T4_CLOTH': 16, 'T3_CLOTH': 8},
                    'category': 'ARMOR',
                    'crafting_city_bonus': 'CLOTH'
                },
                'T5_ARMOR_CLOTH_ROBE': {
                    'materials': {'T5_CLOTH': 16, 'T4_CLOTH': 8},
                    'category': 'ARMOR',
                    'crafting_city_bonus': 'CLOTH'
                },
                'T6_ARMOR_CLOTH_ROBE': {
                    'materials': {'T6_CLOTH': 16, 'T5_CLOTH': 8},
                    'category': 'ARMOR',
                    'crafting_city_bonus': 'CLOTH'
                },
                
                # Bags
                'T4_BAG': {
                    'materials': {'T4_CLOTH': 8, 'T4_LEATHER': 4},
                    'category': 'ACCESSORY',
                    'crafting_city_bonus': 'CLOTH'
                },
                'T5_BAG': {
                    'materials': {'T5_CLOTH': 8, 'T5_LEATHER': 4},
                    'category': 'ACCESSORY',
                    'crafting_city_bonus': 'CLOTH'
                },
                'T6_BAG': {
                    'materials': {'T6_CLOTH': 8, 'T6_LEATHER': 4},
                    'category': 'ACCESSORY',
                    'crafting_city_bonus': 'CLOTH'
                }
            }
        }
    
    def calculate_return_rate(self, tier: str, specialization: int, premium: bool, use_focus: bool) -> float:
        """
        Calculate the return rate for crafting.
        
        Args:
            tier: Item tier (T4, T5, etc.)
            specialization: Specialization level (0-100)
            premium: Whether player has premium
            use_focus: Whether using focus points
            
        Returns:
            Return rate as decimal (0.15 = 15%)
        """
        base_rate = self.data['base_return_rate'].get(tier, 0.15)
        
        # Specialization bonus (up to 30% at level 100)
        spec_bonus = (specialization / 100) * 0.30
        
        if use_focus:
            # Focus significantly increases return rate
            # Formula: RRR = base + spec_bonus + focus_bonus
            focus_bonus = 0.35  # 35% additional return rate with focus
            return_rate = base_rate + spec_bonus + focus_bonus
        else:
            return_rate = base_rate + spec_bonus
        
        # Cap at reasonable maximum (around 70%)
        return min(return_rate, 0.70)
    
    def calculate_focus_cost(self, tier: str, specialization: int, premium: bool, use_focus: bool) -> int:
        """
        Calculate focus cost for crafting.
        
        Args:
            tier: Item tier
            specialization: Specialization level (0-100)
            premium: Whether player has premium
            use_focus: Whether using focus points
            
        Returns:
            Focus cost per craft
        """
        if not use_focus:
            return 0
        
        base_focus = self.data['focus_per_craft'].get(tier, 10)
        
        # Specialization reduces focus cost (up to 50% reduction at level 100)
        spec_reduction = (specialization / 100) * 0.50
        
        # Premium increases focus efficiency (but we apply that as bonus, not cost reduction)
        focus_cost = base_focus * (1 - spec_reduction)
        
        return max(int(focus_cost), 1)  # Minimum 1 focus
    
    def calculate_crafting_profit(self, 
                                item_id: str,
                                city: str,
                                material_prices: Dict[str, float],
                                item_sell_price: float,
                                quantity: int = 1,
                                specialization: int = 0,
                                premium: bool = False,
                                use_focus: bool = False) -> CraftingResult:
        """
        Calculate crafting profitability for an item.
        
        Args:
            item_id: ID of item to craft
            city: City where crafting takes place
            material_prices: Dict of material prices {material_id: price}
            item_sell_price: Selling price of crafted item
            quantity: Number of items to craft
            specialization: Specialization level (0-100)
            premium: Whether player has premium
            use_focus: Whether to use focus points
            
        Returns:
            CraftingResult with detailed profit information
        """
        if item_id not in self.data['recipes']:
            raise ValueError(f"Recipe not found for {item_id}")
        
        recipe = self.data['recipes'][item_id]
        tier = item_id.split('_')[0]  # Extract tier (T4, T5, etc.)
        
        # Calculate return rate
        return_rate = self.calculate_return_rate(tier, specialization, premium, use_focus)
        
        # Calculate focus cost
        focus_cost = self.calculate_focus_cost(tier, specialization, premium, use_focus)
        
        # Get city bonus for this crafting type
        city_bonus = 0
        crafting_bonus_type = recipe.get('crafting_city_bonus', '')
        if city in self.data['city_bonuses'] and crafting_bonus_type in self.data['city_bonuses'][city]:
            city_bonus = self.data['city_bonuses'][city][crafting_bonus_type]
        
        # Calculate material costs with city bonus
        material_costs = {}
        total_material_cost = 0
        
        for material, base_amount in recipe['materials'].items():
            # Apply city bonus (reduces material requirements)
            actual_amount = base_amount * (1 - city_bonus) * quantity
            material_price = material_prices.get(material, 0)
            
            if material_price == 0:
                logger.warning(f"No price data for material {material}")
            
            cost = actual_amount * material_price
            material_costs[material] = cost
            total_material_cost += cost
        
        # Calculate items produced (base + return materials)
        items_produced = quantity * (1 + return_rate)
        
        # Calculate revenue
        total_revenue = items_produced * item_sell_price
        
        # Calculate tax
        tax_rate = self.data['tax_rates'].get(city, 0.05)
        tax_amount = total_revenue * tax_rate
        
        # Calculate profit
        gross_profit = total_revenue - total_material_cost
        net_profit = gross_profit - tax_amount
        
        # Calculate profit margin
        total_cost = total_material_cost + tax_amount
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Calculate break-even price
        break_even_price = total_cost / items_produced if items_produced > 0 else 0
        
        return CraftingResult(
            net_profit=net_profit,
            gross_profit=gross_profit,
            total_cost=total_cost,
            total_revenue=total_revenue,
            profit_margin=profit_margin,
            return_rate=return_rate,
            focus_cost=focus_cost * quantity,
            tax_amount=tax_amount,
            material_costs=material_costs,
            items_produced=items_produced,
            break_even_price=break_even_price
        )
    
    def find_best_crafting_city(self, 
                               item_id: str,
                               material_prices_by_city: Dict[str, Dict[str, float]],
                               item_sell_prices_by_city: Dict[str, float],
                               quantity: int = 1,
                               specialization: int = 0,
                               premium: bool = False,
                               use_focus: bool = False) -> Dict[str, CraftingResult]:
        """
        Find the best city for crafting based on material costs and selling prices.
        
        Args:
            item_id: Item to craft
            material_prices_by_city: Material prices by city
            item_sell_prices_by_city: Item selling prices by city
            quantity: Number to craft
            specialization: Specialization level
            premium: Premium status
            use_focus: Use focus points
            
        Returns:
            Dict of city results sorted by profit
        """
        results = {}
        
        for city in self.data['tax_rates'].keys():
            try:
                # Get prices for this city
                material_prices = material_prices_by_city.get(city, {})
                sell_price = item_sell_prices_by_city.get(city, 0)
                
                if not material_prices or sell_price == 0:
                    continue
                
                result = self.calculate_crafting_profit(
                    item_id=item_id,
                    city=city,
                    material_prices=material_prices,
                    item_sell_price=sell_price,
                    quantity=quantity,
                    specialization=specialization,
                    premium=premium,
                    use_focus=use_focus
                )
                
                results[city] = result
                
            except Exception as e:
                logger.error(f"Error calculating crafting profit for {city}: {e}")
                continue
        
        # Sort by net profit
        return dict(sorted(results.items(), key=lambda x: x[1].net_profit, reverse=True))
    
    def get_available_recipes(self) -> List[str]:
        """Get list of available crafting recipes."""
        return list(self.data['recipes'].keys())
    
    def get_recipe_materials(self, item_id: str) -> Dict[str, int]:
        """Get materials required for a recipe."""
        if item_id not in self.data['recipes']:
            return {}
        return self.data['recipes'][item_id]['materials']
    
    def get_recipe_category(self, item_id: str) -> str:
        """Get the category of a recipe (WEAPON, ARMOR, etc.)."""
        if item_id not in self.data['recipes']:
            return 'UNKNOWN'
        return self.data['recipes'][item_id].get('category', 'UNKNOWN')

# Example usage
if __name__ == "__main__":
    calculator = CraftingCalculator()
    
    # Example: Calculate profit for crafting T4 swords
    material_prices = {
        'T4_METAL': 150,
        'T3_METAL': 75
    }
    
    result = calculator.calculate_crafting_profit(
        item_id='T4_SWORD',
        city='Fort Sterling',  # Good for metal crafting
        material_prices=material_prices,
        item_sell_price=2000,
        quantity=1,
        specialization=50,
        premium=True,
        use_focus=True
    )
    
    print(f"Net Profit: {result.net_profit:,.0f}")
    print(f"Profit Margin: {result.profit_margin:.1f}%")
    print(f"Items Produced: {result.items_produced:.2f}")
    print(f"Return Rate: {result.return_rate:.1%}")
