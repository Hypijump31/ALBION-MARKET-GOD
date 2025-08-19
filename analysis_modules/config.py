import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.config import AlbionConfig, FOOD_BUFFS, QUALITY_MULTIPLIERS

def show_config_page():
    st.title("⚙️ Configuration Albion Online")
    st.markdown("Configurez vos paramètres de jeu pour des calculs précis de rentabilité")
    
    # Load existing config
    if 'config' not in st.session_state:
        st.session_state.config = AlbionConfig.load_config()
    
    config = st.session_state.config
    
    # Create tabs for different configuration sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌍 Serveur & Compte", 
        "🔨 Craft & Raffinage", 
        "📊 Spécialisations", 
        "🍖 Buffs & Équipements", 
        "💰 Économie"
    ])
    
    with tab1:
        st.header("Configuration Serveur & Compte")
        
        col1, col2 = st.columns(2)
        
        with col1:
            config.server = st.selectbox(
                "Serveur de jeu",
                ['Europe', 'Americas', 'Asia'],
                index=['Europe', 'Americas', 'Asia'].index(config.server),
                help="Choisissez votre serveur pour accéder aux bonnes données de marché"
            )
            
            config.premium = st.checkbox(
                "Premium actif",
                value=config.premium,
                help="Le premium donne +50% de Fame et +5% de return rate"
            )
        
        with col2:
            config.focus_points = st.number_input(
                "Points de focalisation disponibles",
                min_value=0,
                max_value=30000,
                value=config.focus_points,
                step=1000,
                help="Vos points de focus actuels (max 30,000 avec premium)"
            )
            
            config.use_focus = st.checkbox(
                "Utiliser la focalisation",
                value=config.use_focus,
                help="Activer l'utilisation de focus pour améliorer les return rates"
            )
    
    with tab2:
        st.header("Configuration Craft & Raffinage")
        
        col1, col2 = st.columns(2)
        
        with col1:
            config.crafting_city = st.selectbox(
                "Ville de craft principale",
                list(config.tax_rates.keys()),
                index=list(config.tax_rates.keys()).index(config.crafting_city),
                help="Votre ville principale pour le crafting (affecte les taxes)"
            )
            
            config.base_return_rate = st.slider(
                "Return rate de base (%)",
                min_value=10.0,
                max_value=50.0,
                value=config.base_return_rate * 100,
                step=0.1,
                help="Return rate de base (15.2% par défaut)"
            ) / 100
        
        with col2:
            config.use_quality_items = st.checkbox(
                "Utiliser des ressources de qualité",
                value=config.use_quality_items,
                help="Activer si vous craftez avec des ressources enchantées"
            )
            
            if config.use_quality_items:
                config.preferred_quality = st.selectbox(
                    "Qualité préférée",
                    list(QUALITY_MULTIPLIERS.keys()),
                    help="Qualité des ressources que vous utilisez habituellement"
                )
            
            config.use_journals = st.checkbox(
                "Utiliser les journaux",
                value=config.use_journals,
                help="Activer si vous utilisez des journaux de craft"
            )
            
            if config.use_journals:
                config.journal_efficiency = st.slider(
                    "Efficacité des journaux (%)",
                    min_value=50,
                    max_value=100,
                    value=int(config.journal_efficiency * 100),
                    help="Efficacité avec laquelle vous remplissez vos journaux"
                ) / 100
    
    with tab3:
        st.header("Niveaux de Spécialisation")
        st.markdown("Configurez vos niveaux de spécialisation pour des calculs précis")
        
        # Refining specializations
        st.subheader("🔥 Raffinage")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            config.specializations['ore_refining'] = st.slider(
                "Smelter", 0, 100, config.specializations.get('ore_refining', 0)
            )
            config.specializations['wood_refining'] = st.slider(
                "Lumberjack", 0, 100, config.specializations.get('wood_refining', 0)
            )
        
        with col2:
            config.specializations['hide_refining'] = st.slider(
                "Tanner", 0, 100, config.specializations.get('hide_refining', 0)
            )
            config.specializations['stone_refining'] = st.slider(
                "Quarrier", 0, 100, config.specializations.get('stone_refining', 0)
            )
        
        with col3:
            config.specializations['fiber_refining'] = st.slider(
                "Weaver", 0, 100, config.specializations.get('fiber_refining', 0)
            )
        
        # Crafting specializations
        st.subheader("🔨 Craft")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            config.specializations['weapon_smith'] = st.slider(
                "Warrior", 0, 100, config.specializations.get('weapon_smith', 0)
            )
            config.specializations['hunter'] = st.slider(
                "Hunter", 0, 100, config.specializations.get('hunter', 0)
            )
        
        with col2:
            config.specializations['armor_smith'] = st.slider(
                "Armorer", 0, 100, config.specializations.get('armor_smith', 0)
            )
            config.specializations['miner'] = st.slider(
                "Miner", 0, 100, config.specializations.get('miner', 0)
            )
        
        with col3:
            config.specializations['toolmaker'] = st.slider(
                "Toolmaker", 0, 100, config.specializations.get('toolmaker', 0)
            )
            config.specializations['fisher'] = st.slider(
                "Fisher", 0, 100, config.specializations.get('fisher', 0)
            )
        
        with col4:
            config.specializations['cook'] = st.slider(
                "Cook", 0, 100, config.specializations.get('cook', 0)
            )
            config.specializations['alchemist'] = st.slider(
                "Alchemist", 0, 100, config.specializations.get('alchemist', 0)
            )
    
    with tab4:
        st.header("Buffs & Équipements")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🍖 Nourriture")
            food_options = list(FOOD_BUFFS.keys())
            food_names = [FOOD_BUFFS[key]['name'] for key in food_options]
            
            selected_food_index = st.selectbox(
                "Buff de nourriture actuel",
                range(len(food_names)),
                format_func=lambda x: food_names[x],
                help="Sélectionnez la nourriture que vous utilisez"
            )
            
            selected_food = food_options[selected_food_index]
            config.food_bonus = FOOD_BUFFS[selected_food]['return_bonus']
            
            if selected_food != 'none':
                st.info(f"Return bonus: +{config.food_bonus*100:.1f}%")
        
        with col2:
            st.subheader("⚔️ Équipements")
            config.equipment_return_bonus = st.slider(
                "Bonus return rate équipement (%)",
                min_value=0.0,
                max_value=10.0,
                value=config.equipment_return_bonus * 100,
                step=0.1,
                help="Bonus de return rate de votre équipement de craft"
            ) / 100
            
            config.equipment_focus_reduction = st.slider(
                "Réduction coût focus équipement (%)",
                min_value=0.0,
                max_value=50.0,
                value=config.equipment_focus_reduction * 100,
                step=1.0,
                help="Réduction du coût en focus grâce à votre équipement"
            ) / 100
    
    with tab5:
        st.header("Configuration Économique")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💸 Taxes par ville")
            for city in config.tax_rates.keys():
                config.tax_rates[city] = st.slider(
                    f"Taxe {city} (%)",
                    min_value=0.0,
                    max_value=10.0,
                    value=config.tax_rates[city] * 100,
                    step=0.1
                ) / 100
        
        with col2:
            st.subheader("📈 Paramètres de profit")
            config.profit_margin_threshold = st.slider(
                "Marge de profit minimale (%)",
                min_value=0.0,
                max_value=50.0,
                value=config.profit_margin_threshold * 100,
                step=1.0,
                help="Marge de profit minimale pour considérer une activité rentable"
            ) / 100
            
            config.calculate_transportation_costs = st.checkbox(
                "Calculer les coûts de transport",
                value=config.calculate_transportation_costs,
                help="Inclure les coûts de transport dans les calculs"
            )
            
            st.subheader("🏛️ Filtrage des villes")
            
            # Créer les attributs s'ils n'existent pas
            if not hasattr(config, 'exclude_brecilien'):
                config.exclude_brecilien = False
            if not hasattr(config, 'exclude_caerleon'):
                config.exclude_caerleon = False
            
            config.exclude_brecilien = st.checkbox(
                "Exclure Brecilien des analyses",
                value=config.exclude_brecilien,
                help="Exclure Brecilien des statistiques et calculs de rentabilité"
            )
            
            config.exclude_caerleon = st.checkbox(
                "Exclure Caerleon des analyses", 
                value=config.exclude_caerleon,
                help="Exclure Caerleon des statistiques et calculs de rentabilité"
            )
    
    # Save configuration
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("💾 Sauvegarder Configuration", type="primary", use_container_width=True):
            config.save_config()
            st.success("Configuration sauvegardée avec succès !")
            st.session_state.config = config
    
    # Display current configuration summary
    with st.expander("📋 Résumé de la configuration"):
        st.write(f"**Serveur:** {config.server}")
        st.write(f"**Premium:** {'✅ Oui' if config.premium else '❌ Non'}")
        st.write(f"**Focus disponible:** {config.focus_points:,} points")
        st.write(f"**Ville de craft:** {config.crafting_city}")
        
        # Calculate total return rate example
        total_return = config.get_total_return_rate('ore_refining')
        st.write(f"**Return rate total (smelter):** {total_return*100:.2f}%")

if __name__ == "__main__":
    show_config_page()
