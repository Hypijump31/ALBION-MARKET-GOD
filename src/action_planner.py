import streamlit as st
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ActionPlanner:
    """Générateur de plan d'action concret pour les activités d'Albion Online."""
    
    def __init__(self):
        pass
    
    def create_refining_action_plan(self, arbitrage_analysis: Dict, tier: str, resource_type: str, 
                                  quantity: int, profit_data: Dict, selected_city: str) -> Dict:
        """
        Crée un plan d'action concret pour le raffinage.
        
        Args:
            arbitrage_analysis: Données d'analyse d'arbitrage
            tier: Tier de la ressource
            resource_type: Type de ressource
            quantity: Quantité à traiter
            profit_data: Données de profit calculées
            selected_city: Ville sélectionnée pour le raffinage
            
        Returns:
            Dict contenant le plan d'action détaillé
        """
        plan = {
            'is_profitable': False,
            'summary': '',
            'steps': [],
            'financial_summary': {},
            'warnings': [],
            'recommendations': []
        }
        
        # Extraire les recommandations d'arbitrage
        raw_rec = arbitrage_analysis.get('raw_recommendations', {})
        prev_refined_rec = arbitrage_analysis.get('prev_refined_recommendations', {})
        refined_rec = arbitrage_analysis.get('refined_recommendations', {})

        # Extraire les détails pour les étapes du plan
        raw_buy_city = raw_rec.get('buy_recommendation', {}).get('city')
        raw_buy_price = raw_rec.get('buy_recommendation', {}).get('price', 0)
        prev_refined_buy_city = prev_refined_rec.get('buy_recommendation', {}).get('city')
        prev_refined_buy_price = prev_refined_rec.get('buy_recommendation', {}).get('price', 0)
        refined_sell_city = refined_rec.get('sell_recommendation', {}).get('city')
        refined_sell_price = refined_rec.get('sell_recommendation', {}).get('price', 0)
        refined_rec = arbitrage_analysis.get('refined_recommendations', {})
        
        # Utiliser les données de profit du calculateur comme unique source de vérité
        if profit_data and profit_data.net_profit is not None:
            if profit_data.net_profit > 0:
                plan['is_profitable'] = True
                
                # Extraire les quantités du calculateur pour être précis
                refined_quantity = profit_data.refined_quantity
                prev_refined_needed = profit_data.prev_refined_needed

                plan['financial_summary'] = {
                    'investment': profit_data.total_cost,
                    'revenue': profit_data.total_revenue,
                    'profit': profit_data.net_profit,
                    'margin': profit_data.profit_margin,
                    'raw_needed': quantity,
                    'prev_refined_needed': prev_refined_needed,
                    'refined_produced': refined_quantity,
                    'premium_status': profit_data.premium,
                    'focus_used': profit_data.use_focus
                }
                
                # Créer le résumé
                plan['summary'] = f"💰 PLAN RENTABLE: {profit_data.net_profit:,.0f} 🪙 de profit ({profit_data.profit_margin:.1f}% marge)"
                
                # Calculer le tier précédent pour affichage
                prev_tier_num = int(tier[1:]) - 1
                prev_tier = f"T{prev_tier_num}" if prev_tier_num >= 1 else tier
                
                # Étapes détaillées avec vraie recette Albion
                plan['steps'] = [
                    {
                        'step': 1,
                        'action': 'ACHETER',
                        'what': f"{quantity:,} x {tier} {resource_type} (brut)",
                        'where': raw_buy_city,
                        'price': f"{raw_buy_price:,.0f} 🪙/unité",
                        'total_cost': f"{profit_data.raw_material_cost:,.0f} 🪙",
                        'icon': '🛒'
                    },
                    {
                        'step': 2,
                        'action': 'ACHETER',
                        'what': f"{prev_refined_needed:,} x {prev_tier} {resource_type} (raffiné)",
                        'where': prev_refined_buy_city,
                        'price': f"{prev_refined_buy_price:,.0f} 🪙/unité",
                        'total_cost': f"{profit_data.prev_refined_material_cost:,.0f} 🪙",
                        'icon': '🛒'
                    },
                    {
                        'step': 3,
                        'action': 'TRANSPORTER',
                        'what': f"Tous matériaux → {selected_city}",
                        'where': selected_city,
                        'price': 'Variable selon distance',
                        'total_cost': 'À calculer',
                        'icon': '🚚'
                    },
                    {
                        'step': 4,
                        'action': 'RAFFINER',
                        'what': f"{quantity:,} x {tier} brut + {prev_refined_needed:,} x {prev_tier} raffiné → {tier} {resource_type}",
                        'where': selected_city,
                        'price': 'Coût focus + taxes',
                        'total_cost': f"~{refined_quantity:,} {tier} raffinées produites",
                        'icon': '🔥'
                    },
                    {
                        'step': 5,
                        'action': 'TRANSPORTER',
                        'what': f"Matières raffinées → {refined_sell_city}",
                        'where': refined_sell_city,
                        'price': 'Variable selon distance',
                        'total_cost': 'À calculer',
                        'icon': '🚚'
                    },
                    {
                        'step': 6,
                        'action': 'VENDRE',
                        'what': f"{refined_quantity:,} x {tier} {resource_type} (raffiné)",
                        'where': refined_sell_city,
                        'price': f"{refined_sell_price:,.0f} 🪙/unité",
                        'total_cost': f"{profit_data.total_revenue:,.0f} 🪙",
                        'icon': '💰'
                    }
                ]
                
                # Recommandations
                focus_rec = f"⚡ Focus utilisé (Retour: {profit_data.return_rate*100:.1f}%) - Coût: {profit_data.focus_cost:,} points" if profit_data.use_focus else "🔵 Focus non utilisé - envisagez de l'activer pour plus de profit"
                premium_rec = "👑 Statut Premium activé" if profit_data.premium else "Statut Premium non actif"

                plan['recommendations'] = [
                    f"✅ Rentabilité confirmée avec {profit_data.profit_margin:.1f}% de marge",
                    focus_rec,
                    premium_rec,
                    f"🏆 Route optimale: {raw_buy_city} → {selected_city} → {refined_sell_city}",
                    f"📊 Surveillez les prix - recalculez si écart > 10%"
                ]
                
                # Avertissements
                if raw_buy_city == refined_sell_city:
                    plan['warnings'].append("⚠️ Achat et vente dans la même ville - pas d'arbitrage géographique")
                
                if profit_data.profit_margin < 10:
                    plan['warnings'].append("⚠️ Marge faible - attention aux coûts de transport")
                
                if selected_city != raw_buy_city and selected_city != refined_sell_city:
                    plan['warnings'].append("💡 Double transport nécessaire - vérifiez les coûts")
                    
            else:
                # Calculer la perte par unité pour l'affichage
                from src.refining_calculator import REFINING_DATA
                requirements = REFINING_DATA['resource_requirements'].get(tier, {'raw': 2})
                raw_per_refined = requirements['raw']
                refined_quantity = quantity // raw_per_refined if raw_per_refined > 0 else 0
                loss_per_unit = profit_data.net_profit / refined_quantity if refined_quantity > 0 else 0
                
                plan['summary'] = f"❌ NON RENTABLE: Perte de {abs(loss_per_unit):,.0f} 🪙 par unité raffinée"
                plan['warnings'].append("❌ Cette stratégie génère des pertes")
                plan['recommendations'].append("🔄 Essayez un autre tier ou type de ressource")
        else:
            plan['summary'] = "⚠️ DONNÉES INSUFFISANTES: Prix manquants pour calculer la rentabilité"
            plan['warnings'].append("📊 Vérifiez la disponibilité des prix sur le marché")
        
        return plan
    
    def display_action_plan(self, plan: Dict):
        """Affiche le plan d'action dans Streamlit de manière très claire."""
        if not plan:
            st.error("❌ Impossible de créer un plan d'action")
            return
        
        # En-tête avec statut
        if plan['is_profitable']:
            st.success(f"## 🎯 {plan['summary']}")
        else:
            st.error(f"## ❌ {plan['summary']}")
        
        # Résumé financier
        if plan.get('financial_summary'):
            fin = plan['financial_summary']
            
            st.markdown("### 💰 **RÉSUMÉ FINANCIER**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💸 Investissement", f"{fin['investment']:,.0f} 🪙")
                st.metric("💰 Revenu", f"{fin['revenue']:,.0f} 🪙")
            with col2:
                st.metric("📈 Profit Net", f"{fin['profit']:,.0f} 🪙", 
                         delta=f"{fin['margin']:.1f}%")
                st.metric("⚡ Raffinés Produits", f"{fin['refined_produced']:,}")
            with col3:
                premium_text = "👑 Premium Actif" if fin['premium_status'] else "Premium Inactif"
                focus_text = "⚡ Focus Utilisé" if fin['focus_used'] else "🔵 Focus Non Utilisé"
                st.info(premium_text)
                st.info(focus_text)
        
        # Plan d'action étape par étape
        if plan.get('steps'):
            st.markdown("---")
            st.markdown("### 📋 **PLAN D'ACTION DÉTAILLÉ**")
            
            for step in plan['steps']:
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                    
                    with col1:
                        st.markdown(f"## {step['icon']}")
                        st.markdown(f"**#{step['step']}**")
                    
                    with col2:
                        st.markdown(f"**{step['action']}** {step['what']}")
                        if step['where']:
                            st.caption(f"📍 {step['where']}")
                    
                    with col3:
                        st.write(f"💰 {step['price']}")
                    
                    with col4:
                        st.write(f"**{step['total_cost']}**")
                
                st.markdown("---")
        
        # Recommandations
        if plan.get('recommendations'):
            st.markdown("### 💡 **RECOMMANDATIONS**")
            for rec in plan['recommendations']:
                st.info(rec)
        
        # Avertissements
        if plan.get('warnings'):
            st.markdown("### ⚠️ **POINTS D'ATTENTION**")
            for warning in plan['warnings']:
                st.warning(warning)
    
    def create_quick_summary(self, plan: Dict) -> str:
        """Crée un résumé ultra-concis du plan."""
        if not plan or not plan.get('is_profitable'):
            return "❌ Non rentable actuellement"
        
        steps = plan.get('steps', [])
        if len(steps) >= 3:
            buy_step = steps[0]
            refine_step = steps[2]  
            sell_step = steps[-1]
            
            return f"🛒 {buy_step['where']} → 🔥 {refine_step['where']} → 💰 {sell_step['where']}"
        
        return "✅ Plan disponible"

# Instance globale
action_planner = ActionPlanner()
