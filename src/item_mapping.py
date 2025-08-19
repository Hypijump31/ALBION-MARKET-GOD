"""
Albion Online Item ID mapping for API calls
Based on official game data and community resources
"""

# Resource mapping for raw materials
RAW_RESOURCES = {
    'T3_ORE': 'T3_ORE',
    'T4_ORE': 'T4_ORE',
    'T5_ORE': 'T5_ORE', 
    'T6_ORE': 'T6_ORE',
    'T7_ORE': 'T7_ORE',
    'T8_ORE': 'T8_ORE',
    
    'T3_WOOD': 'T3_WOOD',
    'T4_WOOD': 'T4_WOOD',
    'T5_WOOD': 'T5_WOOD',
    'T6_WOOD': 'T6_WOOD', 
    'T7_WOOD': 'T7_WOOD',
    'T8_WOOD': 'T8_WOOD',
    
    'T3_HIDE': 'T3_HIDE',
    'T4_HIDE': 'T4_HIDE',
    'T5_HIDE': 'T5_HIDE',
    'T6_HIDE': 'T6_HIDE',
    'T7_HIDE': 'T7_HIDE',
    'T8_HIDE': 'T8_HIDE',
    
    'T3_FIBER': 'T3_FIBER',
    'T4_FIBER': 'T4_FIBER',
    'T5_FIBER': 'T5_FIBER',
    'T6_FIBER': 'T6_FIBER',
    'T7_FIBER': 'T7_FIBER',
    'T8_FIBER': 'T8_FIBER',
    
    'T3_ROCK': 'T3_ROCK',
    'T4_ROCK': 'T4_ROCK',
    'T5_ROCK': 'T5_ROCK',
    'T6_ROCK': 'T6_ROCK',
    'T7_ROCK': 'T7_ROCK',
    'T8_ROCK': 'T8_ROCK'
}

# Refined resources mapping
REFINED_RESOURCES = {
    # Bars (from ore)
    'T3_ORE': 'T3_METALBAR',
    'T4_ORE': 'T4_METALBAR',
    'T5_ORE': 'T5_METALBAR',
    'T6_ORE': 'T6_METALBAR',
    'T7_ORE': 'T7_METALBAR',
    'T8_ORE': 'T8_METALBAR',
    
    # Planks (from wood)  
    'T3_WOOD': 'T3_PLANKS',
    'T4_WOOD': 'T4_PLANKS',
    'T5_WOOD': 'T5_PLANKS',
    'T6_WOOD': 'T6_PLANKS',
    'T7_WOOD': 'T7_PLANKS',
    'T8_WOOD': 'T8_PLANKS',
    
    # Leather (from hide)
    'T3_HIDE': 'T3_LEATHER',
    'T4_HIDE': 'T4_LEATHER',
    'T5_HIDE': 'T5_LEATHER', 
    'T6_HIDE': 'T6_LEATHER',
    'T7_HIDE': 'T7_LEATHER',
    'T8_HIDE': 'T8_LEATHER',
    
    # Cloth (from fiber)
    'T3_FIBER': 'T3_CLOTH',
    'T4_FIBER': 'T4_CLOTH',
    'T5_FIBER': 'T5_CLOTH',
    'T6_FIBER': 'T6_CLOTH',
    'T7_FIBER': 'T7_CLOTH',
    'T8_FIBER': 'T8_CLOTH',
    
    # Stone blocks (from rock/stone)
    'T3_ROCK': 'T3_STONEBLOCK',
    'T4_ROCK': 'T4_STONEBLOCK',
    'T5_ROCK': 'T5_STONEBLOCK',
    'T6_ROCK': 'T6_STONEBLOCK',
    'T7_ROCK': 'T7_STONEBLOCK',
    'T8_ROCK': 'T8_STONEBLOCK'
}

# Display names for UI
DISPLAY_NAMES = {
    'ORE': 'Minerai',
    'WOOD': 'Bois', 
    'HIDE': 'Cuir',
    'FIBER': 'Fibre',
    'ROCK': 'Pierre',
    'STONE': 'Pierre'
}

REFINED_DISPLAY_NAMES = {
    'T4_METALBAR': 'Lingot de Bronze',
    'T5_METALBAR': 'Lingot de Fer',
    'T6_METALBAR': 'Lingot d\'Acier',
    'T7_METALBAR': 'Lingot de Titane',
    'T8_METALBAR': 'Lingot d\'Adamantium',
    
    'T4_PLANKS': 'Planches de Bouleau',
    'T5_PLANKS': 'Planches de Chêne',
    'T6_PLANKS': 'Planches de Cèdre',
    'T7_PLANKS': 'Planches de Saule',
    'T8_PLANKS': 'Planches de Chêne Blanc',
    
    'T4_LEATHER': 'Cuir Brut',
    'T5_LEATHER': 'Cuir Fin',
    'T6_LEATHER': 'Cuir Robuste',
    'T7_LEATHER': 'Cuir Dur',
    'T8_LEATHER': 'Cuir Résistant',
    
    'T4_CLOTH': 'Tissu Brut',
    'T5_CLOTH': 'Tissu Simple',
    'T6_CLOTH': 'Tissu Élégant',
    'T7_CLOTH': 'Tissu Opulent', 
    'T8_CLOTH': 'Tissu Royal',
    
    'T4_STONEBLOCK': 'Bloc de Grès',
    'T5_STONEBLOCK': 'Bloc de Calcaire',
    'T6_STONEBLOCK': 'Bloc de Marbre',
    'T7_STONEBLOCK': 'Bloc de Basalte',
    'T8_STONEBLOCK': 'Bloc de Granit'
}

def get_raw_item_id(tier: str, resource_type: str, enchantment = 0) -> str:
    """Get raw resource item ID for API calls."""
    # Handle both int and list inputs
    if isinstance(enchantment, list):
        enchantment = int(enchantment[0]) if enchantment else 0
    
    key = f"{tier}_{resource_type}"
    base_id = RAW_RESOURCES.get(key, key)
    
    # Raw materials CAN have enchantments using LEVEL format
    if enchantment > 0:
        return f"{base_id}_LEVEL{enchantment}@{enchantment}"
    return base_id

def get_refined_item_id(tier: str, resource_type: str, enchantment = 0) -> str:
    """Get refined resource item ID for API calls."""
    # Handle both int and list inputs
    if isinstance(enchantment, list):
        enchantment = int(enchantment[0]) if enchantment else 0
    
    key = f"{tier}_{resource_type}"
    base_id = REFINED_RESOURCES.get(key, f"{tier}_REFINED_{resource_type}")
    # Refined materials CAN have enchantments using LEVEL format
    if enchantment > 0:
        return f"{base_id}_LEVEL{enchantment}@{enchantment}"
    return base_id

def get_display_name(item_id: str) -> str:
    """Get human-readable display name for an item."""
    return REFINED_DISPLAY_NAMES.get(item_id, item_id)

def get_resource_type_from_old_format(resource_type: str) -> str:
    """Convert old resource type format to new."""
    mapping = {
        'ORE': 'ORE',
        'WOOD': 'WOOD', 
        'HIDE': 'HIDE',
        'FIBER': 'FIBER',
        'STONE': 'ROCK'  # Stone is called ROCK in the API
    }
    return mapping.get(resource_type, resource_type)

# All available tiers and resources for UI
AVAILABLE_TIERS = ['T4', 'T5', 'T6', 'T7', 'T8']
AVAILABLE_RESOURCES = ['ORE', 'WOOD', 'HIDE', 'FIBER', 'ROCK']
