import streamlit as st
import json
import os
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SessionManager:
    """Gestionnaire de session pour la persistance des données."""
    
    def __init__(self):
        self.session_file = "session_data.json"
        self.auto_save_keys = [
            'selected_tier',
            'selected_resource_type',
            'selected_city',
            'quantity',
            'specialization',
            'premium',
            'use_focus',
            'confirm_api',
            'selected_recipe',
            'last_prices',
            'current_page'
        ]
    
    def save_session_data(self, key: str, value: Any):
        """Sauvegarde une donnée de session."""
        try:
            # Sauvegarder dans session_state
            st.session_state[key] = value
            
            # Sauvegarder sur disque si c'est une clé importante
            if key in self.auto_save_keys:
                self._save_to_file(key, value)
                logger.debug(f"Session data saved: {key}")
        except Exception as e:
            logger.error(f"Error saving session data: {e}")
    
    def load_session_data(self, key: str, default: Any = None) -> Any:
        """Charge une donnée de session."""
        try:
            # D'abord vérifier session_state
            if key in st.session_state:
                return st.session_state[key]
            
            # Ensuite charger depuis le fichier
            value = self._load_from_file(key, default)
            if value is not None:
                st.session_state[key] = value
                return value
            
            return default
        except Exception as e:
            logger.error(f"Error loading session data: {e}")
            return default
    
    def _save_to_file(self, key: str, value: Any):
        """Sauvegarde sur fichier."""
        try:
            # Charger les données existantes
            session_data = {}
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
            
            # Mettre à jour avec la nouvelle valeur
            session_data[key] = {
                'value': value,
                'timestamp': datetime.now().isoformat()
            }
            
            # Sauvegarder
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Error saving to file: {e}")
    
    def _load_from_file(self, key: str, default: Any = None) -> Any:
        """Charge depuis le fichier."""
        try:
            if not os.path.exists(self.session_file):
                return default
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            if key in session_data:
                return session_data[key]['value']
            
            return default
        
        except Exception as e:
            logger.error(f"Error loading from file: {e}")
            return default
    
    def clear_session(self):
        """Vide la session."""
        try:
            # Vider session_state
            for key in list(st.session_state.keys()):
                if key in self.auto_save_keys:
                    del st.session_state[key]
            
            # Supprimer le fichier
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            
            logger.info("Session cleared")
            
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
    
    def get_session_info(self) -> Dict[str, Any]:
        """Récupère les infos de session."""
        try:
            info = {
                'keys_in_memory': len([k for k in st.session_state.keys() if k in self.auto_save_keys]),
                'file_exists': os.path.exists(self.session_file),
                'file_size': 0
            }
            
            if info['file_exists']:
                info['file_size'] = os.path.getsize(self.session_file)
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return {}
    
    def restore_defaults(self):
        """Restaure les valeurs par défaut."""
        defaults = {
            'selected_tier': 'T4',
            'selected_resource_type': 'ORE',
            'selected_city': 'Caerleon',
            'quantity': 1000,
            'specialization': 0,
            'premium': False,
            'use_focus': False,
            'confirm_api': False,
            'selected_recipe': 'T4_SWORD'
        }
        
        for key, value in defaults.items():
            self.save_session_data(key, value)

# Instance globale
session_manager = SessionManager()

# Fonctions helper pour faciliter l'utilisation
def save_session(key: str, value: Any):
    """Sauvegarde rapide."""
    session_manager.save_session_data(key, value)

def load_session(key: str, default: Any = None) -> Any:
    """Chargement rapide."""
    return session_manager.load_session_data(key, default)

def clear_session():
    """Vider la session."""
    session_manager.clear_session()

# Example usage
if __name__ == "__main__":
    # Test du système de session
    sm = SessionManager()
    
    # Sauvegarder des données
    sm.save_session_data('test_key', 'test_value')
    sm.save_session_data('test_number', 42)
    
    # Charger des données
    value = sm.load_session_data('test_key', 'default')
    number = sm.load_session_data('test_number', 0)
    
    print(f"Loaded value: {value}")
    print(f"Loaded number: {number}")
    
    # Info de session
    info = sm.get_session_info()
    print(f"Session info: {info}")
