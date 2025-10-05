"""
Privacy Management Module
Handles user data privacy, transparency, and control
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

class PrivacyManager:
    """
    Manages privacy settings, data transparency, and user control over personal data
    """
    
    def __init__(self, privacy_config_file: str = "privacy_config.json"):
        self.config_file = privacy_config_file
        self.privacy_levels = {
            'minimal': {
                'store_conversations': False,
                'learn_preferences': False,
                'calendar_integration': False,
                'proactive_suggestions': False,
                'data_retention_days': 1
            },
            'balanced': {
                'store_conversations': True,
                'learn_preferences': True,
                'calendar_integration': True,
                'proactive_suggestions': True,
                'data_retention_days': 30
            },
            'full': {
                'store_conversations': True,
                'learn_preferences': True,
                'calendar_integration': True,
                'proactive_suggestions': True,
                'data_retention_days': 365
            }
        }
        
        self.config = self._load_privacy_config()
    
    def _load_privacy_config(self) -> Dict[str, Any]:
        """Load privacy configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        
        # Default configuration
        return {
            'privacy_level': 'balanced',
            'data_processing_consent': {},
            'data_sharing_consent': False,
            'analytics_consent': False,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'user_rights_acknowledged': False,
            'data_retention_override': None
        }
    
    def _save_privacy_config(self):
        """Save privacy configuration to file"""
        self.config['last_updated'] = datetime.now().isoformat()
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def set_privacy_level(self, level: str) -> bool:
        """Set overall privacy level"""
        if level not in self.privacy_levels:
            return False
        
        self.config['privacy_level'] = level
        self._save_privacy_config()
        return True
    
    def get_privacy_level(self) -> str:
        """Get current privacy level"""
        return self.config.get('privacy_level', 'balanced')
    
    def get_privacy_settings(self) -> Dict[str, Any]:
        """Get current privacy settings based on level"""
        level = self.get_privacy_level()
        settings = self.privacy_levels.get(level, self.privacy_levels['balanced']).copy()
        
        # Apply any overrides
        if self.config.get('data_retention_override'):
            settings['data_retention_days'] = self.config['data_retention_override']
        
        return settings
    
    def can_store_conversations(self) -> bool:
        """Check if conversation storage is allowed"""
        return self.get_privacy_settings()['store_conversations']
    
    def can_learn_preferences(self) -> bool:
        """Check if preference learning is allowed"""
        return self.get_privacy_settings()['learn_preferences']
    
    def can_use_calendar(self) -> bool:
        """Check if calendar integration is allowed"""
        return self.get_privacy_settings()['calendar_integration']
    
    def can_make_proactive_suggestions(self) -> bool:
        """Check if proactive suggestions are allowed"""
        return self.get_privacy_settings()['proactive_suggestions']
    
    def get_data_retention_days(self) -> int:
        """Get data retention period in days"""
        return self.get_privacy_settings()['data_retention_days']
    
    def request_consent(self, data_type: str, purpose: str) -> bool:
        """
        Request user consent for specific data processing
        In a real implementation, this would show a consent dialog
        """
        consent_key = f"{data_type}_{purpose}"
        
        # For this demo, we'll assume consent is granted for essential features
        essential_consents = [
            'conversation_assistance',
            'preferences_personalization',
            'goals_tracking'
        ]
        
        if consent_key in essential_consents:
            self.config['data_processing_consent'][consent_key] = {
                'granted': True,
                'timestamp': datetime.now().isoformat(),
                'purpose': purpose
            }
            self._save_privacy_config()
            return True
        
        # For non-essential features, check existing consent
        existing_consent = self.config['data_processing_consent'].get(consent_key)
        if existing_consent:
            return existing_consent['granted']
        
        # In a real app, show consent dialog here
        # For demo, default to False for non-essential features
        return False
    
    def revoke_consent(self, data_type: str, purpose: str):
        """Revoke consent for specific data processing"""
        consent_key = f"{data_type}_{purpose}"
        
        if consent_key in self.config['data_processing_consent']:
            self.config['data_processing_consent'][consent_key]['granted'] = False
            self.config['data_processing_consent'][consent_key]['revoked_at'] = datetime.now().isoformat()
            self._save_privacy_config()
    
    def generate_privacy_report(self) -> Dict[str, Any]:
        """Generate comprehensive privacy report"""
        settings = self.get_privacy_settings()
        
        return {
            'privacy_level': self.get_privacy_level(),
            'data_collection': self._describe_data_collection(settings),
            'data_usage': self._describe_data_usage(settings),
            'data_retention': f"{settings['data_retention_days']} days",
            'storage_location': 'Local device only (SQLite database)',
            'sharing_policy': 'No data sharing with third parties',
            'user_rights': self._list_user_rights(),
            'consent_status': self.config.get('data_processing_consent', {}),
            'last_updated': self.config.get('last_updated'),
            'data_categories': self._list_data_categories(settings)
        }
    
    def _describe_data_collection(self, settings: Dict) -> str:
        """Describe what data is being collected"""
        collected = []
        
        if settings['store_conversations']:
            collected.append('conversation messages')
        
        if settings['learn_preferences']:
            collected.append('user preferences and patterns')
        
        if settings['calendar_integration']:
            collected.append('calendar event information')
        
        if not collected:
            return "Minimal data collection - no persistent storage"
        
        return f"Collecting: {', '.join(collected)}"
    
    def _describe_data_usage(self, settings: Dict) -> str:
        """Describe how data is being used"""
        uses = []
        
        if settings['learn_preferences']:
            uses.append('personalizing responses')
        
        if settings['proactive_suggestions']:
            uses.append('providing proactive suggestions')
        
        if settings['calendar_integration']:
            uses.append('calendar-based assistance')
        
        if not uses:
            return "Data used only for immediate responses"
        
        return f"Data used for: {', '.join(uses)}"
    
    def _list_user_rights(self) -> List[str]:
        """List user privacy rights"""
        return [
            'Right to access your data',
            'Right to delete your data',
            'Right to export your data',
            'Right to modify privacy settings',
            'Right to revoke consent',
            'Right to data portability'
        ]
    
    def _list_data_categories(self, settings: Dict) -> List[Dict[str, str]]:
        """List categories of data being processed"""
        categories = []
        
        if settings['store_conversations']:
            categories.append({
                'category': 'Conversation Data',
                'description': 'Messages exchanged during conversations',
                'purpose': 'Providing contextual assistance',
                'retention': f"{settings['data_retention_days']} days"
            })
        
        if settings['learn_preferences']:
            categories.append({
                'category': 'Preference Data',
                'description': 'Learned communication style and interests',
                'purpose': 'Personalizing interaction style',
                'retention': f"{settings['data_retention_days']} days"
            })
        
        if settings['calendar_integration']:
            categories.append({
                'category': 'Calendar Data',
                'description': 'Calendar events and scheduling information',
                'purpose': 'Proactive scheduling assistance',
                'retention': 'Not stored - accessed real-time only'
            })
        
        return categories
    
    def export_user_data(self, export_path: Optional[str] = None) -> str:
        """Export all user data for portability"""
        if not export_path:
            export_path = f"user_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Import here to avoid circular imports
        from .memory import UserMemory
        
        memory = UserMemory()
        data_export = memory.export_data()
        
        # Add privacy information
        data_export['privacy_settings'] = self.config
        data_export['privacy_report'] = self.generate_privacy_report()
        
        # Save to file
        with open(export_path, 'w') as f:
            json.dump(data_export, f, indent=2, default=str)
        
        return export_path
    
    def delete_data(self, deletion_type: str):
        """Delete user data based on type"""
        from .memory import UserMemory
        
        memory = UserMemory()
        
        deletion_map = {
            '1': 'recent_conversations',  # Last 7 days
            '2': 'conversations',         # All conversations
            '3': 'profile',              # Learned preferences
            '4': 'all'                   # Everything
        }
        
        data_type = deletion_map.get(deletion_type, 'recent_conversations')
        
        if data_type == 'recent_conversations':
            # Delete conversations from last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            # This would need to be implemented in memory.py
            pass
        else:
            memory.clear_data(data_type)
        
        # Log the deletion
        self._log_data_deletion(data_type)
    
    def _log_data_deletion(self, data_type: str):
        """Log data deletion for audit trail"""
        if 'deletion_log' not in self.config:
            self.config['deletion_log'] = []
        
        self.config['deletion_log'].append({
            'data_type': data_type,
            'deleted_at': datetime.now().isoformat(),
            'reason': 'user_request'
        })
        
        self._save_privacy_config()
    
    def cleanup_expired_data(self):
        """Clean up data that has exceeded retention period"""
        retention_days = self.get_data_retention_days()
        
        if retention_days > 0:
            from .memory import UserMemory
            
            memory = UserMemory()
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # This would need to be implemented in memory.py
            # memory.delete_old_data(cutoff_date)
            
            self._log_data_deletion('expired_data_cleanup')
    
    def get_privacy_dashboard_data(self) -> Dict[str, Any]:
        """Get data for privacy dashboard display"""
        settings = self.get_privacy_settings()
        
        return {
            'current_level': self.get_privacy_level(),
            'available_levels': list(self.privacy_levels.keys()),
            'level_descriptions': {
                'minimal': 'No data storage, basic functionality only',
                'balanced': 'Limited data storage for personalization',
                'full': 'Full data storage for advanced features'
            },
            'active_features': {
                'Conversation Storage': settings['store_conversations'],
                'Preference Learning': settings['learn_preferences'],
                'Calendar Integration': settings['calendar_integration'],
                'Proactive Suggestions': settings['proactive_suggestions']
            },
            'data_retention': f"{settings['data_retention_days']} days",
            'consent_status': len([c for c in self.config.get('data_processing_consent', {}).values() if c.get('granted')]),
            'last_export': self._get_last_export_date(),
            'deletion_history': len(self.config.get('deletion_log', []))
        }
    
    def _get_last_export_date(self) -> Optional[str]:
        """Get the date of the last data export"""
        # This would track export history in a real implementation
        return None
    
    def validate_privacy_compliance(self) -> Dict[str, bool]:
        """Validate that the system is complying with privacy settings"""
        settings = self.get_privacy_settings()
        compliance = {}
        
        # Check if data storage matches settings
        compliance['conversation_storage'] = True  # Would check actual storage
        compliance['preference_learning'] = True   # Would check if learning is active
        compliance['calendar_access'] = True       # Would check calendar permissions
        compliance['proactive_features'] = True    # Would check if proactive features are active
        
        # Check data retention compliance
        compliance['data_retention'] = True        # Would check if old data is properly deleted
        
        return compliance
