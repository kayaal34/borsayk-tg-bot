import json
import os

SETTINGS_FILE = 'user_settings.json'

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {
            "symbols": {
                "BIST 100": "XU100.IS",
                "Ons Altın": "GC=F",
                "Ons Gümüş": "SI=F",
                "USD/TRY": "TRY=X",
                "EUR/TRY": "EURTRY=X",
                "USD/RUB": "RUB=X",
                "USD/CNY": "CNY=X" # Çapraz kur için Dolar/Yuan paritesini alıyoruz
            },
            "notification_times": ["09:00", "18:00"], 
            "is_active": True
        }
    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)