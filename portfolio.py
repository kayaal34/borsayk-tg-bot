"""Portföy: kullanıcının elindeki varlıklar ve TL karşılıkları.

Varlıklar ayarlarda {"altin": 12.5, "hisse:THYAO": 20, "fon:AFT": 1500}
şeklinde tutulur. Fiyatlar raporda kullanılan piyasa verisinden gelir;
BIST hisseleri ayrıca Yahoo Finance'ten çekilir. TEFAS otomatik isteklere
izin vermediği için fon fiyatları kullanıcı tarafından /fiyat ile girilir.
"""
import asyncio
import logging
import yfinance as yf

logger = logging.getLogger("FinBot.Portfolio")

# kısa ad -> (görünen ad, piyasa verisindeki anahtar, birim)
BASIC_ASSETS = {
    "tl": ("Türk Lirası", None, "TL"),
    "altin": ("Gram Altın", "Gram Altın", "gr"),
    "gumus": ("Gram Gümüş", "Gram Gümüş", "gr"),
    "usd": ("Dolar", "USD/TRY", "$"),
    "eur": ("Euro", "EUR/TRY", "€"),
    "rub": ("Ruble", "TRY/RUB", "₽"),
}

ALIASES = {
    "altın": "altin", "gram": "altin", "gümüş": "gumus",
    "dolar": "usd", "euro": "eur", "ruble": "rub", "lira": "tl", "try": "tl",
}

def parse_asset(text):
    """Kullanıcının yazdığı varlık adını ayarlardaki anahtara çevirir.

    "altın" -> "altin", "thyao" hissesi için "hisse:THYAO", fon için "fon:AFT".
    Tanınmayan adlarda ValueError fırlatır.
    """
    text = text.strip().lower()
    for prefix in ("hisse:", "fon:"):
        if text.startswith(prefix):
            code = text[len(prefix):].strip().upper()
            if not code.isalnum():
                raise ValueError(f"Geçersiz kod: {code or '(boş)'}")
            return prefix + code
    text = ALIASES.get(text, text)
    if text in BASIC_ASSETS:
        return text
    raise ValueError(f"Bilinmeyen varlık: {text}")


def parse_amount(text):
    """'12,5' veya '12.5' gibi miktarları sayıya çevirir."""
    amount = float(text.replace(",", "."))
    if amount != amount or amount in (float("inf"), float("-inf")):
        raise ValueError("Geçersiz miktar")
    return amount


def add_holding(holdings, key, amount):
    """Miktarı ekler (eksi miktar azaltır). Sıfıra inen varlık silinir."""
    new_amount = round(holdings.get(key, 0) + amount, 6)
    if new_amount < 0:
        raise ValueError("Elindekinden fazlasını çıkaramazsın")
    if new_amount == 0:
        holdings.pop(key, None)
    else:
        holdings[key] = new_amount
    return holdings


def describe(key):
    """(görünen ad, birim) döndürür."""
    if key.startswith("hisse:"):
        return key[6:], "lot"
    if key.startswith("fon:"):
        return f"{key[4:]} fonu", "pay"
    label, _, unit = BASIC_ASSETS[key]
    return label, unit


def _stock_prices(codes):
    prices = {}
    if not codes:
        return prices
    symbols = {code: f"{code}.IS" for code in codes}
    try:
        tickers = yf.Tickers(" ".join(symbols.values()))
    except Exception as e:
        logger.warning(f"Hisse fiyatları alınamadı: {e}")
        return prices
    for code, symbol in symbols.items():
        try:
            hist = tickers.tickers[symbol].history(period="5d")
            closes = hist["Close"].dropna()
            if len(closes) >= 2:
                price, prev = float(closes.iloc[-1]), float(closes.iloc[-2])
                prices[f"hisse:{code}"] = {"price": price, "change": (price - prev) / prev * 100}
        except Exception as e:
            logger.warning(f"{code} hissesi alınamadı: {e}")
    return prices


async def fetch_extra_prices(holdings, manual_prices=None):
    """Piyasa raporunda olmayan hisse fiyatlarını çeker.

    Elle girilen fiyatlar (ör. fonlar) değişimsiz olarak eklenir; aynı
    varlığın canlı fiyatı varsa canlı fiyat kullanılır.
    """
    prices = {key: {"price": price, "change": 0.0, "manual": True}
              for key, price in (manual_prices or {}).items() if key in holdings}
    stocks = [key[6:] for key in holdings if key.startswith("hisse:")]
    if stocks:
        prices.update(await asyncio.to_thread(_stock_prices, stocks))
    return prices


def _unit_price(key, market, extra):
    """Varlığın 1 biriminin TL fiyatı ve günlük değişimi; veri yoksa None."""
    if key == "tl":
        return 1.0, 0.0
    if key in extra:
        item = extra[key]
    else:
        market_key = BASIC_ASSETS.get(key, (None, None))[1]
        item = market.get(market_key)
    if not item or not item.get("price"):
        return None
    price, change = item["price"], item.get("change", 0.0)
    if key == "rub":
        # TRY/RUB 1 TL'nin kaç ruble olduğunu verir; 1 rublenin TL değeri tersidir
        price = 1 / price
        change = (1 / (1 + change / 100) - 1) * 100
    return price, change


def value_portfolio(holdings, market, extra=None):
    """Her varlığın TL değerini ve toplamı hesaplar.

    Dönen sözlük: rows (varlık satırları), total, prev_total, missing
    (fiyatı bulunamayan varlıklar).
    """
    extra = extra or {}
    rows, missing = [], []
    total = prev_total = 0.0
    for key, amount in holdings.items():
        priced = _unit_price(key, market, extra)
        if priced is None:
            missing.append(key)
            continue
        price, change = priced
        value = amount * price
        prev_value = value / (1 + change / 100) if change > -100 else value
        rows.append({"key": key, "amount": amount, "price": price,
                     "value": value, "change": change,
                     "manual": extra.get(key, {}).get("manual", False)})
        total += value
        prev_total += prev_value
    rows.sort(key=lambda row: row["value"], reverse=True)
    return {"rows": rows, "total": total, "prev_total": prev_total, "missing": missing}
