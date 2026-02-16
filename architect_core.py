import hashlib, json, os, requests, zipfile
from datetime import datetime, timedelta

class ArchitectCore:
    def __init__(self):
        self.version = "5.7.5"
        self.build_date = "2026-02-15"
        self.config_file = "system_config.json"
        self.registry_file = "client_registry.json"

    def get_hash(self, password):
        return hashlib.sha512(password.encode()).hexdigest()

    def run_purge_audit(self, test_days_offset=0):
        if not os.path.exists(self.registry_file): return {"status": "Complete", "purged": 0}
        with open(self.registry_file, 'r') as f: clients = json.load(f)
        sim_now = datetime.now() + timedelta(days=test_days_offset)
        keep = [c for c in clients if sim_now <= datetime.strptime(c['last_unlock'], '%Y-%m-%d') + timedelta(days=30)]
        with open(self.registry_file, 'w') as f: json.dump(keep, f, indent=4)
        return {"status": "Complete", "purged": len(clients) - len(keep), "date": sim_now.strftime('%Y-%m-%d')}

    def apply_friction(self, text):
        f_map = {"a": "а", "e": "е", "o": "о", "p": "р"}
        for eng, cyr in f_map.items(): text = text.replace(eng, cyr)
        return text

    def create_bundle(self, name, cv):
        folder = f"Output_{name.replace(' ', '_')}"
        if not os.path.exists(folder): os.makedirs(folder)
        with open(os.path.join(folder, f"{name}_CV.txt"), 'w', encoding='utf-8') as f:
            f.write(f"CAREER ARCHITECT PROTECTED DOCUMENT\n\n{self.apply_friction(cv)}")
        with open(os.path.join(folder, f"{name}.carf"), 'w') as f:
            json.dump({"name": name, "cv": cv, "v": self.version}, f)
        z_path = f"{folder}.zip"
        with zipfile.ZipFile(z_path, 'w') as zf:
            for root, dirs, files in os.walk(folder):
                for file in files: zf.write(os.path.join(root, file), file)
        return z_path

    def fetch_jobs(self, title, loc="London"):
        if not os.path.exists(self.config_file): return []
        with open(self.config_file, 'r') as f: cfg = json.load(f)
        p = {"app_id": cfg['admin_settings']['api_keys']['adzuna_id'], 
             "app_key": cfg['admin_settings']['api_keys']['adzuna_key'], 
             "what": title, "where": loc, "content-type": "application/json"}
        try:
            r = requests.get("https://api.adzuna.com/v1/api/jobs/gb/search/1", params=p)
            return r.json().get('results', [])
        except: return []
