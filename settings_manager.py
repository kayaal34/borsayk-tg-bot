import json
import os

SETTINGS_FILE = 'user_settings.json'

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {
            "symbols": {
                "Ons Altın": "GC=F",
                "USD/TRY": "TRY=X",
                "EUR/TRY": "EURTRY=X",
                "TRY/RUB": "TRYRUB=X"
            },
            "tefas_funds": ["TI1", "MAC", "GMR"]
        }
    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)
