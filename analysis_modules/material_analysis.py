"""
Complete material refining profitability analysis with enchantments
Analyzes all tiers (T4-T8) and all materials (ORE, WOOD, HIDE, FIBER, ROCK) with enchantments (0-4)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_collector import AlbionMarketData
from refining_calculator import RefiningCalculator
from item_mapping import get_raw_item_id, get_refined_item_id, get_display_name, AVAILABLE_TIERS, AVAILABLE_RESOURCES
from config import AlbionConfig


# Configuration complète
ENCHANT_LEVELS = [0, 1, 2, 3, 4]
ALL_TIERS = AVAILABLE_TIERS  # ['T4', 'T5', 'T6', 'T7', 'T8']
ALL_RESOURCES = AVAILABLE_RESOURCES  # ['ORE', 'WOOD', 'HIDE', 'FIBER', 'ROCK']

# Material names by tier
MATERIAL_NAMES = {
    'ORE': {
        'T3': 'Tin', 'T4': 'Copper', 'T5': 'Iron', 'T6': 'Steel', 'T7': 'Titanium', 'T8': 'Adamantium'
    },
    'WOOD': {
        'T3': 'Chestnut', 'T4': 'Birch', 'T5': 'Oak', 'T6': 'Cedar', 'T7': 'Willow', 'T8': 'Whitewood'
    },
    'HIDE': {
        'T3': 'Fox Hide', 'T4': 'Wolf Hide', 'T5': 'Boar Hide', 'T6': 'Bear Hide', 'T7': 'Dragon Hide', 'T8': 'Mammoth Hide'
    },
    'FIBER': {
        'T3': 'Wild Flax', 'T4': 'Cotton', 'T5': 'Flax', 'T6': 'Hemp', 'T7': 'Ghost Hemp', 'T8': 'Silkweed'
    },
    'ROCK': {
        'T3': 'Limestone', 'T4': 'Sandstone', 'T5': 'Slate', 'T6': 'Marble', 'T7': 'Basalt', 'T8': 'Granite'
    }
}

# Resource icons
RESOURCE_ICONS = {
    'ORE': '⚒️',
    'WOOD': '🌳', 
    'HIDE': '🦌',
    'FIBER': '🌾',
    'ROCK': '🗿'
}

def get_enchanted_item_id(base_item_id: str, enchant_level: int) -> str:
    """Generate item ID with enchantment."""
    if enchant_level == 0:
        return base_item_id
    return f"{base_item_id}@{enchant_level}"

def get_enchanted_display_name(tier: str, resource_type: str, enchant: int) -> str:
    """Generate display name for material with tier and enchantment."""
    base_name = MATERIAL_NAMES.get(resource_type, {}).get(tier, f"{tier} {resource_type}")
    
    # Add tier with enchantment
    tier_display = tier
    if enchant > 0:
        tier_display = f"{tier}.{enchant}"
    
    return f"{base_name} ({tier_display})"

@st.cache_data(ttl=300)
def get_material_prices_all_enchants(region: str, selected_resources: list) -> pd.DataFrame:
    """Fetch prices for all selected materials and enchantments."""
    collector = AlbionMarketData(region=region)
    all_data = []
    
    # Build list of all items to fetch
    all_items = []
    
    # Available tiers with T3 for previous refined materials
    all_tiers_with_t3 = ['T3', 'T4', 'T5', 'T6', 'T7', 'T8']
    
    for resource_type in selected_resources:
        for tier in all_tiers_with_t3:
            for enchant in ENCHANT_LEVELS:
                raw_base = get_raw_item_id(tier, resource_type)
                refined_base = get_refined_item_id(tier, resource_type)
                
                raw_item = get_enchanted_item_id(raw_base, enchant)
                refined_item = get_enchanted_item_id(refined_base, enchant)
                
                all_items.extend([raw_item, refined_item])
    
    # Fetch prices via API
    try:
        # Build URL for all items
        items_str = ','.join(all_items)
        url = f"{collector.base_url}/prices/{items_str}"
        
        response = collector.session.get(url, timeout=30)
        
        if response.status_code == 200:
            price_data = response.json()
            st.success(f"✅ Data fetched: {len(price_data)} entries")
            
            # Organize data by tier/enchant/city
            for item_data in price_data:
                item_id = item_data.get('item_id', '')
                city = item_data.get('city', '')
                quality = item_data.get('quality', 1)
                
                if quality != 1 or not city or not item_id:
                    continue
                
                # Determine tier, resource_type, enchant from item_id
                tier, resource_type, enchant, item_type = parse_item_id(item_id)
                
                if tier and tier in all_tiers_with_t3 and resource_type in selected_resources and item_type in ['raw', 'refined']:
                    all_data.append({
                        'tier': tier,
                        'resource_type': resource_type,
                        'enchant': enchant,
                        'city': city,
                        'type': item_type,
                        'item_id': item_id,
                        'buy_min': item_data.get('buy_price_min', 0),
                        'buy_max': item_data.get('buy_price_max', 0),
                        'sell_min': item_data.get('sell_price_min', 0),
                        'sell_max': item_data.get('sell_price_max', 0)
                    })
        
        else:
            st.error(f"API Error: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error fetching prices: {e}")
        return pd.DataFrame()
    
    return pd.DataFrame(all_data)

def parse_item_id(item_id: str):
    """Parse item_id to extract tier, resource_type, enchant and type."""
    try:
        # Separate enchantment
        if '@' in item_id:
            base_id, enchant_str = item_id.split('@')
            enchant = int(enchant_str)
        else:
            base_id = item_id
            enchant = 0
        
        # Determine tier
        tier = None
        for t in ALL_TIERS:
            if base_id.startswith(t):
                tier = t
                break
        
        # Determine resource_type and item_type
        resource_type = None
        item_type = None
        
        # Raw materials
        for res in ALL_RESOURCES:
            if f'_{res}' in base_id and not any(refined in base_id for refined in ['METALBAR', 'PLANKS', 'LEATHER', 'CLOTH', 'STONEBLOCK']):
                resource_type = res
                item_type = 'raw'
                break
        
        # Refined materials
        if item_type is None:
            if 'METALBAR' in base_id:
                resource_type = 'ORE'
                item_type = 'refined'
            elif 'PLANKS' in base_id:
                resource_type = 'WOOD'
                item_type = 'refined'
            elif 'LEATHER' in base_id:
                resource_type = 'HIDE'
                item_type = 'refined'
            elif 'CLOTH' in base_id:
                resource_type = 'FIBER'
                item_type = 'refined'
            elif 'STONEBLOCK' in base_id:
                resource_type = 'ROCK'
                item_type = 'refined'
        
        return tier, resource_type, enchant, item_type
        
    except:
        return None, None, None, None

def calculate_material_profitability(df: pd.DataFrame, region: str) -> pd.DataFrame:
    """Calculate profitability for all materials and enchantments."""
    calculator = RefiningCalculator()
    results = []
    
    # Load configuration to filter cities
    config = AlbionConfig.load_config()
    allowed_cities = config.get_allowed_cities()
    
    # Filter DataFrame by allowed cities
    df_filtered = df[df['city'].isin(allowed_cities)]
    
    # Previous tier mapping
    tier_mapping = {'T4': 'T3', 'T5': 'T4', 'T6': 'T5', 'T7': 'T6', 'T8': 'T7'}
    
    # Group by tier/resource_type/enchant/city
    for (tier, resource_type, enchant, city), group in df_filtered.groupby(['tier', 'resource_type', 'enchant', 'city']):
        # Skip T3 since we don't have T2 refined
        if tier == 'T3':
            continue
            
        raw_data = group[group['type'] == 'raw']
        refined_data = group[group['type'] == 'refined']
        
        if len(raw_data) > 0 and len(refined_data) > 0:
            raw_price = raw_data['sell_min'].iloc[0]  # Prix d'achat de raw
            refined_price = refined_data['sell_min'].iloc[0]  # Prix de vente de refined
            
            # Find the refined T-1 price to calculate profit
            previous_tier = tier_mapping.get(tier)
            if previous_tier:
                # Look for refined T-1 of same resource_type and enchant
                prev_refined = df_filtered[
                    (df_filtered['tier'] == previous_tier) & 
                    (df_filtered['resource_type'] == resource_type) &
                    (df_filtered['enchant'] == enchant) &
                    (df_filtered['type'] == 'refined') &
                    (df_filtered['city'] == city)
                ]
                
                if len(prev_refined) > 0:
                    prev_refined_price = prev_refined['buy_max'].iloc[0]  # Buy price
                    
                    # Normaliser le type de ressource pour le calculateur
                    resource_type_normalized = calculator.normalize_resource_type(resource_type)
                    
                    # Calculer avec différentes configs
                    for use_focus in [True, False]:
                        for specialization in [0, 50, 100]:
                            result = calculator.calculate_refining_profit(
                                tier=tier,
                                resource_type=resource_type_normalized,
                                city=city,
                                raw_price=raw_price,
                                refined_price=refined_price,
                                quantity=100,
                                specialization=specialization,
                                premium=True,
                                use_focus=use_focus,
                                prev_refined_price=prev_refined_price
                            )
                            
                            # Get the actual local production bonus for this city/resource
                            lpb = calculator.get_local_production_bonus(city, resource_type_normalized)
                            
                            results.append({
                                'tier': tier,
                                'resource_type': resource_type,
                                'enchant': enchant,
                                'city': city,
                                'material_name': get_enchanted_display_name(tier, resource_type, enchant),
                                'raw_price': raw_price,
                                'refined_price': refined_price,
                                'prev_refined_price': prev_refined_price,
                                'use_focus': use_focus,
                                'profit': result.net_profit,
                                'margin': result.profit_margin,
                                'return_rate': result.return_rate,
                                'specialization': specialization,
                                'tax_cost': result.tax_cost,
                                'focus_cost': result.focus_cost,
                                'output_value': result.output_value,
                                'input_cost': result.input_cost,
                                'lpb': lpb  # Add local production bonus
                            })
    
    return pd.DataFrame(results)

def main():
    st.title("Material Refining Analysis")
    
    # Simple explanation
    st.info("""
    ## 🤔 **What is Refining?**
    
    **The principle is simple:**
    1. 🛒 **BUY** raw materials (e.g. Raw Willow) 
    2. ⚒️ **REFINE** at a station (Lumbermill) = transform into finished product (Willow Planks)
    3. 💰 **SELL** the finished product for more than you paid for materials
    
    **Concrete example:** 
    - You buy 2 Raw Willow + 1 Birch Planks = 3,069 silver
    - You refine that into 1 Willow Planks  
    - You sell these Willow Planks = 12,294 silver
    - **PROFIT = 12,294 - 3,069 = 9,225 silver !** 🎉
    
    **The table below shows you the best profit opportunities.**
    """)
    
    st.markdown("---")
    
    # Simple description
    st.info("📖 **How it works?** This analysis compares the purchase cost of components (raw materials + previous material) with the selling price of the refined product to tell you where to make the most profit.")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Quick Configuration")
    
    region = st.sidebar.selectbox(
        "🌍 Region",
        ["Europe", "Americas", "Asia"],
        index=0
    )
    
    # Material selection
    selected_resources = st.sidebar.multiselect(
        "🎯 Materials to analyze",
        ALL_RESOURCES,
        default=['WOOD'],  # Start simple with just wood
        format_func=lambda x: f"{RESOURCE_ICONS[x]} {x.title()}"
    )
    
    if not selected_resources:
        st.warning("⚠️ Select at least one material in the sidebar to start the analysis")
        st.stop()
    
    # Data fetching
    if st.sidebar.button("🔄 Refresh data", type="primary"):
        st.cache_data.clear()
    
    with st.spinner("Loading market data..."):
        df = get_material_prices_all_enchants(region, selected_resources)
    
    if df.empty:
        st.error("No data available")
        return
    # Profitability calculation
    with st.spinner("Calculating best opportunities..."):
        results_df = calculate_material_profitability(df, region)
    
    if results_df.empty:
        st.error("😞 Unable to calculate profitability. Check that market data is available.")
        st.write("**DEBUG:** Input data for calculation:")
        st.write(df.head(10))
        st.stop()
    
    # Simplified filters
    st.sidebar.subheader("🎯 Quick Filters")
    
    use_focus = st.sidebar.checkbox(
        "🔍 Use Focus", 
        value=True,
        help="Enable to see profits with focus (recommended)"
    )
    
    specialization = st.sidebar.slider(
        "🏆 Specialization",
        0, 100, 50,
        help="Your refining specialization level"
    )
    
    min_profit = st.sidebar.number_input(
        "💰 Minimum profit (silver)",
        min_value=0,
        value=1000,
        step=500,
        help="Hide opportunities with less profit"
    )
    
    # Apply filters
    filtered_df = results_df[
        (results_df['use_focus'] == use_focus) &
        (results_df['specialization'] == specialization) &
        (results_df['profit'] >= min_profit) &
        (results_df['resource_type'].isin(selected_resources))
    ]
    
    if filtered_df.empty:
        st.warning("🚫 No profitable opportunities found with these filters. Try reducing the minimum profit or changing parameters.")
        st.stop()
    
    # TOP RECOMMENDATION
    st.header("🏆 BEST OPPORTUNITY")
    
    best_opportunity = filtered_df.loc[filtered_df['profit'].idxmax()]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Décomposer le nom pour extraire les infos
        tier = best_opportunity['tier']
        resource_type = best_opportunity['resource_type']
        enchant = best_opportunity['enchant']
        
        # Noms de matériaux
        raw_material = MATERIAL_NAMES[resource_type][tier]
        prev_tier = {'T4': 'T3', 'T5': 'T4', 'T6': 'T5', 'T7': 'T6', 'T8': 'T7'}[tier]
        prev_material = MATERIAL_NAMES[resource_type][prev_tier]
        
        # Nom du produit final
        refined_names = {
            'ORE': 'Lingots', 'WOOD': 'Planches', 'HIDE': 'Cuir', 
            'FIBER': 'Tissu', 'ROCK': 'Blocs'
        }
        final_product = f"{refined_names[resource_type]} de {raw_material}"
        if enchant > 0:
            final_product += f" .{enchant}"
        
        st.success(f"""
        ## 📋 PLAN D'ACTION DÉTAILLÉ
        
        ### 🛒 **ÉTAPE 1: ACHETER LES MATÉRIAUX**
        1. **{raw_material} brut** → {best_opportunity['raw_price']:,.0f} silver/unité
        2. **{refined_names[resource_type]} de {prev_material}** → {best_opportunity['prev_refined_price']:,.0f} silver/unité
        
        ### ⚒️ **ÉTAPE 2: RAFFINER À {best_opportunity['city']}**
        - Utiliser un **{['Fonderie', 'Scierie', 'Tannerie', 'Tisseranderie', 'Taillerie de Pierre'][['ORE', 'WOOD', 'HIDE', 'FIBER', 'ROCK'].index(resource_type)]}**
        - **BONUS:** {best_opportunity['city']} donne +{best_opportunity.get('lpb', 0)*100:.0f}% de bonus pour {['Minerai', 'Bois', 'Cuir', 'Fibre', 'Pierre'][['ORE', 'WOOD', 'HIDE', 'FIBER', 'ROCK'].index(resource_type)]}
        - Recette: **{['2', '3', '4', '5', '6'][['T4', 'T5', 'T6', 'T7', 'T8'].index(tier)]} {raw_material} + 1 {refined_names[resource_type]} de {prev_material} = 1 {final_product}**
        - Coût total par unité finale: **{best_opportunity['input_cost']:,.0f} silver**
        
        ### 💰 **ÉTAPE 3: REVENDRE LE PRODUIT FINI**
        - Vendre **{final_product}** → **{best_opportunity['refined_price']:,.0f} silver/unité**
        - 📍 Où vendre? Dans n'importe quelle ville avec de la demande (souvent les mêmes villes)
        
        ### 🎯 **RÉSUMÉ: {best_opportunity['profit']:,.0f} silver de PROFIT par unité finale**
        
        ---
        
        ### 💡 **EXEMPLE CONCRET POUR 10 UNITÉS:**
        - **Investissement:** {best_opportunity['input_cost']*10:,.0f} silver (acheter matériaux)
        - **Revenus:** {best_opportunity['refined_price']*10:,.0f} silver (vendre produit fini)  
        - **PROFIT NET:** {best_opportunity['profit']*10:,.0f} silver
        
        **⚡ Tu achètes les matériaux, tu raffines, tu revends = profit garanti!**
        """)
    
    with col2:
        st.metric("💰 Profit Net", f"{best_opportunity['profit']:,.0f}", delta="Meilleur choix")
        st.metric("📈 Marge", f"{best_opportunity['margin']:.1f}%")
        st.metric("🔄 Retour", f"{best_opportunity['return_rate']:.1f}%")
    
    if filtered_df.empty:
        st.warning("Aucune donnée correspondant aux filtres")
        return
    
    # TOP 10 SIMPLE
    st.header("📄 TOP 10 des Meilleures Opportunités")
    
    top_10 = filtered_df.nlargest(10, 'profit')
    
    # Tableau simple et clair avec explication des étapes
    st.info("💡 **Comment lire ce tableau:** Chaque ligne vous dit quoi acheter, où raffiner, et combien vous gagnerez.")
    
    display_data = []
    for _, row in top_10.iterrows():
        # Extraire les infos
        tier = row['tier']
        resource_type = row['resource_type']
        enchant = row['enchant']
        
        raw_material = MATERIAL_NAMES[resource_type][tier]
        prev_tier = {'T4': 'T3', 'T5': 'T4', 'T6': 'T5', 'T7': 'T6', 'T8': 'T7'}[tier]
        prev_material = MATERIAL_NAMES[resource_type][prev_tier]
        
        refined_names = {
            'ORE': 'Lingots', 'WOOD': 'Planches', 'HIDE': 'Cuir', 
            'FIBER': 'Tissu', 'ROCK': 'Blocs'
        }
        
        # Recette claire avec quantités correctes par tier
        raw_quantities = {'T4': 2, 'T5': 3, 'T6': 4, 'T7': 5, 'T8': 6}
        raw_qty = raw_quantities.get(tier, 2)
        recipe = f"{raw_qty} {raw_material} + 1 {refined_names[resource_type]} de {prev_material}"
        
        display_data.append({
            'Rang': len(display_data) + 1,
            '🛒 Acheter': recipe,
            '⚒️ Raffiner à': row['city'],
            '💰 Coût Total': f"{row['input_cost']:,.0f} silver",
            '💵 Revendre à': f"{row['refined_price']:,.0f} silver",
            '🎯 PROFIT': f"{row['profit']:,.0f} silver",
        })
    
    display_df = pd.DataFrame(display_data)
    
    # Colorier selon la rentabilité
    def color_profit(val):
        if 'PROFIT' in str(val):
            profit_val = float(val.replace(',', ''))
            if profit_val > 5000:
                return 'background-color: #90EE90'  # Vert clair
            elif profit_val > 2000:
                return 'background-color: #FFFFE0'  # Jaune clair
            else:
                return 'background-color: #FFE4E1'  # Rouge clair
        return ''
    
    st.dataframe(
        display_df.style.applymap(color_profit),
        use_container_width=True,
        hide_index=True
    )
    
    # GRAPHIQUE SIMPLE
    st.header("📈 Visualisation des Profits")
    
    fig = px.bar(
        top_10,
        x='material_name',
        y='profit',
        color='city',
        title="Comparaison des Profits par Matériau",
        labels={'profit': 'Profit Net (Silver)', 'material_name': 'Matériau'},
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(
        xaxis_tickangle=45,
        height=500,
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ANALYSE ENCHANTEMENTS
    st.header("💎 Rentabilité par Niveau d'Enchantement")
    
    enchant_summary = []
    for enchant in sorted(filtered_df['enchant'].unique()):
        enchant_data = filtered_df[filtered_df['enchant'] == enchant]
        if not enchant_data.empty:
            best_enchant = enchant_data.loc[enchant_data['profit'].idxmax()]
            enchant_summary.append({
                'Enchantement': f'.{enchant}' if enchant > 0 else 'Normal',
                'Meilleur Matériau': best_enchant['material_name'],
                'Profit Max': f"{best_enchant['profit']:,.0f}",
                'Profit Moyen': f"{enchant_data['profit'].mean():,.0f}"
            })
    
    enchant_df = pd.DataFrame(enchant_summary)
    st.dataframe(enchant_df, use_container_width=True, hide_index=True)
    
    # ANALYSE VILLES
    st.header("🏦️ Rentabilité par Ville")
    
    city_summary = []
    for city in sorted(filtered_df['city'].unique()):
        city_data = filtered_df[filtered_df['city'] == city]
        if not city_data.empty:
            best_city = city_data.loc[city_data['profit'].idxmax()]
            city_summary.append({
                'Ville': city,
                'Meilleur Matériau': best_city['material_name'],
                'Profit Max': f"{best_city['profit']:,.0f}",
                'Nombre d\'Opportunités': len(city_data)
            })
    
    city_df = pd.DataFrame(city_summary)
    st.dataframe(city_df, use_container_width=True, hide_index=True)
    
    # CONSEILS PRATIQUES
    st.header("💡 Conseils Pratiques")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **🔍 Pour maximiser vos profits:**
        
        1. **Surveillez les prix** - Les marchés fluctuent
        2. **Utilisez le focus** - Améliore le return rate
        3. **Spécialisez-vous** - Plus de spécialisation = plus de profit
        4. **Choisissez la bonne ville** - Bonus de production
        """)
    
    with col2:
        st.warning("""
        **⚠️ Points d'attention:**
        
        - Vérifiez les **stocks disponibles** avant d'investir
        - Les **taxes** varient selon les villes
        - Les prix changent rapidement - **actualisez régulièrement**
        - Considérez les **coûts de transport**
        """)
    
    # EXPORTATION
    if st.button("💾 Exporter les résultats (CSV)"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Télécharger le CSV",
            data=csv,
            file_name=f"analyse_raffinage_{region.lower()}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
