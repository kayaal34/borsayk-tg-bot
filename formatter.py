from portfolio import describe


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

def _tl(value):
    # 12,345.67 -> 12.345,67 (Türkçe yazım)
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _amount(value):
    text = f"{value:,.4f}".rstrip("0").rstrip(".")
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def format_portfolio(valuation):
    html = "<b>💼 Portföyüm</b>\n\n"
    if not valuation["rows"] and not valuation["missing"]:
        return html + ("Portföyün boş. Eklemek için örnek:\n"
                       "<code>/ekle altin 10</code>\n<code>/ekle usd 500</code>\n"
                       "<code>/ekle hisse:THYAO 20</code>\n<code>/ekle fon:AFT 1500</code>")

    for row in valuation["rows"]:
        label, unit = describe(row["key"])
        change = "elle girilen fiyat" if row["manual"] else f"{row['change']:+.2f}%"
        html += (f"{get_emoji(row['change'])} <b>{label}</b>: {_amount(row['amount'])} {unit}"
                 f" = <code>{_tl(row['value'])} TL</code> <i>({change})</i>\n")
    for key in valuation["missing"]:
        label, unit = describe(key)
        hint = f" (/fiyat {key} &lt;fiyat&gt;)" if key.startswith("fon:") else ""
        html += f"⚪ <b>{label}</b>: <i>fiyat alınamadı{hint}</i>\n"

    total, prev = valuation["total"], valuation["prev_total"]
    diff = total - prev
    pct = diff / prev * 100 if prev else 0.0
    html += (f"\n<b>Toplam:</b> <code>{_tl(total)} TL</code>\n"
             f"{get_emoji(pct)} Günlük: <code>{'+' if diff >= 0 else '-'}{_tl(abs(diff))} TL</code>"
             f" <i>({pct:+.2f}%)</i>\n")
    if valuation["missing"]:
        html += "<i>Fiyatı alınamayan varlıklar toplama dahil değil.</i>\n"
    return html
