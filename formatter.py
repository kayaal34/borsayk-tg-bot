def get_emoji(change_pct):
    if change_pct > 0.01: return "🟢"
    elif change_pct < -0.01: return "🔴"
    return "⚪"

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
            item = piyasa[sym]
            html += f"{get_emoji(item['change'])} <b>{isim: <15}</b>: <code>{item['price']:,.4f}</code> <i>({item['change']:+.2f}%)</i>\n"

    # Emtia
    html += "\n<b>🪙 Değerli Madenler</b>\n"
    for sym in ["Gram Altın", "Gram Gümüş", "Ons Altın"]:
        if sym in piyasa:
            item = piyasa[sym]
            html += f"{get_emoji(item['change'])} <b>{sym: <15}</b>: <code>{item['price']:,.2f}</code> <i>({item['change']:+.2f}%)</i>\n"

    # Borsa
    html += "\n<b>📈 Borsa (Endeks)</b>\n"
    if "BIST 100" in piyasa:
        item = piyasa["BIST 100"]
        html += f"{get_emoji(item['change'])} <b>BIST 100</b>: <code>{item['price']:,.2f}</code> <i>({item['change']:+.2f}%)</i>\n"
        
    return html