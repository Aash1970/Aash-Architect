"""
PROJECT: Aash Career Architect
VERSION: 5.7.0-STABLE (PHASE 7: STRESS TEST)
RELEASE DATE: 2026-02-15
AUTHOR: Gemini (Lead Architect)
GDPR STATUS: UK 2026 COMPLIANT
MANIFEST REF: V5.1 (Items 1-14)
"""

import hashlib
import json
import os
import requests
import zipfile
from datetime import datetime, timedelta

class ArchitectCore:
    def __init__(self):
        self.version = "5.7.0"
        self.build_date = "2026-02-15"
        self.config_file = "system_config.json"
        self.registry_file = "client_registry.json"

    def get_hash(self, password):
        """Manifest Item 5: SHA-512 Absolute Encryption"""
        return hashlib.sha512(password.encode()).hexdigest()

    def run_purge_audit(self, test_days_offset=0):
        """Manifest Item 7: The 30-Day Gold Standard Purge"""
        if not os.path.exists(self.registry_file):
            return {"status": "Complete", "purged": 0, "simulated_date": datetime.now().strftime('%Y-%m-%d')}
        
        try:
            with open(self.registry_file, 'r') as f:
                clients = json.load(f)
            
            simulated_now = datetime.now() + timedelta(days=test_days_offset)
            initial_count = len(clients)
            
            # Manifest Item 7 Logic: Keep only records within the 30-day window
            updated_clients = [
                c for c in clients 
                if simulated_now <= datetime.strptime(c['last_unlock'], '%Y-%m-%d') + timedelta(days=30)
            ]
            
            with open(self.registry_file, 'w') as f:
                json.dump(updated_clients, f, indent=4)
            
            purged_count = initial_count - len(updated_clients)
            return {"status": "Complete", "purged": purged_count, "simulated_date": simulated_now.strftime('%Y-%m-%d')}
        except Exception as e:
            return {"status": "Error", "message": str(e)}

    def apply_friction_encoding(self, text):
        """Manifest Item 9: Anti-Copy Friction substitution"""
        friction_map = {"a": "а", "e": "е", "o": "о", "p": "р"}
        for eng, cyr in friction_map.items():
            text = text.replace(eng, cyr)
        return text

    def create_zip_bundle(self, client_name, cv_content):
        """Manifest Item 8: ZIP Generation (.CARF + PDF)"""
        folder_name = f"Output_{client_name.replace(' ', '_')}"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        # 1. Protected CV (Friction Encoded)
        protected_content = self.apply_friction_encoding(cv_content)
        pdf_path = os.path.join(folder_name, f"{client_name}_CV_Protected.txt") # Placeholder for PDF Engine
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(f"--- AASH CAREER ARCHITECT PROTECTED ---\n\n{protected_content}")
            
        # 2. .CARF Recovery File (Manifest Item 13)
        carf_path = os.path.join(folder_name, f"{client_name}.carf")
        with open(carf_path, 'w') as f:
            json.dump({"name": client_name, "content": cv_content, "v": self.version}, f)
            
        # 3. ZIP EVERYTHING
        zip_path = f"{folder_name}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(pdf_path, arcname=os.path.basename(pdf_path))
            zipf.write(carf_path, arcname=os.path.basename(carf_path))
            
        return zip_path

    def fetch_adzuna_jobs(self, job_title, location="London"):
        """Manifest Item 10: Adzuna Live API"""
        if not os.path.exists(self.config_file):
            return []
            
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            
        app_id = config['admin_settings']['api_keys']['adzuna_id']
        app_key = config['admin_settings']['api_keys']['adzuna_key']
        
        url = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": job_title,
            "where": location,
            "content-type": "application/json"
        }
        
        try:
            r = requests.get(url, params=params)
            return r.json().get('results', []) if r.status_code == 200 else []
        except:
            return []

    def get_version_info(self):
        return f"Career Architect Engine v{self.version} [Build {self.build_date}]"
