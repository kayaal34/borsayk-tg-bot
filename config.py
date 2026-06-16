import os
import logging
from dotenv import load_dotenv
import pytz

# Bağlamdaki .env dosyasındaki değişkenleri yükle
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")

# Zaman dilimi yapılandırması
TZ_YEKATERINBURG = pytz.timezone("Asia/Yekaterinburg")

# Loglama yapılandırması - Terminal/Konsol takibi için
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger("FinBot")