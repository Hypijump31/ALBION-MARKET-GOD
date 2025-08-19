#!/usr/bin/env python3
"""
Script pour vider le cache et forcer l'utilisation du nouveau format d'IDs enchantés
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def clear_cache():
    """Vider tout le cache pour forcer la régénération avec le nouveau format"""
    try:
        # Clear performance cache
        from src.performance_optimizer import performance_optimizer
        performance_optimizer.clear_cache()
        print("✅ Cache performance vidé")
        
        # Clear Streamlit cache if available
        try:
            import streamlit as st
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
            if hasattr(st, 'cache_resource'):
                st.cache_resource.clear()
            print("✅ Cache Streamlit vidé")
        except:
            print("ℹ️ Streamlit cache non disponible (normal)")
        
        # Test nouveau format
        from src.item_mapping import get_raw_item_id, get_refined_item_id
        
        print("\n=== Test nouveau format d'IDs ===")
        
        # T4.1 (enchantement 1)
        raw_id = get_raw_item_id('T4', 'WOOD', 1)
        refined_t3 = get_refined_item_id('T3', 'WOOD', 1)
        refined_t4 = get_refined_item_id('T4', 'WOOD', 1)
        
        print(f"Raw T4 WOOD enchant 1: {raw_id}")
        print(f"Refined T3 PLANKS enchant 1: {refined_t3}")
        print(f"Refined T4 PLANKS enchant 1: {refined_t4}")
        
        # Vérifier le format correct
        expected_format = "LEVEL1@1"
        if expected_format in raw_id and expected_format in refined_t3 and expected_format in refined_t4:
            print("\n✅ NOUVEAU FORMAT CORRECT : LEVEL1@1")
        else:
            print(f"\n❌ Format incorrect détecté!")
            print(f"   Attendu: contient '{expected_format}'")
            print(f"   Raw: {raw_id}")
            print(f"   T3 Refined: {refined_t3}")
            print(f"   T4 Refined: {refined_t4}")
        
        print(f"\nItems pour API: [{raw_id}, {refined_t3}, {refined_t4}]")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du vidage du cache: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧹 Vidage du cache pour nouveau format d'enchantements...")
    success = clear_cache()
    
    if success:
        print("\n🎉 Cache vidé avec succès!")
        print("   Redémarrez l'application Streamlit pour appliquer les changements.")
    else:
        print("\n💥 Erreur lors du vidage du cache.")
