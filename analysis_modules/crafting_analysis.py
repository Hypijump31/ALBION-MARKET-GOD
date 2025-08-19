import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.crafting_calculator import CraftingCalculator
from src.data_collector import AlbionMarketData
from src.config import AlbionConfig
from src.price_manager import PriceManager
from src.session_manager import session_manager, save_session, load_session

def show_crafting_analysis():
    """Display the crafting profit analysis page."""
    st.title("Crafting Analysis")
    st.markdown("Calculate precise crafting profits with real Albion Online mechanics")
    
    # Load config
    if 'config' not in st.session_state:
        st.session_state.config = AlbionConfig.load_config()
    
    config = st.session_state.config
    calculator = CraftingCalculator()
    market_data = AlbionMarketData(region=config.server)
    price_manager = PriceManager(market_data)
    
    # Recipe selection with session persistence
    st.sidebar.markdown("**Crafting Recipe**")
    
    available_recipes = list(calculator.recipes.keys())
    default_recipe = load_session('selected_recipe', available_recipes[0])
    recipe_index = available_recipes.index(default_recipe) if default_recipe in available_recipes else 0
    
    selected_recipe = st.sidebar.selectbox(
        "Select recipe",
        available_recipes,
        index=recipe_index,
        key='recipe_select'
    )
    save_session('selected_recipe', selected_recipe)
    
    # City selection
    cities = ['Thetford', 'Fort Sterling', 'Lymhurst', 'Bridgewatch', 'Martlock', 'Caerleon', 'Brecilien']
    selected_city = st.sidebar.selectbox(
        "Crafting city",
        cities,
        index=cities.index(config.crafting_city) if config.crafting_city in cities else 0
    )
    
    # API confirmation option
    st.sidebar.subheader("API Settings")
    confirm_api = st.sidebar.checkbox("Confirm API requests", value=False, help="Show details before each request")
    
    # Quantity
    quantity = st.sidebar.number_input(
        "Quantity to produce",
        min_value=1,
        max_value=1000,
        value=1,
        step=1,
        help="Number of items to craft"
    )
    
    # Player configuration
    st.sidebar.subheader("Player Settings")
    
    specialization = st.sidebar.slider(
        "Specialization (%)",
        min_value=0,
        max_value=100,
        value=config.specialization_levels.get('CRAFTING', 0),
        step=1,
        help="Specialization level for this recipe"
    )
    
    premium = st.sidebar.checkbox(
        "Premium Account",
        value=config.premium,
        help="Enable premium bonuses"
    )
    
    use_focus = st.sidebar.checkbox(
        "Use Focus Points",
        value=config.use_focus,
        help="Significantly improves return rate"
    )
    
    # Get recipe info
    recipe_materials = calculator.get_recipe_materials(selected_recipe)
    recipe_category = calculator.get_recipe_category(selected_recipe)
    
    # Display recipe information
    st.header("Recipe Information")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Item", selected_recipe)
    with col2:
        st.metric("Category", recipe_category)
    with col3:
        tier = selected_recipe.split('_')[0]
        st.metric("Tier", tier)
    
    # Display materials required
    st.subheader("Required Materials")
    materials_df = pd.DataFrame([
        {"Material": material, "Quantity": amount}
        for material, amount in recipe_materials.items()
    ])
    st.dataframe(materials_df, use_container_width=True)
    
    # Price fetching section
    st.header("Material Prices")
    
    # Get material prices
    material_prices = {}
    
    if confirm_api:
        st.info("API confirmation mode enabled - Check details before each request")
    
    with st.spinner("Fetching material prices..."):
        material_items = list(recipe_materials.keys())
        
        try:
            # Fetch prices for all materials
            current_prices = market_data.get_current_prices(
                item_ids=material_items,
                locations=[selected_city],
                confirm_request=confirm_api
            )
            
            # Process prices
            for material in material_items:
                material_price = 100  # Default fallback
                
                if not current_prices.empty:
                    material_data = current_prices[
                        (current_prices['item_id'] == material) & 
                        (current_prices['city'] == selected_city)
                    ]
                    
                    if not material_data.empty and material_data.iloc[0]['sell_price_min'] > 0:
                        material_price = material_data.iloc[0]['sell_price_min']
                        st.success(f"✓ {material}: {material_price:,.0f} 🪙 (API)")
                    else:
                        st.warning(f"⚠️ Price {material} unavailable")
                        material_price = st.number_input(
                            f"Price {material} (manual)",
                            min_value=1,
                            value=100,
                            step=10,
                            key=f"price_{material}"
                        )
                else:
                    st.warning(f"⚠️ Price {material} unavailable")
                    material_price = st.number_input(
                        f"Price {material} (manual)",
                        min_value=1,
                        value=100,
                        step=10,
                        key=f"price_{material}"
                    )
                
                material_prices[material] = material_price
        
        except Exception as e:
            st.error(f"Error fetching prices: {e}")
            # Manual input fallback
            st.subheader("Manual Prices")
            for material in material_items:
                material_prices[material] = st.number_input(
                    f"Price {material}",
                    min_value=1,
                    value=100,
                    step=10,
                    key=f"manual_price_{material}"
                )
    
    # Get crafted item price
    st.subheader("Sale Price")
    
    with st.spinner("Fetching sale price..."):
        try:
            item_prices = market_data.get_current_prices(
                item_ids=[selected_recipe],
                locations=[selected_city],
                confirm_request=confirm_api
            )
            
            item_sell_price = 1000  # Default fallback
            
            if not item_prices.empty:
                item_data = item_prices[
                    (item_prices['item_id'] == selected_recipe) & 
                    (item_prices['city'] == selected_city)
                ]
                
                if not item_data.empty and item_data.iloc[0]['sell_price_min'] > 0:
                    item_sell_price = item_data.iloc[0]['sell_price_min']
                    st.success(f"✓ Sale price: {item_sell_price:,.0f} 🪙 (API)")
                else:
                    st.warning("⚠️ Sale price unavailable")
                    item_sell_price = st.number_input(
                        f"Sale price {selected_recipe} (manual)",
                        min_value=1,
                        value=1000,
                        step=50
                    )
            else:
                st.warning("⚠️ Sale price unavailable")
                item_sell_price = st.number_input(
                    f"Sale price {selected_recipe} (manual)",
                    min_value=1,
                    value=1000,
                    step=50
                )
        
        except Exception as e:
            st.error(f"Error fetching sale price: {e}")
            item_sell_price = st.number_input(
                f"Sale price {selected_recipe} (manual)",
                min_value=1,
                value=1000,
                step=50
            )
    
    # Calculate crafting profit
    st.header("Profitability Analysis")
    
    try:
        result = calculator.calculate_crafting_profit(
            item_id=selected_recipe,
            city=selected_city,
            material_prices=material_prices,
            item_sell_price=item_sell_price,
            quantity=quantity,
            specialization=specialization,
            premium=premium,
            use_focus=use_focus
        )
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            profit_color = "normal" if result.net_profit >= 0 else "inverse"
            st.metric("Net Profit", f"{result.net_profit:,.0f} 🪙", delta=None, delta_color=profit_color)
        with col2:
            st.metric("Profit Margin", f"{result.profit_margin:.1f}%")
        with col3:
            st.metric("Items Produced", f"{result.items_produced:.2f}")
        with col4:
            st.metric("Return Rate", f"{result.return_rate:.1%}")
        
        # Detailed breakdown
        st.subheader("Financial Details")
        
        breakdown_data = {
            "Element": [
                "Total Revenue",
                "Material Cost",
                "Crafting Taxes",
                "Gross Profit",
                "Net Profit"
            ],
            "Amount (🪙)": [
                f"{result.total_revenue:,.0f}",
                f"-{sum(result.material_costs.values()):,.0f}",
                f"-{result.tax_amount:,.0f}",
                f"{result.gross_profit:,.0f}",
                f"{result.net_profit:,.0f}"
            ]
        }
        
        breakdown_df = pd.DataFrame(breakdown_data)
        st.dataframe(breakdown_df, use_container_width=True)
        
        # Material cost breakdown
        st.subheader("Material Cost Breakdown")
        
        material_data = []
        for material, cost in result.material_costs.items():
            amount = recipe_materials[material] * quantity
            unit_price = material_prices[material]
            material_data.append({
                "Material": material,
                "Quantity": f"{amount:.0f}",
                "Unit Price": f"{unit_price:,.0f} 🪙",
                "Total Cost": f"{cost:,.0f} 🪙"
            })
        
        material_df = pd.DataFrame(material_data)
        st.dataframe(material_df, use_container_width=True)
        
        # Focus cost information
        if use_focus and result.focus_cost > 0:
            st.info(f"💫 Focus Points required: {result.focus_cost}")
        
        # Break-even analysis
        st.subheader("Break-even Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Break-even Price", f"{result.break_even_price:,.0f} 🪙")
        with col2:
            current_margin = ((item_sell_price - result.break_even_price) / item_sell_price * 100) if item_sell_price > 0 else 0
            st.metric("Safety Margin", f"{current_margin:.1f}%")
        
        if item_sell_price > result.break_even_price:
            st.success("✅ Sale price profitable")
        else:
            st.error("⚠️ Sale price too low!")
        
        # Visualization
        st.subheader("Visualization")
        
        # Profit breakdown pie chart
        fig_costs = go.Figure(data=[go.Pie(
            labels=['Materials', 'Taxes', 'Net Profit'],
            values=[sum(result.material_costs.values()), result.tax_amount, max(result.net_profit, 0)],
            hole=0.3
        )])
        fig_costs.update_traces(textposition='inside', textinfo='percent+label')
        fig_costs.update_layout(
            title="Cost and Profit Distribution",
            margin=dict(l=60, r=60, t=60, b=60),
            height=400
        )
        st.plotly_chart(fig_costs, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error calculating profitability: {e}")
        st.info("Check that all prices are available and the recipe is valid.")
    
    # City comparison section
    st.header("City Comparison")
    
    with st.expander("View city comparison"):
        with st.spinner("Analyzing cities..."):
            try:
                # Get prices for all cities
                all_material_prices = {}
                all_item_prices = {}
                
                for city in cities:
                    # Get material prices for this city
                    city_material_prices = market_data.get_current_prices(
                        item_ids=list(recipe_materials.keys()),
                        locations=[city],
                        confirm_request=False  # Disable confirmation for batch processing
                    )
                    
                    city_prices = {}
                    for material in recipe_materials.keys():
                        if not city_material_prices.empty:
                            material_data = city_material_prices[
                                (city_material_prices['item_id'] == material) & 
                                (city_material_prices['city'] == city)
                            ]
                            if not material_data.empty and material_data.iloc[0]['sell_price_min'] > 0:
                                city_prices[material] = material_data.iloc[0]['sell_price_min']
                            else:
                                city_prices[material] = material_prices.get(material, 100)
                        else:
                            city_prices[material] = material_prices.get(material, 100)
                    
                    all_material_prices[city] = city_prices
                    
                    # Get item price for this city
                    city_item_prices = market_data.get_current_prices(
                        item_ids=[selected_recipe],
                        locations=[city],
                        confirm_request=False
                    )
                    
                    if not city_item_prices.empty:
                        item_data = city_item_prices[
                            (city_item_prices['item_id'] == selected_recipe) & 
                            (city_item_prices['city'] == city)
                        ]
                        if not item_data.empty and item_data.iloc[0]['sell_price_min'] > 0:
                            all_item_prices[city] = item_data.iloc[0]['sell_price_min']
                        else:
                            all_item_prices[city] = item_sell_price
                    else:
                        all_item_prices[city] = item_sell_price
                
                # Calculate profits for all cities
                city_results = calculator.find_best_crafting_city(
                    item_id=selected_recipe,
                    material_prices_by_city=all_material_prices,
                    item_sell_prices_by_city=all_item_prices,
                    quantity=quantity,
                    specialization=specialization,
                    premium=premium,
                    use_focus=use_focus
                )
                
                if city_results:
                    comparison_data = []
                    for city, result in city_results.items():
                        comparison_data.append({
                            "City": city,
                            "Net Profit": f"{result.net_profit:,.0f} 🪙",
                            "Margin (%)": f"{result.profit_margin:.1f}%",
                            "Return Rate": f"{result.return_rate:.1%}",
                            "Taxes": f"{result.tax_amount:,.0f} 🪙"
                        })
                    
                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df, use_container_width=True)
                else:
                    st.warning("Unable to compare cities - insufficient prices")
                    
            except Exception as e:
                st.error(f"Error during city comparison: {e}")

if __name__ == "__main__":
    show_crafting_analysis()
