from datetime import datetime

# sembol -> (emoji, görünen ad, ondalık basamak)
KURLAR = {
    "USD/TRY": ("🇺🇸", "Dolar / TL", 4),
    "EUR/TRY": ("🇪🇺", "Euro / TL", 4),
    "TRY/RUB": ("🇹🇷", "TL / Ruble", 4),
    "USD/RUB": ("🇷🇺", "Dolar / Ruble", 4),
    "CNY/RUB": ("🇨🇳", "Yuan / Ruble", 4),
}

MADENLER = {
    "Gram Altın": ("🥇", "Gram Altın", 2),
    "Ons Altın": ("🏅", "Ons Altın ($)", 2),
    "Gram Gümüş": ("🥈", "Gram Gümüş", 2),
}

BORSA = {
    "BIST 100": ("🏛️", "BIST 100", 2),
}


def get_emoji(change_pct):
    if change_pct > 0.01: return "📈"
    elif change_pct < -0.01: return "📉"
    return "➖"


def format_number(value, decimals):
    # 10,500.50 -> 10.500,50 (Türkçe yazım)
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def format_change(change_pct):
    arrow = "▲" if change_pct > 0.01 else "▼" if change_pct < -0.01 else "•"
    return f"{arrow} %{format_number(abs(change_pct), 2)}"


def format_line(emoji, label, item, decimals):
    # data_fetcher, veri alamadığı sembolleri 0 fiyatla döndürür
    if not item['price']:
        return f"{emoji} <b>{label}</b>\n      ⚠️ <i>veri yok</i>\n"
    return (f"{emoji} <b>{label}</b>\n"
            f"      <code>{format_number(item['price'], decimals)}</code>"
            f"  {get_emoji(item['change'])} {format_change(item['change'])}\n")


def format_section(title, rows, piyasa):
    lines = [format_line(emoji, label, piyasa[sym], decimals)
             for sym, (emoji, label, decimals) in rows.items() if sym in piyasa]
    if not lines:
        return ""
    return f"<b>{title}</b>\n" + "".join(lines) + "\n"


def format_daily_message(data, now=None):
    now = now or datetime.now()
    piyasa = data.get("Piyasa", {})
    html = f"<b>📊 Piyasa Özeti</b>\n🗓️ <i>{now:%d.%m.%Y %H:%M}</i>\n\n"
    body = (format_section("💱 Döviz Kurları", KURLAR, piyasa)
            + format_section("🪙 Değerli Madenler", MADENLER, piyasa)
            + format_section("📈 Borsa İstanbul", BORSA, piyasa))
    if not body:
        return html + "⚠️ <i>Şu an piyasa verisi alınamadı, biraz sonra tekrar dene.</i>"
    return html + body.rstrip("\n")
