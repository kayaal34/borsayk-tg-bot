# borsayk-tg-bot

Telegram bot that sends a daily market summary: exchange rates (TRY, RUB, CNY), gold and silver per gram, and BIST 100. It can also track your own portfolio and send its value in TL every day.

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

- 📊 Anlık Rapor: market summary right now
- 💼 Portföyüm: your portfolio's value right now
- ⚙️ Saat Ayarları: up to three daily report times (Asia/Yekaterinburg)
- ▶️ Başlat / ⏸️ Durdur: turn the scheduled reports on or off

### Portfolio

| Command | Example |
|---|---|
| `/ekle <asset> <amount>` | `/ekle altin 10` |
| `/cikar <asset> <amount>` | `/cikar usd 100` |
| `/sil <asset>` | `/sil fon:AFT` |
| `/fiyat <asset> <TL price>` | `/fiyat fon:AFT 2,3456` |
| `/portfoy` | |

Assets: `tl`, `altin` (gram), `gumus` (gram), `usd`, `eur`, `rub`, `hisse:KOD` (BIST stock in lots, e.g. `hisse:THYAO`), `fon:KOD` (fund units).

Gold, silver and currencies use the same prices as the daily report, and BIST stocks come from Yahoo Finance. These are market prices, so they differ a little from a bank's buy and sell rates. TEFAS does not accept automated requests, so enter fund prices with `/fiyat` and update them when you want.

When the portfolio is not empty, every scheduled report is followed by a second message with each holding's value, the total in TL and the change since the previous close.

## Tests

```bash
pip install pytest
python -m pytest -q
```
