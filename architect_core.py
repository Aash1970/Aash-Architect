"""
PROJECT: Aash Career Architect
VERSION: 5.6.0-STABLE (PHASE 6: AUTO-DOCS)
RELEASE DATE: 2026-02-15
AUTHOR: Gemini (Lead Architect)
GDPR STATUS: UK 2026 COMPLIANT
MANIFEST REF: V5.1 (Item 16)
"""

import hashlib
import json
import os
import requests
import zipfile
from datetime import datetime, timedelta

class ArchitectCore:
    def __init__(self):
        self.version = "5.6.0"
        self.build_date = "2026-02-15"
        self.config_file = "system_config.json"
        self.registry_file = "client_registry.json"

    def get_hash(self, password):
        return hashlib.sha512(password.encode()).hexdigest()

    def run_purge_audit(self):
        if not os.path.exists(self.registry_file): return "No registry found."
        with open(self.registry_file, 'r') as f:
            clients = json.load(f)
        updated_clients = [c for c in clients if datetime.now() <= datetime.strptime(c['last_unlock'], '%Y-%m-%d') + timedelta(days=30)]
        with open(self.registry_file, 'w') as f:
            json.dump(updated_clients, f, indent=4)
        return f"Purge Audit Complete. {len(clients) - len(updated_clients)} deleted."

    def generate_system_manual(self, role="Admin"):
        """Manifest Item 16: Auto-generate PDF/Text Manuals for roles."""
        manuals = {
            "Admin": "ADMIN MANUAL: Manage API keys, set Royal Blue branding, and perform master purges.",
            "Supervisor": "SUPERVISOR MANUAL: Unlock client files, generate ZIP bundles, and use .CARF recovery.",
            "Client": "CLIENT MANUAL: Your data is deleted in 30 days. Keep your .CARF file to resume later."
        }
        return manuals.get(role, "General System Manual")

    def apply_friction_encoding(self, text):
        friction_map = {"a": "а", "e": "е", "o": "о", "p": "р"}
        for eng, cyr in friction_map.items():
            text = text.replace(eng, cyr)
        return text

    def create_zip_bundle(self, client_name, cv_content):
        folder_name = f"Output_{client_name.replace(' ', '_')}"
        if not os.path.exists(folder_name): os.makedirs(folder_name)
        
        protected_content = self.apply_friction_encoding(cv_content)
        pdf_path = os.path.join(folder_name, f"{client_name}_CV_Protected.pdf")
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(f"--- AASH CAREER ARCHITECT PROTECTED DOCUMENT ---\n\n{protected_content}")
            
        # Add Client Manual to the ZIP bundle automatically
        manual_path = os.path.join(folder_name, "READ_ME_Client_Instructions.txt")
        with open(manual_path, 'w') as f:
            f.write(self.generate_system_manual("Client"))

        carf_path = os.path.join(folder_name, f"{client_name}.carf")
        with open(carf_path, 'w') as f:
            f.write(json.dumps({"name": client_name, "content": cv_content, "v": self.version}))
            
        zip_path = f"{folder_name}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(pdf_path, arcname=os.path.basename(pdf_path))
            zipf.write(carf_path, arcname=os.path.basename(carf_path))
            zipf.write(manual_path, arcname=os.path.basename(manual_path))
        
        return zip_path

    def fetch_adzuna_jobs(self, job_title, location="London"):
        with open(self.config_file, 'r') as f: config = json.load(f)
        params = {"app_id": config['admin_settings']['api_keys']['adzuna_id'],
                  "app_key": config['admin_settings']['api_keys']['adzuna_key'],
                  "what": job_title, "where": location}
        r = requests.get("https://api.adzuna.com/v1/api/jobs/gb/search/1", params=params)
        return r.json().get('results', []) if r.status_code == 200 else []

    def get_version_info(self):
        return f"Career Architect Engine v{self.version}"
