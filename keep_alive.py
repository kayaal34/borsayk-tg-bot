from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Finans Botu 7/24 Calisiyor!"

def run():
    # Render'ın zorunlu kıldığı portu dinliyoruz
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # Botun çalışmasını durdurmamak için web sunucusunu ayrı bir kanalda (thread) başlatıyoruz
    t = Thread(target=run)
    t.start()