def get_emoji(change_pct):
    if change_pct > 0.01: return "🟢"
    elif change_pct < -0.01: return "🔴"
    return "⚪"

def format_line(label, item, decimals):
    # data_fetcher, veri alamadığı sembolleri 0 fiyatla döndürür
    if not item['price']:
        return f"⚪ <b>{label}</b>: <i>veri yok</i>\n"
    return f"{get_emoji(item['change'])} <b>{label}</b>: <code>{item['price']:,.{decimals}f}</code> <i>({item['change']:+.2f}%)</i>\n"

def format_daily_message(data):
    html = "<b>🌟 Finansal Piyasa Özeti</b>\n\n"
    piyasa = data.get("Piyasa", {})
    
    # Döviz Kurları
    html += "<b>💵 Döviz Kurları</b>\n"
    kurlar = {
        "TRY/RUB": "TL to Ruble",
        "USD/TRY": "Dolar to TL",
        "EUR/TRY": "Euro to TL",
        "USD/RUB": "Dolar to Ruble",
        "CNY/RUB": "Yuan to Ruble"
    }
    for sym, isim in kurlar.items():
        if sym in piyasa:
            html += format_line(f"{isim: <15}", piyasa[sym], 4)

    # Emtia
    html += "\n<b>🪙 Değerli Madenler</b>\n"
    for sym in ["Gram Altın", "Gram Gümüş", "Ons Altın"]:
        if sym in piyasa:
            html += format_line(f"{sym: <15}", piyasa[sym], 2)

    # Borsa
    html += "\n<b>📈 Borsa (Endeks)</b>\n"
    if "BIST 100" in piyasa:
        html += format_line("BIST 100", piyasa["BIST 100"], 2)
        
    return html