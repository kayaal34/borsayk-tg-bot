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

def parse_time(text):
    """'9:00', '09.00' veya '0900' gibi girişleri '09:00' biçimine çevirir.

    Geçersiz saatlerde None döner.
    """
    text = text.strip().replace(".", ":")
    if ":" not in text and text.isdigit() and len(text) in (3, 4):
        text = f"{text[:-2]}:{text[-2:]}"
    parts = text.split(":")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        return None
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour < 24 and 0 <= minute < 60):
        return None
    return f"{hour:02d}:{minute:02d}"
