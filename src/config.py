import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import os

@dataclass
class AlbionConfig:
    """Configuration class for Albion Online market analyzer."""
    
    # API Configuration
    server: str = 'Europe'  # Europe, Americas, Asia
    
    # Player Settings
    premium: bool = False
    
    # Crafting/Refining Settings
    focus_points: int = 10000  # Available focus points
    use_focus: bool = True
    
    # Specialization levels (0-100)
    specializations: Dict[str, int] = None
    
    # Crafting location settings
    crafting_city: str = 'Caerleon'
    
    # Resource return rates (affected by specialization, premium, food, etc.)
    base_return_rate: float = 0.152  # Base 15.2% return rate
    premium_bonus: float = 0.05  # +5% return rate with premium
    specialization_bonus: float = 0.0  # Bonus from specialization
    food_bonus: float = 0.0  # Bonus from food
    
    # Quality settings
    use_quality_items: bool = False
    preferred_quality: str = 'normal'  # normal, good, outstanding, excellent, masterpiece
    
    # Journal settings
    use_journals: bool = False
    journal_efficiency: float = 1.0  # How efficiently we use journals
    
    # Tax settings (different per city)
    tax_rates: Dict[str, float] = None
    
    # Equipment bonuses
    equipment_return_bonus: float = 0.0  # Bonus from crafting gear
    equipment_focus_reduction: float = 0.0  # Focus cost reduction from gear
    
    # Advanced settings
    calculate_transportation_costs: bool = False
    profit_margin_threshold: float = 0.1  # Minimum 10% profit margin
    
    # City filtering options
    exclude_brecilien: bool = False
    exclude_caerleon: bool = False
    
    def __post_init__(self):
        if self.specializations is None:
            self.specializations = {
                # Refining
                'ore_refining': 0,
                'hide_refining': 0,
                'fiber_refining': 0,
                'wood_refining': 0,
                'stone_refining': 0,
                
                # Crafting
                'weapon_smith': 0,
                'armor_smith': 0,
                'toolmaker': 0,
                'artifact_founder': 0,
                'cook': 0,
                'alchemist': 0,
                'scholar': 0,
                'farmer': 0,
                'hunter': 0,
                'fisher': 0,
                'lumberjack': 0,
                'miner': 0,
                'quarrier': 0
            }
        
        if self.tax_rates is None:
            # Default tax rates per city (approximate)
            self.tax_rates = {
                'Thetford': 0.045,      # 4.5%
                'Fort Sterling': 0.045,  # 4.5%
                'Lymhurst': 0.045,      # 4.5%
                'Bridgewatch': 0.045,   # 4.5%
                'Martlock': 0.045,      # 4.5%
                'Caerleon': 0.035,      # 3.5%
                'Brecilien': 0.02       # 2.0%
            }
    
    def get_total_return_rate(self, activity_type: str) -> float:
        """
        Calculate total return rate for a specific activity.
        
        Args:
            activity_type: Type of activity (e.g., 'ore_refining', 'weapon_smith')
            
        Returns:
            Total return rate including all bonuses
        """
        total_rate = self.base_return_rate
        
        # Premium bonus
        if self.premium:
            total_rate += self.premium_bonus
        
        # Specialization bonus (approximately 0.5% per 10 spec levels)
        if activity_type in self.specializations:
            spec_level = self.specializations[activity_type]
            total_rate += (spec_level / 10) * 0.005
        
        # Food bonus
        total_rate += self.food_bonus
        
        # Equipment bonus
        total_rate += self.equipment_return_bonus
        
        return min(total_rate, 1.0)  # Cap at 100%
    
    def get_focus_cost_multiplier(self, activity_type: str) -> float:
        """
        Calculate focus cost multiplier including equipment bonuses.
        
        Returns:
            Multiplier for focus costs (1.0 = normal, 0.8 = 20% reduction)
        """
        multiplier = 1.0
        
        # Equipment bonus for focus reduction
        multiplier -= self.equipment_focus_reduction
        
        # Specialization can reduce focus costs
        if activity_type in self.specializations:
            spec_level = self.specializations[activity_type]
            # Rough approximation: 1% focus reduction per 20 spec levels
            multiplier -= (spec_level / 20) * 0.01
        
        return max(multiplier, 0.1)  # Minimum 10% of original cost
    
    def get_tax_rate(self, city: str) -> float:
        """Get tax rate for a specific city."""
        return self.tax_rates.get(city, 0.05)  # Default 5% if city not found
    
    def get_local_production_bonus(self, city: str, resource_type: str) -> float:
        """
        Get the local production bonus for a specific resource type in a city.
        Based on official Albion Online wiki data.
        
        Args:
            city: City name
            resource_type: Resource type (ORE, WOOD, HIDE, FIBER, ROCK)
            
        Returns:
            Local production bonus (e.g., 0.40 for +40%)
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
    
    def get_allowed_cities(self) -> List[str]:
        """Get list of allowed cities based on exclusion settings."""
        all_cities = list(self.tax_rates.keys())
        allowed_cities = []
        
        for city in all_cities:
            if self.exclude_brecilien and city == 'Brecilien':
                continue
            if self.exclude_caerleon and city == 'Caerleon':
                continue
            allowed_cities.append(city)
        
        return allowed_cities
    
    def get_specialization_level(self, activity_type: str) -> int:
        """Get specialization level for a specific activity."""
        return self.specializations.get(activity_type, 0)
    
    def save_config(self, filepath: str = 'config.json'):
        """Save configuration to a JSON file."""
        config_dict = asdict(self)
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load_config(cls, filepath: str = 'config.json') -> 'AlbionConfig':
        """Load configuration from a JSON file."""
        if not os.path.exists(filepath):
            return cls()  # Return default config if file doesn't exist
        
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        
        return cls(**config_dict)

# Default configuration instance
default_config = AlbionConfig()

# Quality multipliers for items
QUALITY_MULTIPLIERS = {
    'normal': 1.0,
    'good': 1.2,
    'outstanding': 1.4,
    'excellent': 1.6,
    'masterpiece': 2.0
}

# Focus costs for different activities (base costs)
FOCUS_COSTS = {
    # Refining (per resource)
    'ore_refining': {
        'T4': 10,
        'T5': 20,
        'T6': 40,
        'T7': 80,
        'T8': 160
    },
    'hide_refining': {
        'T4': 10,
        'T5': 20,
        'T6': 40,
        'T7': 80,
        'T8': 160
    },
    # Add more as needed
}

# Popular food buffs for crafting/refining
FOOD_BUFFS = {
    'none': {'name': 'No Food', 'return_bonus': 0.0, 'focus_reduction': 0.0},
    'carrot_soup': {'name': 'Carrot Soup', 'return_bonus': 0.062, 'focus_reduction': 0.0},
    'wheat_soup': {'name': 'Wheat Soup', 'return_bonus': 0.044, 'focus_reduction': 0.125},
    'bean_salad': {'name': 'Bean Salad', 'return_bonus': 0.038, 'focus_reduction': 0.0},
    # Add more food buffs
}
