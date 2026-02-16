# VERSION 7.5.0 | CAREER ARCHITECT CORE | SECURITY: SHA-512
import hashlib, json, os, zipfile
from datetime import datetime, timedelta

class ArchitectCore:
    def __init__(self):
        self.version = "7.5.0"
        self.registry = "client_registry.json"

    def get_hash(self, text):
        return hashlib.sha512(text.encode()).hexdigest()

    def apply_friction(self, text):
        mapping = {"a": "а", "e": "е", "o": "о", "p": "р"}
        for eng, cyr in mapping.items():
            text = text.replace(eng, cyr)
        return text

    def create_bundle(self, name, cv, rating):
        folder = f"CA_{name.replace(' ', '_')}"
        if not os.path.exists(folder): os.makedirs(folder)
        
        # 1. The Protected TXT
        with open(os.path.join(folder, "Protected_CV.txt"), "w", encoding="utf-8") as f:
            f.write(f"CAREER ARCHITECT | RATING: {rating}/10\n\n" + self.apply_friction(cv))
        
        # 2. The CARF Data File
        with open(os.path.join(folder, "data.carf"), "w") as f:
            json.dump({"name": name, "cv": cv, "rating": rating, "v": self.version}, f)
            
        # 3. ZIP it
        z_name = f"{folder}.zip"
        with zipfile.ZipFile(z_name, 'w') as zf:
            for root, _, files in os.walk(folder):
                for file in files: zf.write(os.path.join(root, file), file)
        return z_name
