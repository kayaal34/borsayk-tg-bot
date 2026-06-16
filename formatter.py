def get_emoji(change_pct):
    """Değişim oranına göre yeşil, kırmızı veya gri (nötr) emoji döndürür."""
    if change_pct > 0.01:
        return "🟢"
    elif change_pct < -0.01:
        return "🔴"
    return "⚪"

def format_daily_message(data):
    """
    Ham finansal verileri alıp, Telegram'ın HTML Parse Mode'u ile 
    uyumlu şık ve minimalist bir string'e çevirir.
    """
    
    html = "<b>🌟 Günlük Finansal Özet</b>\n\n"
    
    html += "<b>📊 Döviz ve Emtia</b>\n"
    piyasa = data.get("Piyasa", {})
    
    # Kurların ve altının sıralaması
    order = ["USD/TRY", "EUR/TRY", "RUB/TRY", "Ons Altın", "Gram Altın"]
    for sym in order:
        if sym in piyasa:
            item = piyasa[sym]
            price = item['price']
            change = item['change']
            emoji = get_emoji(change)
            
            # Kurların formatlaması farklı (Dövizde 4 basamak, Altında 2 basamak idealdir)
            price_str = f"{price:,.4f}" if "TRY" in sym else f"{price:,.2f}"
            change_str = f"{change:+.2f}%"
            html += f"{emoji} <b>{sym: <10}</b> {price_str} <i>({change_str})</i>\n"
            
    html += "\n<b>📈 TEFAS Yatırım Fonları</b>\n"
    fonlar = data.get("Fonlar", {})
    
    for code, item in fonlar.items():
        price = item['price']
        change = item['change']
        emoji = get_emoji(change)
        
        # Fonlar genellikle ondalık kısmı yoğun değerlere sahiptir
        price_str = f"{price:,.6f}"
        change_str = f"{change:+.2f}%"
        html += f"{emoji} <b>{code: <10}</b> {price_str} <i>({change_str})</i>\n"
        
    html += "\n<i>⌚ Asia/Yekaterinburg zaman dilimine göre hazırlanmıştır.</i>"
    
    return html