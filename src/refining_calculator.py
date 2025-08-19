"""
Albion Online Refining Profit Calculator
Based on official game mechanics and community research
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class RefiningResult:
    """Result of refining calculation."""
    total_cost: float
    total_revenue: float
    net_profit: float
    profit_margin: float
    focus_cost: int
    tax_cost: float
    return_rate: float
    resources_returned: int
    refined_quantity: int
    prev_refined_needed: int
    raw_material_cost: float
    prev_refined_material_cost: float
    output_value: float
    input_cost: float
    premium: bool
    use_focus: bool

# Albion Online refining data based on game mechanics
REFINING_DATA = {
    # Local Production Bonus per city and resource type (OFFICIAL DATA FROM WIKI)
    'local_production_bonus': {
        'Fort Sterling': {
            'ORE': 0.00,
            'WOOD': 0.40,     # +40% for wood (CORRECT)
            'HIDE': 0.00,
            'FIBER': 0.00,
            'STONE': 0.00,
            'ROCK': 0.00
        },
        'Lymhurst': {
            'ORE': 0.00,
            'WOOD': 0.00,
            'HIDE': 0.00,
            'FIBER': 0.40,    # +40% for fiber (CORRECT)
            'STONE': 0.00,
            'ROCK': 0.00
        },
        'Bridgewatch': {
            'ORE': 0.00,
            'WOOD': 0.00,
            'HIDE': 0.00,
            'FIBER': 0.00,
            'STONE': 0.40,    # +40% for stone (CORRECT)
            'ROCK': 0.40     # ROCK is same as STONE
        },
        'Martlock': {
            'ORE': 0.00,
            'WOOD': 0.00,
            'HIDE': 0.40,     # +40% for hide (CORRECT)
            'FIBER': 0.00,
            'STONE': 0.00,
            'ROCK': 0.00
        },
        'Thetford': {
            'ORE': 0.40,      # +40% for ore (CORRECT)
            'WOOD': 0.00,
            'HIDE': 0.00,
            'FIBER': 0.00,
            'STONE': 0.00,
            'ROCK': 0.00
        },
        'Caerleon': {
            'ORE': 0.00,
            'WOOD': 0.00,
            'HIDE': 0.00,
            'FIBER': 0.00,
            'STONE': 0.00,
            'ROCK': 0.00     # No bonuses in Caerleon
        },
        'Brecilien': {
            'ORE': 0.00,
            'WOOD': 0.00,
            'HIDE': 0.00,
            'FIBER': 0.00,
            'STONE': 0.00,
            'ROCK': 0.00     # No refining bonuses in Brecilien
        }
    },
    
    # Tax rates per city (usage fees)
    'tax_rates': {
        'Thetford': 0.045,
        'Fort Sterling': 0.045,
        'Lymhurst': 0.045,
        'Bridgewatch': 0.045,
        'Martlock': 0.045,
        'Caerleon': 0.035,
        'Brecilien': 0.020
    },
    
    # Base focus cost per refined resource (with 100 specialization)
    'base_focus_cost': {
        'T4': 10,
        'T5': 20,
        'T6': 40,
        'T7': 80,
        'T8': 160
    },
    
    # Resource requirements per refined material (raw + previous tier refined)
    'resource_requirements': {
        'T4': {'raw': 2, 'refined_prev': 1},   # 2 raw + 1 T3 refined = 1 T4 refined
        'T5': {'raw': 3, 'refined_prev': 1},   # 3 raw + 1 T4 refined = 1 T5 refined
        'T6': {'raw': 4, 'refined_prev': 1},   # 4 raw + 1 T5 refined = 1 T6 refined
        'T7': {'raw': 5, 'refined_prev': 1},   # 5 raw + 1 T6 refined = 1 T7 refined
        'T8': {'raw': 6, 'refined_prev': 1}    # 6 raw + 1 T7 refined = 1 T8 refined
    },
    
    # Resource type mapping (handle STONE -> ROCK conversion)
    'resource_type_mapping': {
        'ORE': 'ORE',
        'WOOD': 'WOOD',
        'HIDE': 'HIDE', 
        'FIBER': 'FIBER',
        'STONE': 'ROCK',  # API uses ROCK instead of STONE
        'ROCK': 'ROCK'
    },
    
    # Premium bonus
    'premium_bonus': 0.50,  # +50% focus efficiency (not return rate directly)
    
    # Focus bonus to LPB
    'focus_bonus': 0.45,     # Focus adds flat 45% to RRR (from 37.1% to 49.7%)

    # Base refining bonus without focus
    'base_refining_bonus': 0.18, # Corresponds to ~15.2% base return rate

    # Item Value for tax calculation (based on in-game data)
    'item_values': {
        'T2_RAW': 2,
        'T3_RAW': 4,
        'T4_RAW': 8,
        'T5_RAW': 16,
        'T6_RAW': 32,
        'T7_RAW': 64,
        'T8_RAW': 128,
        'T2_REFINED': 8,
        'T3_REFINED': 24,
        'T4_REFINED': 72,
        'T5_REFINED': 192,
        'T6_REFINED': 480,
        'T7_REFINED': 1152,
        'T8_REFINED': 2688
    },

    # Nutrition cost multiplier for tax calculation
    'nutrition_cost_multiplier': 0.1125
}

class RefiningCalculator:
    """Calculator for Albion Online refining profits."""
    
    def __init__(self):
        self.data = REFINING_DATA
    
    def get_optimal_refining_city(self, resource_type: str) -> str:
        """Get the optimal city for refining a specific resource type."""
        city_bonuses = self.data['local_production_bonus']
        optimal_city = None
        max_bonus = 0
        
        for city, bonuses in city_bonuses.items():
            bonus = bonuses.get(resource_type, 0)
            if bonus > max_bonus:
                max_bonus = bonus
                optimal_city = city
        
        return optimal_city if optimal_city else 'Caerleon'
    
    def normalize_resource_type(self, resource_type: str) -> str:
        """Convert resource type to API format."""
        return self.data['resource_type_mapping'].get(resource_type, resource_type)
    
    def get_local_production_bonus(self, city: str, resource_type: str) -> float:
        """
        Get the local production bonus for a specific resource type in a city.
        Based on official Albion Online wiki data.
        """
        # Official refining bonuses from Albion Online wiki
        city_bonuses = {
            'Fort Sterling': {'WOOD': 0.40},
            'Lymhurst': {'FIBER': 0.40},
            'Bridgewatch': {'ROCK': 0.40},
            'Martlock': {'HIDE': 0.40},
            'Thetford': {'ORE': 0.40},
            'Caerleon': {},  # No refining bonuses
            'Brecilien': {}  # No refining bonuses
        }
        
        city_bonus = city_bonuses.get(city, {})
        return city_bonus.get(resource_type, 0.0)

    def calculate_return_rate(self, city: str, resource_type: str, use_focus: bool = True, 
                            personal_island: bool = False) -> float:
        """
        Calculate resource return rate based on Albion Online mechanics.
        
        Formula with focus: RRR = 1 - 1/(1 + 0.59 + LPB)
        Formula without focus: RRR = 1 - 1/(1 + LPB)
        
        Args:
            city: City where refining takes place
            resource_type: Type of resource (ORE, WOOD, HIDE, FIBER, ROCK)
            use_focus: Whether focus is used
            personal_island: Whether refining on personal island
            
        Returns:
            Return rate as decimal (e.g., 0.371 for 37.1%)
        """
        # Base return rate is always present
        total_bonus = self.data['base_refining_bonus']

        # Add city bonus if not on a personal island
        if not personal_island:
            total_bonus += self.get_local_production_bonus(city, resource_type)

        # Add focus bonus if used
        if use_focus:
            total_bonus += self.data['focus_bonus']

        # Final formula: RRR = 1 - 1 / (1 + Total Bonus)
        rrr = 1 - (1 / (1 + total_bonus))
        
        return rrr
    
    def calculate_focus_cost(self, tier: str, quantity: int, specialization: int = 0, 
                           premium: bool = False) -> int:
        """
        Calculate focus cost for refining.
        
        Args:
            tier: Resource tier (T4, T5, etc.)
            quantity: Number of resources to refine
            specialization: Specialization level (0-100)
            premium: Whether player has premium
            
        Returns:
            Total focus cost
        """
        base_cost = self.data['base_focus_cost'].get(tier, 10)
        
        # Specialization reduces focus cost
        spec_reduction = 1 - (specialization / 100 * 0.5)  # Up to 50% reduction at 100 spec
        
        # Premium reduces focus cost by 50%
        premium_reduction = (1 - self.data['premium_bonus']) if premium else 1.0
        
        total_cost = base_cost * quantity * spec_reduction * premium_reduction
        
        return max(1, int(total_cost))
    
    def calculate_refining_profit(self, tier: str, resource_type: str, city: str,
                                raw_price: float, refined_price: float, quantity: int = 100,
                                specialization: int = 0, premium: bool = False,
                                use_focus: bool = True, prev_refined_price: float = 0) -> RefiningResult:
        """
        Calculate complete refining profit analysis.
        
        Args:
            tier: Resource tier (T4, T5, T6, T7, T8)
            resource_type: Type (ORE, WOOD, HIDE, FIBER, STONE)
            city: City for refining
            raw_price: Price per raw resource
            refined_price: Price per refined resource
            quantity: Number of raw resources to process
            specialization: Specialization level (0-100)
            premium: Premium status
            use_focus: Use focus points
            prev_refined_price: Price per previous tier refined material
            
        Returns:
            RefiningResult with complete analysis
        """
        # Get resource requirements
        requirements = self.data['resource_requirements'].get(tier, {'raw': 2, 'refined_prev': 1})
        raw_per_refined = requirements['raw']
        prev_refined_per_refined = requirements['refined_prev']
        
        # Calculate how many refined materials we can make
        refined_quantity = quantity // raw_per_refined
        
        if refined_quantity == 0:
            logger.warning(f"Not enough resources to refine. Need {raw_per_refined} raw for 1 refined.")
            return RefiningResult(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, premium=premium, use_focus=use_focus)

        # Calculate how many previous tier refined materials are needed
        prev_refined_needed = refined_quantity * prev_refined_per_refined

        # Calculate costs
        raw_material_cost = quantity * raw_price
        prev_refined_material_cost = prev_refined_needed * prev_refined_price
        input_cost = raw_material_cost + prev_refined_material_cost

        # Calculate return rate and focus cost
        return_rate = self.calculate_return_rate(city, resource_type, use_focus)
        focus_cost = self.calculate_focus_cost(tier, refined_quantity, specialization, premium) if use_focus else 0

        # Calculate tax
        tax_rate = self.data['tax_rates'].get(city, 0.05)
        item_value = self.data['item_values'].get(f"{tier}_REFINED", 0)
        tax_cost = refined_quantity * item_value * self.data['nutrition_cost_multiplier'] * tax_rate

        total_cost = input_cost + tax_cost

        # Calculate revenue
        total_revenue = refined_quantity * refined_price
        
        # Calculate resource return value
        resources_returned_value = (quantity * return_rate * raw_price) + (prev_refined_needed * return_rate * prev_refined_price)
        total_revenue += resources_returned_value

        # Final profit calculation
        net_profit = total_revenue - total_cost
        profit_margin = (net_profit / total_cost) * 100 if total_cost > 0 else 0
        resources_returned = int(quantity * return_rate)

        return RefiningResult(
            total_cost=total_cost,
            total_revenue=total_revenue,
            net_profit=net_profit,
            profit_margin=profit_margin,
            focus_cost=focus_cost,
            tax_cost=tax_cost,
            return_rate=return_rate,
            resources_returned=resources_returned,
            refined_quantity=refined_quantity,
            prev_refined_needed=prev_refined_needed,
            raw_material_cost=raw_material_cost,
            prev_refined_material_cost=prev_refined_material_cost,
            output_value=total_revenue, # Simplified for now
            input_cost=input_cost,
            premium=premium,
            use_focus=use_focus
        )

    def find_best_refining_city(self, tier: str, resource_type: str, raw_price: float,
                              refined_price: float, specialization: int = 0, 
                              premium: bool = False, use_focus: bool = True, 
                              prev_refined_price: float = 0) -> Dict:
        """
        Find the most profitable city for refining a specific resource.
        
        Returns:
            Dictionary with city rankings and profit analysis
        """
        results = {}
        cities = list(self.data['local_production_bonus'].keys())
        
        for city in cities:
            result = self.calculate_refining_profit(
                tier, resource_type, city, raw_price, refined_price,
                quantity=100, specialization=specialization, 
                premium=premium, use_focus=use_focus,
                prev_refined_price=prev_refined_price
            )
            
            results[city] = {
                'profit': result.net_profit,
                'margin': result.profit_margin,
                'return_rate': result.return_rate,
                'tax_rate': self.data['tax_rates'].get(city, 0.05),
                'lpb': self.get_local_production_bonus(city, resource_type),
                'full_result': result
            }
        
        # Sort by profit
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1]['profit'], reverse=True))
        
        return sorted_results
    
    def calculate_break_even_price(self, tier: str, resource_type: str, city: str,
                                 refined_price: float, specialization: int = 0,
                                 premium: bool = False, use_focus: bool = True,
                                 prev_refined_price: float = 0) -> float:
        """
        Calculate the maximum price you can pay for raw resources to break even.
        
        Returns:
            Maximum raw resource price for break-even
        """
        # Binary search for break-even price
        low, high = 1.0, refined_price * 10
        tolerance = 0.01
        
        while high - low > tolerance:
            mid = (low + high) / 2
            
            result = self.calculate_refining_profit(
                tier, resource_type, city, mid, refined_price,
                quantity=100, specialization=specialization,
                premium=premium, use_focus=use_focus,
                prev_refined_price=prev_refined_price
            )
            
            if result.net_profit > 0:
                low = mid
            else:
                high = mid
        
        return low

# Example usage and testing
if __name__ == "__main__":
    calculator = RefiningCalculator()
    
    # Example: Calculate T5 ore refining profit in Thetford
    result = calculator.calculate_refining_profit(
        tier='T5',
        resource_type='ORE',
        city='Thetford',
        raw_price=100,  # 100 silver per raw ore
        refined_price=350,  # 350 silver per refined ore
        quantity=300,  # Process 300 raw ore
        specialization=50,  # 50 specialization
        premium=True,
        use_focus=True
    )
    
    print(f"Refining Analysis:")
    print(f"Total Cost: {result.total_cost:,.0f} silver")
    print(f"Total Revenue: {result.total_revenue:,.0f} silver") 
    print(f"Tax Cost: {result.tax_cost:,.0f} silver")
    print(f"Focus Cost: {result.focus_cost:,} focus points")
    print(f"Net Profit: {result.net_profit:,.0f} silver")
    print(f"Profit Margin: {result.profit_margin:.1f}%")
    print(f"Return Rate: {result.return_rate:.1f}%")
    print(f"Resources Returned: {result.resources_returned}")
    
    print("\n" + "="*50)
    
    # Find best city for T5 ore refining
    best_cities = calculator.find_best_refining_city(
        tier='T5',
        resource_type='ORE',
        raw_price=100,
        refined_price=350,
        specialization=50,
        premium=True,
        use_focus=True
    )
    
    print("Best Cities for T5 Ore Refining:")
    for i, (city, data) in enumerate(best_cities.items(), 1):
        print(f"{i}. {city}: {data['profit']:,.0f} silver profit ({data['margin']:.1f}% margin)")
    
    print("\n" + "="*50)
    
    # Calculate break-even price
    break_even = calculator.calculate_break_even_price(
        tier='T5',
        resource_type='ORE', 
        city='Thetford',
        refined_price=350,
        specialization=50,
        premium=True,
        use_focus=True
    )
    
    print(f"Break-even price for T5 ore in Thetford: {break_even:.0f} silver")
