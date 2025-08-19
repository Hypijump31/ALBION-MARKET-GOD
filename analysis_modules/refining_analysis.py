import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.refining_calculator import RefiningCalculator
from src.data_collector import AlbionMarketData
from src.config import AlbionConfig
from src.item_mapping import AVAILABLE_TIERS, AVAILABLE_RESOURCES, get_display_name, get_refined_item_id, get_raw_item_id
from src.price_manager import PriceManager
from src.session_manager import session_manager, save_session, load_session
from src.api_monitor import api_monitor
# arbitrage_analyzer will be created with config in the analysis section
from src.action_planner import action_planner

def show_refining_analysis():
    """Display the refining profit analysis page."""
    st.title("Refining Analysis")
    st.markdown("Calculate precise refining profits with real Albion Online mechanics")
    
    # Load config
    if 'config' not in st.session_state:
        st.session_state.config = AlbionConfig.load_config()
    
    config = st.session_state.config
    calculator = RefiningCalculator()
    market_data = AlbionMarketData(region=config.server)
    price_manager = PriceManager(market_data)
    
    # Sidebar configuration
    # Resource selection with session persistence
    st.sidebar.markdown("**Resource Selection**")
    
    # Resource selection
    tier = st.sidebar.selectbox(
        "Tier",
        AVAILABLE_TIERS,
        index=AVAILABLE_TIERS.index(load_session('tier', 'T4')),
        key='tier_select'
    )
    save_session('tier', tier)
    
    resource_type = st.sidebar.selectbox(
        "Resource Type", 
        AVAILABLE_RESOURCES,
        index=AVAILABLE_RESOURCES.index(load_session('resource_type', 'WOOD')),
        key='resource_select'
    )
    save_session('resource_type', resource_type)
    
    # Enchantment selection
    enchantment = st.sidebar.selectbox(
        "Enchantment",
        ["0 (Normal)", "1 (.1)", "2 (.2)", "3 (.3)", "4 (.4)"],
        index=0,
        key='enchantment_select'
    )
    enchant_level = int(enchantment[0])  # Extract number
    
    # City selection with optimal recommendation
    cities = list(calculator.data['local_production_bonus'].keys())
    optimal_city = calculator.get_optimal_refining_city(resource_type)
    
    # Show optimal recommendation
    st.sidebar.markdown("### 🏆 Optimal City")
    optimal_bonus = calculator.get_local_production_bonus(optimal_city, resource_type)
    st.sidebar.success(f"**{optimal_city}** (+{optimal_bonus*100:.0f}% bonus for {resource_type})")
    
    # The application will now automatically use the optimal city.
    selected_city = optimal_city
    save_session('selected_city', selected_city) # Keep saving for potential future use or consistency
    
    # API confirmation is no longer a user option and is defaulted to False.
    confirm_api = False
    
    # Analysis parameters
    st.sidebar.markdown("**Analysis Parameters**")

    # Initialize session state for budget and quantity if they don't exist
    if 'refining_quantity' not in st.session_state:
        st.session_state.refining_quantity = 1000
    if 'refining_budget' not in st.session_state:
        st.session_state.refining_budget = 100000.0
    if 'last_refining_input' not in st.session_state:
        st.session_state.last_refining_input = 'quantity'

    def budget_updated():
        st.session_state.last_refining_input = 'budget'

    def quantity_updated():
        st.session_state.last_refining_input = 'quantity'

    st.sidebar.number_input(
        "Quantity to refine",
        min_value=10,
        max_value=10000,
        key='refining_quantity',
        step=100,
        on_change=quantity_updated
    )

    st.sidebar.number_input(
        "Amount to spend",
        min_value=1000.0,
        max_value=10000000.0,
        key='refining_budget',
        step=1000.0,
        on_change=budget_updated,
        format="%.2f"
    )
    
    
    # Player settings
    st.sidebar.markdown("**Player Settings**")
    specialization = st.sidebar.slider(
        "Specialization (%)",
        min_value=0,
        max_value=100,
        value=load_session('specialization', config.get_specialization_level(resource_type.lower() + '_refining')),
        step=1,
        key='spec_slider'
    )
    save_session('specialization', specialization)

    premium = st.sidebar.checkbox("Premium", value=config.premium, key='premium_checkbox')
    use_focus = st.sidebar.checkbox("Use Focus", value=config.use_focus, key='focus_checkbox')
    
    st.markdown("---")

    # Analyze market opportunities
    with st.spinner("Analyzing market opportunities..."):
        # Get prices from allowed cities only (respects exclusion filters)
        allowed_cities = config.get_allowed_cities()
        all_price_data = market_data.get_refining_prices(tier, resource_type, enchantment=enchant_level, locations=allowed_cities, confirm_request=confirm_api)
        
        # Initialize arbitrage analyzer with config to respect city exclusions
        from src.arbitrage_analyzer import ArbitrageAnalyzer
        config_aware_arbitrage_analyzer = ArbitrageAnalyzer(config=config, calculator=calculator)
        
        # Analyze arbitrage opportunities
        arbitrage_analysis = config_aware_arbitrage_analyzer.analyze_opportunities(all_price_data, tier, resource_type)
        
        # Display arbitrage recommendations
        config_aware_arbitrage_analyzer.display_recommendations(arbitrage_analysis, tier, resource_type)
    
    # Synchronize quantity and budget
    raw_item_id = get_raw_item_id(tier, resource_type, enchant_level)
    raw_price_data = all_price_data.get(raw_item_id, {})
    raw_buy_price = raw_price_data.get('buy_price', 0)

    if raw_buy_price > 0:
        if st.session_state.last_refining_input == 'budget':
            st.session_state.refining_quantity = int(st.session_state.refining_budget // raw_buy_price)
        elif st.session_state.last_refining_input == 'quantity':
            st.session_state.refining_budget = st.session_state.refining_quantity * raw_buy_price

    quantity = st.session_state.refining_quantity

    # CREATE AND DISPLAY CONCRETE ACTION PLAN
    st.header("Action Plan")

    # Check if we have valid arbitrage data before creating a plan
    raw_buy_price = arbitrage_analysis.get('raw_recommendations', {}).get('buy_recommendation', {}).get('price', 0)
    refined_sell_price = arbitrage_analysis.get('refined_recommendations', {}).get('sell_recommendation', {}).get('price', 0)
    prev_refined_buy_price = arbitrage_analysis.get('prev_refined_recommendations', {}).get('buy_recommendation', {}).get('price', 0)

    if not all([raw_buy_price, refined_sell_price, prev_refined_buy_price]):
        missing_items = []
        if not raw_buy_price:
            raw_item_id = get_raw_item_id(tier, resource_type, enchant_level)
            missing_items.append(f"Matière première ({raw_item_id})")
        if not prev_refined_buy_price:
            tier_num = int(tier[1:])
            prev_tier = f"T{tier_num - 1}"
            prev_refined_id = get_refined_item_id(prev_tier, resource_type, enchant_level)
            missing_items.append(f"Ressource raffinée T-1 ({get_display_name(prev_refined_id)})")
        if not refined_sell_price:
            refined_id = get_refined_item_id(tier, resource_type, enchant_level)
            missing_items.append(f"Ressource raffinée finale ({get_display_name(refined_id)})")
        
        st.error(f"❌ DONNÉES INSUFFISANTES: Prix manquants pour: {', '.join(missing_items)}.")
        st.warning("Vérifiez que tous les composants sont disponibles sur le marché dans les villes sélectionnées.")
    else:
        # Calculate refining profit for the plan using optimal city
        profit_data = calculator.calculate_refining_profit(
            tier=tier,
            resource_type=resource_type,
            city=optimal_city,  # Use optimal city for calculations
            raw_price=raw_buy_price,
            refined_price=refined_sell_price,
            quantity=quantity,
            specialization=specialization,
            premium=premium, # Use value from checkbox
            use_focus=use_focus, # Use value from checkbox
            prev_refined_price=prev_refined_buy_price
        )
        
        # Create action plan using optimal city for both calculation and display
        action_plan = action_planner.create_refining_action_plan(
            arbitrage_analysis=arbitrage_analysis,
            tier=tier,
            resource_type=resource_type,
            quantity=quantity,
            profit_data=profit_data,
            selected_city=optimal_city  # Always use optimal city for the plan
        )
        
        # Display action plan
        action_planner.display_action_plan(action_plan)
    
    # Use prices from arbitrage analysis for consistency in the main analysis section
    # This ensures the main breakdown uses the same data as the action plan
    raw_price = arbitrage_analysis.get('raw_recommendations', {}).get('buy_recommendation', {}).get('price', 0)
    refined_price = arbitrage_analysis.get('refined_recommendations', {}).get('sell_recommendation', {}).get('price', 0)
    prev_refined_price = arbitrage_analysis.get('prev_refined_recommendations', {}).get('buy_recommendation', {}).get('price', 0)
    
    
    
    # Main analysis
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header(f"Analysis: {tier} {resource_type}")
        
        # Calculate profit for selected city, now including previous refined price
        result = calculator.calculate_refining_profit(
            tier=tier,
            resource_type=resource_type,
            city=optimal_city,
            raw_price=raw_price,
            refined_price=refined_price,
            quantity=quantity,
            specialization=specialization,
            premium=premium,
            use_focus=use_focus,
            prev_refined_price=prev_refined_price
        )
        
        # Display key metrics
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            profit_color = "normal" if result.net_profit >= 0 else "inverse"
            st.metric(
                "Net Profit",
                f"{result.net_profit:,.0f} 🪙",
                delta=None,
                delta_color=profit_color
            )
        
        with col_b:
            st.metric(
                "Margin",
                f"{result.profit_margin:.1f}%"
            )
        
        with col_c:
            st.metric(
                "Return Rate",
                f"{result.return_rate*100:.1f}%"
            )
        
        with col_d:
            st.metric(
                "Focus Required",
                f"{result.focus_cost:,}"
            )
        
        # Detailed breakdown
        st.subheader("Financial Breakdown")
        
        breakdown_data = {
            'Category': ['Purchase Cost', 'Refined Sales', 'Return Sales', 'Taxes', 'Net Profit'],
            'Amount': [
                -result.input_cost,
                (quantity // calculator.data['resource_requirements'].get(tier, {'raw': 2})['raw']) * refined_price,
                result.resources_returned * raw_price,
                -result.tax_cost,
                result.net_profit
            ],
            'Type': ['Cost', 'Revenue', 'Revenue', 'Cost', 'Result']
        }
        
        breakdown_df = pd.DataFrame(breakdown_data)
        
        # Create bar chart with optimized scale
        resource_req = calculator.data['resource_requirements'].get(tier, {'raw': 2})
        expected_output = quantity // resource_req['raw']
        fig = px.bar(
            x=["Purchase Price", "Taxes", "Sales Price", "Profit"],
            y=[result.input_cost, result.tax_cost, expected_output * refined_price, result.net_profit],
            color=["Purchase Price", "Taxes", "Sales Price", "Profit"],
            title="Refining Financial Analysis",
            labels={'x': 'Components', 'y': 'Amount (Silver)'},
            height=400
        )
        
        # Optimize chart layout
        fig.update_layout(
            xaxis={'range': [-0.7, 3.7]},
            yaxis={'autorange': True},
            margin=dict(l=60, r=60, t=60, b=60),
            bargap=0.4
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Detailed Calculation Breakdown
        with st.expander("🔍 Show Calculation Breakdown"):
            st.markdown("#### Inputs")
            c1, c2, c3 = st.columns(3)
            c1.metric("Raw Material Price", f"{raw_price:,.0f}")
            c2.metric("Refined Material Price", f"{refined_price:,.0f}")
            c3.metric("T-1 Refined Price", f"{prev_refined_price:,.0f}")
            c1.metric("Quantity to Refine", f"{quantity:,}")
            c2.metric("Specialization", f"{specialization}%")

            st.markdown("#### Bonuses & Rates")
            c1, c2, c3 = st.columns(3)
            city_bonus = calculator.get_local_production_bonus(optimal_city, resource_type)
            c1.metric("City Bonus", f"{city_bonus*100:.0f}%")
            c2.metric("Premium Status", "✅ Active" if premium else "❌ Inactive")
            c3.metric("Focus Used", "✅ Yes" if use_focus else "❌ No")
            c1.metric("Return Rate (RRR)", f"{result.return_rate*100:.2f}%")
            c2.metric("Resources Returned", f"{result.resources_returned:,.2f}")

            st.markdown("#### Costs")
            c1, c2 = st.columns(2)
            c1.metric("Total Input Cost", f"{result.input_cost:,.0f} 🪙")
            c2.metric("Tax Cost", f"{result.tax_cost:,.0f} 🪙")
            c1.metric("Focus Point Cost", f"{result.focus_cost:,.0f}")

            st.markdown("#### Final Calculation")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Revenue", f"{result.total_revenue:,.0f} 🪙")
            c2.metric("Net Profit", f"{result.net_profit:,.0f} 🪙", delta_color="off")
            c3.metric("Profit Margin", f"{result.profit_margin:.2f}%")
    
    with col2:
        st.subheader("Detailed Information")
        
        # Local production bonus info
        lpb = calculator.data['local_production_bonus'].get(optimal_city, {}).get(resource_type, 0)
        st.info(f"**Local Bonus:** {lpb*100:.0f}%")
        
        # Tax rate
        tax_rate = calculator.data['tax_rates'].get(optimal_city, 0.05)
        st.info(f"**Tax Rate:** {tax_rate*100:.1f}%")
        
        # Resource requirements
        req = calculator.data['resource_requirements'].get(tier, {'raw': 2})
        st.info(f"**Ratio:** {req['raw']} raw + {req.get('refined_prev', 1)} prev refined → 1 + returns")
        
        # Resources returned
        st.info(f"**Returns:** {result.resources_returned} units")
        
        # Break-even price
        break_even = calculator.calculate_break_even_price(
            tier, resource_type, optimal_city, refined_price,
            specialization, premium, use_focus
        )
        st.warning(f"**Break-even Price:** {break_even:.0f} 🪙")
        
        if raw_price > break_even:
            st.error("⚠️ Purchase price too high!")
        else:
            st.success("✅ Purchase price profitable")
    
    # City comparison with real API prices
    st.header("City Comparison (API Prices)")
    
    with st.spinner("Fetching prices for all cities..."):
        # Use the price manager to get prices for all cities
        all_city_prices = price_manager.get_refining_prices_cached(tier, resource_type, enchant_level, cities)
        
        city_results = {}
        for city in cities:
            # Use API prices if available, otherwise fallback to current prices
            city_raw_price = raw_price
            city_refined_price = refined_price
            
            if all_city_prices and city in all_city_prices:
                city_data = all_city_prices[city]
                if 'raw' in city_data and city_data['raw']['sell_min'] > 0:
                    city_raw_price = city_data['raw']['sell_min']
                if 'refined' in city_data and city_data['refined']['sell_min'] > 0:
                    city_refined_price = city_data['refined']['sell_min']
            
            # Calculate profit for this city
            result = calculator.calculate_refining_profit(
                tier=tier,
                resource_type=resource_type,
                city=city,
                raw_price=city_raw_price,
                refined_price=city_refined_price,
                quantity=100,  # Standard quantity for comparison
                specialization=specialization,
                premium=premium,
                use_focus=use_focus
            )
            
            city_results[city] = {
                'profit': result.net_profit,
                'margin': result.profit_margin,
                'return_rate': result.return_rate,
                'tax_rate': calculator.data['tax_rates'].get(city, 0.05),
                'lpb': calculator.data['local_production_bonus'].get(city, {}).get(resource_type, 0.0),
                'raw_price': city_raw_price,
                'refined_price': city_refined_price,
                'full_result': result
            }
        
        # Sort by profit
        city_results = dict(sorted(city_results.items(), key=lambda x: x[1]['profit'], reverse=True))
    
    # Create comparison DataFrame
    comparison_data = []
    for city, data in city_results.items():
        comparison_data.append({
            'City': city,
            'Profit': data['profit'],
            'Margin (%)': data['margin'],
            'Return Rate (%)': data['return_rate'] * 100,
            'Local Bonus (%)': data['lpb'] * 100,
            'Tax (%)': data['tax_rate'] * 100,
            'Raw Price': data['raw_price'],
            'Refined Price': data['refined_price']
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Profit comparison chart
    fig_comparison = px.bar(
        comparison_df,
        x='City',
        y='Profit',
        color='Profit',
        color_continuous_scale=['red', 'yellow', 'green'],
        title=f"Profit by City - {tier} {resource_type}",
        labels={'Profit': 'Profit (silver)'}
    )
    
    fig_comparison.update_layout(
        height=400,
        margin=dict(l=60, r=60, t=60, b=60),
        bargap=0.3
    )
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Detailed comparison table
    st.subheader("Detailed Comparison Table")
    
    # Style the dataframe
    def style_profit(val):
        color = 'color: green' if val > 0 else 'color: red'
        return color
    
    styled_df = comparison_df.style.map(style_profit, subset=['Profit'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Advanced analysis
    with st.expander("Advanced Analysis"):
        col_adv1, col_adv2 = st.columns(2)
        
        with col_adv1:
            st.subheader("Price Sensitivity")
            
            # Price sensitivity analysis
            price_range = st.slider(
                "Price variation (%)",
                min_value=-50,
                max_value=50,
                value=(-20, 20),
                step=5
            )
            
            sensitivity_results = []
            
            for price_change in range(price_range[0], price_range[1]+1, 5):
                adjusted_raw_price = raw_price * (1 + price_change/100)
                
                sens_result = calculator.calculate_refining_profit(
                    tier=tier,
                    resource_type=resource_type,
                    city=optimal_city,
                    raw_price=adjusted_raw_price,
                    refined_price=refined_price,
                    quantity=quantity,
                    specialization=specialization,
                    premium=premium,
                    use_focus=use_focus
                )
                
                sensitivity_results.append({
                    'Price Variation (%)': price_change,
                    'Adjusted Price': adjusted_raw_price,
                    'Profit': sens_result.net_profit,
                    'Margin (%)': sens_result.profit_margin
                })
            
            sens_df = pd.DataFrame(sensitivity_results)
            
            fig_sensitivity = px.line(
                sens_df,
                x='Price Variation (%)',
                y='Profit',
                title="Price Variation Impact on Profit",
                markers=True
            )
            
            fig_sensitivity.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Break-even")
            fig_sensitivity.update_layout(
                margin=dict(l=60, r=60, t=60, b=60),
                height=400
            )
            st.plotly_chart(fig_sensitivity, use_container_width=True)
        
        with col_adv2:
            st.subheader("Arbitrage Opportunities")
            
            # Get arbitrage opportunities
            arbitrage_ops = price_manager.get_arbitrage_opportunities(tier, resource_type, enchant_level)
            
            if arbitrage_ops:
                for i, op in enumerate(arbitrage_ops):
                    st.success(f"""
                    **Opportunity #{i+1}**
                    - Buy at {op['buy_city']}: {op['buy_price']:,.0f} 🪙
                    - Sell at {op['sell_city']}: {op['sell_price']:,.0f} 🪙
                    - Profit: {op['profit_per_unit']:,.0f} 🪙 ({op['profit_margin']:.1f}%)
                    """)
            else:
                st.info("No arbitrage opportunities detected")
            
            # Show current market spread
            st.subheader("Current Price Spreads")
            
            if all_city_prices:
                raw_prices = []
                refined_prices = []
                city_names = []
                
                for city, data in all_city_prices.items():
                    if 'raw' in data and data['raw']['sell_min'] > 0:
                        raw_prices.append(data['raw']['sell_min'])
                        city_names.append(city)
                    if 'refined' in data and data['refined']['sell_min'] > 0:
                        refined_prices.append(data['refined']['sell_min'])
                
                if raw_prices:
                    min_raw = min(raw_prices)
                    max_raw = max(raw_prices)
                    st.metric("Raw Resource Spread", f"{max_raw - min_raw:,.0f} 🪙", 
                            f"{((max_raw - min_raw) / min_raw * 100):.1f}%")
                
                if refined_prices:
                    min_refined = min(refined_prices)
                    max_refined = max(refined_prices)
                    st.metric("Refined Resource Spread", f"{max_refined - min_refined:,.0f} 🪙",
                            f"{((max_refined - min_refined) / min_refined * 100):.1f}%")

if __name__ == "__main__":
    show_refining_analysis()
