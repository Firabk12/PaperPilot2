from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class NotificationPreferences:
    def __init__(self):
        self.notifications_dir = "user_notifications"
        os.makedirs(self.notifications_dir, exist_ok=True)

    def _get_user_file_path(self, user_id: int) -> str:
        return os.path.join(self.notifications_dir, f"notifications_{user_id}.json")

    def get_preferences(self, user_id: int) -> Dict:
        """Get user notification preferences."""
        try:
            with open(self._get_user_file_path(user_id), 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            default_prefs = {
                'enabled': False,
                'frequency': 'daily',  # or 'weekly'
                'keywords': [],
                'categories': [],
                'last_notification': None,
                'notification_time': "09:00",  # Default to 9 AM UTC
                'last_checked': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.save_preferences(user_id, default_prefs)
            return default_prefs

    def save_preferences(self, user_id: int, preferences: Dict) -> None:
        """Save user notification preferences."""
        with open(self._get_user_file_path(user_id), 'w') as f:
            json.dump(preferences, f, indent=2)

    def add_keyword(self, user_id: int, keyword: str) -> None:
        """Add a keyword to user's notification preferences."""
        prefs = self.get_preferences(user_id)
        if keyword not in prefs['keywords']:
            prefs['keywords'].append(keyword)
            self.save_preferences(user_id, prefs)

    def remove_keyword(self, user_id: int, keyword: str) -> None:
        """Remove a keyword from user's notification preferences."""
        prefs = self.get_preferences(user_id)
        if keyword in prefs['keywords']:
            prefs['keywords'].remove(keyword)
            self.save_preferences(user_id, prefs)

    def should_notify(self, user_id: int) -> bool:
        """Check if it's time to send notifications to the user."""
        prefs = self.get_preferences(user_id)

        if not prefs['enabled']:
            return False

        last_notification = prefs.get('last_notification')
        if not last_notification:
            return True

        last_notification = datetime.strptime(last_notification, '%Y-%m-%d %H:%M:%S')
        now = datetime.utcnow()

        if prefs['frequency'] == 'daily':
            return (now - last_notification) >= timedelta(days=1)
        elif prefs['frequency'] == 'weekly':
            return (now - last_notification) >= timedelta(days=7)

        return False