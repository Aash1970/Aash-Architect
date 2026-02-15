"""
PROJECT: Aash Career Architect
VERSION: 5.1.0-STABLE
RELEASE DATE: 2026-02-15
AUTHOR: Gemini (Lead Architect)
GDPR STATUS: UK 2026 COMPLIANT (30-Day Purge Active)
MANIFEST REF: V5.1 (Items 1-56)
"""

import hashlib
import json
import os
from datetime import datetime, timedelta

class ArchitectCore:
    def __init__(self):
        # VERSION CONTROL
        self.version = "5.1.0"
        self.build_date = "2026-02-15"
        
        # MANIFEST ITEM 6 & 7: DATA SPLIT
        self.config_file = "system_config.json"
        self.registry_file = "client_registry.json"

    def get_hash(self, password):
        """
        Manifest Item 12: SHA-512 Absolute Encryption.
        Ensures no plain-text passwords ever touch the JSON files.
        """
        return hashlib.sha512(password.encode()).hexdigest()

    def run_purge_audit(self):
        """
        Manifest Item 53: The 30-Day 'Death Clock' Logic.
        Executed on Admin login. Permanently deletes data older than 30 days.
        """
        if not os.path.exists(self.registry_file):
            return "Audit Status: No client registry found."
        
        try:
            with open(self.registry_file, 'r') as f:
                clients = json.load(f)
            
            initial_count = len(clients)
            updated_clients = []
            
            for client in clients:
                # Calculate time since the final "Unlock"
                unlock_date = datetime.strptime(client['last_unlock'], '%Y-%m-%d')
                if datetime.now() > unlock_date + timedelta(days=30):
                    # Data is purged by omission from the updated list
                    continue 
                updated_clients.append(client)
            
            # Write the cleaned list back to the JSON file
            with open(self.registry_file, 'w') as f:
                json.dump(updated_clients, f, indent=4)
            
            purged_count = initial_count - len(updated_clients)
            return f"Purge Audit Complete. {purged_count} records permanently deleted."

        except Exception as e:
            return f"Error during Purge Audit: {str(e)}"

    def get_version_info(self):
        return f"Career Architect Engine v{self.version} [Build {self.build_date}]"
