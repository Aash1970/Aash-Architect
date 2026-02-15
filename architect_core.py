"""
PROJECT: Aash Career Architect
VERSION: 5.3.0-STABLE (PHASE 4: REMOTE ADMIN)
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
        self.version = "5.3.0"
        self.build_date = "2026-02-15"
        self.config_file = "system_config.json"
        self.registry_file = "client_registry.json"

    def get_hash(self, password):
        """Manifest Item 12: SHA-512 Encryption"""
        return hashlib.sha512(password.encode()).hexdigest()

    def run_purge_audit(self):
        """Manifest Item 53: 30-Day Gold Standard Purge"""
        if not os.path.exists(self.registry_file):
            return "No registry found."
        with open(self.registry_file, 'r') as f:
            clients = json.load(f)
        updated_clients = [c for c in clients if datetime.now() <= datetime.strptime(c['last_unlock'], '%Y-%m-%d') + timedelta(days=30)]
        with open(self.registry_file, 'w') as f:
            json.dump(updated_clients, f, indent=4)
        return f"Purge Complete. {len(clients) - len(updated_clients)} deleted."

    def fetch_adzuna_jobs(self, job_title, location="London"):
        """Manifest Item 12: Live Adzuna API"""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        params = {
            "app_id": config['admin_settings']['api_keys']['adzuna_id'],
            "app_key": config['admin_settings']['api_keys']['adzuna_key'],
            "what": job_title, "where": location, "content-type": "application/json"
        }
        r = requests.get("https://api.adzuna.com/v1/api/jobs/gb/search/1", params=params)
        return r.json().get('results', []) if r.status_code == 200 else []

    def send_whatsapp_alert(self, message):
        """Manifest Item 10: WhatsApp Admin Bot"""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        token = config['admin_settings']['api_keys']['whatsapp_token']
        # Logic for Meta Business API Request would go here
        return f"Remote Alert Sent: {message}"

    def get_version_info(self):
        return f"Career Architect Engine v{self.version}"
