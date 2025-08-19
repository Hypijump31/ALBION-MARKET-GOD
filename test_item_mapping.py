#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.item_mapping import get_raw_item_id, get_refined_item_id

def test_enchantment_formats():
    print("=== Testing Item ID Generation ===")
    
    # Test T4.1 (enchantment level 1)
    print("\n--- T4.1 Test ---")
    raw_id = get_raw_item_id('T4', 'WOOD', 1)
    print(f"Raw T4 WOOD enchant 1: {raw_id}")
    
    refined_t3_id = get_refined_item_id('T3', 'WOOD', 1)
    print(f"Refined T3 PLANKS enchant 1: {refined_t3_id}")
    
    refined_t4_id = get_refined_item_id('T4', 'WOOD', 1)
    print(f"Refined T4 PLANKS enchant 1: {refined_t4_id}")
    
    print(f"\nItems to fetch: [{raw_id}, {refined_t3_id}, {refined_t4_id}]")
    
    # Test with list input (like from Streamlit)
    print("\n--- Testing List Input (Streamlit format) ---")
    enchant_list = ['1']
    raw_id_list = get_raw_item_id('T4', 'WOOD', enchant_list)
    print(f"Raw T4 WOOD with list ['1']: {raw_id_list}")
    
    refined_t3_list = get_refined_item_id('T3', 'WOOD', enchant_list)
    print(f"Refined T3 PLANKS with list ['1']: {refined_t3_list}")
    
    # Test normal (no enchantment)
    print("\n--- T4.0 Test (Normal) ---")
    raw_normal = get_raw_item_id('T4', 'WOOD', 0)
    refined_normal = get_refined_item_id('T4', 'WOOD', 0)
    print(f"Raw T4 WOOD normal: {raw_normal}")
    print(f"Refined T4 PLANKS normal: {refined_normal}")

if __name__ == "__main__":
    test_enchantment_formats()
