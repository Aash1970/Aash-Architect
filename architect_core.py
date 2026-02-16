# VERSION 7.7.0 | CAREER ARCHITECT CORE | STATUS: FUNCTIONAL LOCK
# COPYRIGHT © 2026 ALL RIGHTS RESERVED

import hashlib, json, os, requests, zipfile
from datetime import datetime, timedelta

class ArchitectCore:
    def __init__(self):
        self.version = "7.7.0"
        self.config_file = "system_config.json"
        self.registry_file = "user_registry.json"
        self.load_config()

    def load_config(self):
        with open(self.config_file, 'r') as f:
            self.config = json.load(f)

    def get_hash(self, text):
        return hashlib.sha512(text.encode()).hexdigest()

    def get_market_intel(self, keywords):
        url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1"
        params = {
            "app_id": self.config['admin_settings']['api_keys']['adzuna_id'],
            "app_key": self.config['admin_settings']['api_keys']['adzuna_key'],
            "results_per_page": 5,
            "what": keywords,
            "content-type": "application/json"
        }
        try:
            r = requests.get(url, params=params)
            return r.json().get('results', [])
        except:
            return []

    def apply_friction(self, text):
        mapping = {"a": "а", "e": "е", "o": "о", "p": "р"}
        for eng, cyr in mapping.items():
            text = text.replace(eng, cyr)
        return text

    def create_bundle(self, name, cv, rating):
        folder = f"CA_{name.replace(' ', '_')}"
        if not os.path.exists(folder): os.makedirs(folder)
        with open(os.path.join(folder, "Protected_CV.txt"), "w", encoding="utf-8") as f:
            f.write(f"CAREER ARCHITECT | RATING: {rating}/10\n\n" + self.apply_friction(cv))
        with open(os.path.join(folder, "data.carf"), "w") as f:
            json.dump({"name": name, "cv": cv, "rating": rating, "v": self.version}, f)
        z_name = f"{folder}.zip"
        with zipfile.ZipFile(z_name, 'w') as zf:
            for root, _, files in os.walk(folder):
                for file in files: zf.write(os.path.join(root, file), file)
        return z_name
