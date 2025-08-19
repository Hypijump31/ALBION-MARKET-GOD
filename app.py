import streamlit as st
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collector import AlbionMarketData
from src.analyzer import MarketAnalyzer
from src.visualization import create_price_chart, create_market_heatmap
from src.config import AlbionConfig
from src.performance_optimizer import PerformanceOptimizer
from src.session_manager import session_manager, save_session, load_session
import pandas as pd

import logging

def main():
    # Configure logging to ensure all debug messages are captured
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout  # Ensure logs go to stdout for Streamlit
    )

    st.set_page_config(
        page_title="Albion Market Analyzer", 
        layout="wide",
        page_icon="⚔️",
        initial_sidebar_state="expanded"
    )
    
    # Initialize configuration
    if 'config' not in st.session_state:
        st.session_state.config = AlbionConfig.load_config()
    
    config = st.session_state.config
    
    # Simple navigation
    st.sidebar.title("📊 Albion Market Analyzer")
    pages = ["Configuration", "Refining Analysis", "Crafting Analysis", "Material Analysis"]
    page_labels = ["⚙️ Configuration", "🔥 Refining Analysis", "🔨 Crafting Analysis", "💎 Material Analysis"]
    default_page = load_session('current_page', pages[0])
    page_index = pages.index(default_page) if default_page in pages else 0
    
    page = st.sidebar.radio(
        "Select Analysis",
        options=pages,
        format_func=lambda x: page_labels[pages.index(x)],
        index=page_index,
        key='page_selector'
    )
    save_session('current_page', page)
    
    if page == "Configuration":
        show_config_page()
    elif page == "Refining Analysis":
        show_refining_page()
    elif page == "Crafting Analysis":
        show_crafting_page()
    elif page == "Material Analysis":
        show_material_page()
    else:
        show_config_page()  # Default to config

def show_config_page():
    """Display the configuration page."""
    from analysis_modules.config import show_config_page as config_page
    config_page()

def show_refining_page():
    """Display the refining analysis page."""
    from analysis_modules.refining_analysis import show_refining_analysis
    show_refining_analysis()

def show_crafting_page():
    """Display the crafting analysis page."""
    from analysis_modules.crafting_analysis import show_crafting_analysis
    show_crafting_analysis()

def show_material_page():
    """Display the material analysis page."""
    from analysis_modules.material_analysis import main as material_main
    material_main()


if __name__ == "__main__":
    main()
