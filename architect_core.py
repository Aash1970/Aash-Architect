# VERSION 7.6.0 | CAREER ARCHITECT CORE | STATUS: FUNCTIONAL LOCK
import hashlib, json, os, requests, zipfile
from datetime import datetime, timedelta

class ArchitectCore:
    def __init__(self):
        self.version = "7.6.0"
        self.config_file = "system_config.json"
        self.registry_file = "client_registry.json"
        self.load_config()

    def load_config(self):
        with open(self.config_file, 'r') as f:
            self.config = json.load(f)

    def get_hash(self, text):
        return hashlib.sha512(text.encode()).hexdigest()

    def get_market_intel(self, keywords):
        # ADZUNA API INTEGRATION
        url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1"
        params = {
            "app_id": self.config['adzuna_id'],
            "app_key": self.config['adzuna_key'],
            "results_per_page": 5,
            "what": keywords,
            "content-type": "application/json"
        }
        try:
            r = requests.get(url, params=params)
            return r.json().get('results', [])
        except:
            return []

    def run_purge_audit(self):
        if not os.path.exists(self.registry_file): return 0
        with open(self.registry_file, 'r') as f:
            clients = json.load(f)
        
        now = datetime.now()
        # Keep only clients seen in the last 30 days
        keep = [c for c in clients if (now - datetime.strptime(c['date'], '%Y-%m-%d')).days < 30]
        purged_count = len(clients) - len(keep)
        
        with open(self.registry_file, 'w') as f:
            json.dump(keep, f, indent=4)
        return purged_count

    def apply_friction(self, text):
        mapping = {"a": "а", "e": "е", "o": "о", "p": "р"}
        for eng, cyr in mapping.items():
            text = text.replace(eng, cyr)
        return text

    def create_bundle(self, name, cv, rating):
        folder = f"CA_{name.replace(' ', '_')}"
        if not os.path.exists(folder): os.makedirs(folder)
        
        # Save Registry Entry
        entry = {"name": name, "date": datetime.now().strftime('%Y-%m-%d'), "rating": rating}
        clients = []
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f: clients = json.load(f)
        clients.append(entry)
        with open(self.registry_file, 'w') as f: json.dump(clients, f, indent=4)

        # Create Files
        with open(os.path.join(folder, "Protected_CV.txt"), "w", encoding="utf-8") as f:
            f.write(f"CAREER ARCHITECT | RATING: {rating}/10\n\n" + self.apply_friction(cv))
        with open(os.path.join(folder, "data.carf"), "w") as f:
            json.dump({"name": name, "cv": cv, "rating": rating, "v": self.version}, f)
            
        z_name = f"{folder}.zip"
        with zipfile.ZipFile(z_name, 'w') as zf:
            for root, _, files in os.walk(folder):
                for file in files: zf.write(os.path.join(root, file), file)
        return z_name
