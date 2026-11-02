import copy
import json
import os

SETTINGS_FILE = 'user_settings.json'

DEFAULT_SETTINGS = {
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

def load_settings():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            saved = json.load(f)
    except (OSError, ValueError):
        # Dosya yoksa veya bozuksa bot varsayılanlarla çalışmaya devam eder
        return settings
    if isinstance(saved, dict):
        settings.update(saved)
    return settings

def save_settings(settings):
    # Önce geçici dosyaya yazıyoruz; yarıda kalan yazma ayarları bozmasın
    temp_file = SETTINGS_FILE + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)
    os.replace(temp_file, SETTINGS_FILE)