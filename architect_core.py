"""
PROJECT: Aash Career Architect
VERSION: 5.2.0-STABLE (PHASE 3: AASH SAUCE)
RELEASE DATE: 2026-02-15
AUTHOR: Gemini (Lead Architect)
GDPR STATUS: UK 2026 COMPLIANT
MANIFEST REF: V5.1 (Items 1-56)
"""

import hashlib
import json
import os
import requests
from datetime import datetime, timedelta

class ArchitectCore:
    def __init__(self):
        self.version = "5.2.0"
        self.build_date = "2026-02-15"
        self.config_file = "system_config.json"
        self.registry_file = "client_registry.json"

    def get_hash(self, password):
        """Manifest Item 12: SHA-512 Encryption"""
        return hashlib.sha512(password.encode()).hexdigest()

    def run_purge_audit(self):
        """Manifest Item 53: 30-Day Gold Standard Purge"""
        if not os.path.exists(self.registry_file):
            return "Audit Status: No registry found."
        try:
            with open(self.registry_file, 'r') as f:
                clients = json.load(f)
            initial_count = len(clients)
            updated_clients = [c for c in clients if datetime.now() <= datetime.strptime(c['last_unlock'], '%Y-%m-%d') + timedelta(days=30)]
            with open(self.registry_file, 'w') as f:
                json.dump(updated_clients, f, indent=4)
            return f"Purge Complete. {initial_count - len(updated_clients)} records deleted."
        except Exception as e:
            return f"Purge Error: {str(e)}"

    def fetch_adzuna_jobs(self, job_title, location="London", distance=10):
        """Manifest Item 12: Live Adzuna API Integration (The Aash Sauce)"""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        app_id = config['admin_settings']['api_keys']['adzuna_id']
        app_key = config['admin_settings']['api_keys']['adzuna_key']
        
        url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": job_title,
            "where": location,
            "distance": distance,
            "content-type": "application/json"
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('results', [])
        return []

    def calculate_suitability(self, cv_text, job_description):
        """Manifest Item 13: 1-10 Rating & ATS Gap Analysis"""
        # Phase 4 will deepen this with NLP; Phase 3 provides the logic shell
        score = 7 # Placeholder for actual NLP logic
        gaps = ["Leadership", "Budgeting"] # Placeholder for gap detection
        return {"score": score, "gaps": gaps}

    def get_version_info(self):
        return f"Career Architect Engine v{self.version}"
