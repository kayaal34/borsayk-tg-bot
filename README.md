# borsayk-tg-bot

Telegram bot that sends a daily market summary: exchange rates (TRY, RUB, CNY), gold and silver per gram, and BIST 100.

```
📊 Piyasa Özeti
🗓️ 08.11.2026 09:00

💱 Döviz Kurları
🇺🇸 Dolar / TL
      41,2500  📈 ▲ %0,50
🥇 Gram Altın
      4.250,10  📉 ▼ %0,32
```

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
TELEGRAM_BOT_TOKEN=...
TARGET_CHAT_ID=...
```

Run it with `python main.py`.

## Usage

The buttons at the bottom of the chat:

- 📊 Anlık Rapor: the summary right now
- ⚙️ Saat Ayarları: up to three daily report times, written as `09:00`, `9.00` or `0900` (Asia/Yekaterinburg)
- ⏰ Aktif Saatleri Gör: the saved times and whether reports are on
- ▶️ Başlat / ⏸️ Durdur: turn the scheduled reports on or off

Prices come from Yahoo Finance. Gram gold and silver are calculated from the ounce price and USD/TRY, so they differ a little from a bank's buy and sell rates.

## Tests

```bash
pip install pytest
python -m pytest -q
```
