from typing import Dict, List, Optional
import json
import os
from datetime import datetime

class UserPreferences:

    ARXIV_CATEGORIES = {
        "Computer Science": {
            "cs.AI": "Artificial Intelligence",
            "cs.CL": "Computation and Language",
            "cs.CV": "Computer Vision and Pattern Recognition",
            "cs.LG": "Machine Learning",
            "cs.NE": "Neural and Evolutionary Computing",
            "cs.RO": "Robotics",
            "cs.SE": "Software Engineering"
        },
        "Physics": {
            "physics.app-ph": "Applied Physics",
            "physics.data-an": "Data Analysis, Statistics and Probability",
            "physics.comp-ph": "Computational Physics"
        },
        "Mathematics": {
            "math.NA": "Numerical Analysis",
            "math.ST": "Statistics Theory",
            "math.PR": "Probability"
        },
        "Statistics": {
            "stat.ML": "Machine Learning",
            "stat.TH": "Statistics Theory",
            "stat.AP": "Applications"
        },
        "Quantitative Biology": {
            "q-bio.BM": "Biomolecules",
            "q-bio.NC": "Neurons and Cognition",
            "q-bio.QM": "Quantitative Methods"
        }
    }


    def __init__(self):
        self.preferences_dir = "user_preferences"
        os.makedirs(self.preferences_dir, exist_ok=True)

    def _get_user_file_path(self, user_id: int) -> str:
        return os.path.join(self.preferences_dir, f"user_{user_id}.json")

    def get_preferences(self, user_id: int) -> Dict:
        """Get user preferences, creating default if none exist."""
        try:
            with open(self._get_user_file_path(user_id), 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            default_prefs = {
                'max_results': 10,
                'specific_journals': [],
                'preferred_categories': [],
                'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'auto_download': False,
                'preferred_categories': []
            }
            self.save_preferences(user_id, default_prefs)
            return default_prefs

    def save_preferences(self, user_id: int, preferences: Dict) -> None:
        """Save user preferences to file."""
        preferences['last_updated'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        with open(self._get_user_file_path(user_id), 'w') as f:
            json.dump(preferences, f, indent=2)

    def update_preference(self, user_id: int, key: str, value: any) -> Dict:
        """Update a single preference and return all preferences."""
        prefs = self.get_preferences(user_id)
        prefs[key] = value
        self.save_preferences(user_id, prefs)
        return prefs

    def get_max_results(self, user_id: int) -> int:
        """Get user's preferred maximum number of results."""
        return self.get_preferences(user_id).get('max_results', 10)

    def get_specific_journals(self, user_id: int) -> List[str]:
        """Get user's preferred journals."""
        return self.get_preferences(user_id).get('specific_journals', [])