import logging
from datetime import time
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import TELEGRAM_BOT_TOKEN, TARGET_CHAT_ID, TZ_YEKATERINBURG, logger
from data_fetcher import get_all_data
from formatter import format_daily_message, format_portfolio
from portfolio import add_holding, fetch_extra_prices, parse_amount, parse_asset, value_portfolio
from settings_manager import load_settings, save_settings
from keep_alive import keep_alive

# Saat sorma adımları
ASK_TIME_1, ASK_TIME_2, ASK_TIME_3 = range(3)

def get_main_menu():
    """Ekranın altında kalıcı olarak duran ana menü butonları."""
    keyboard = [
        ["📊 Anlık Rapor", "⚙️ Saat Ayarları"],
        ["💼 Portföyüm", "⏰ Aktif Saatleri Gör"],
        ["▶️ Başlat", "⏸️ Durdur"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def schedule_jobs(application: Application):
    settings = load_settings()
    job_queue = application.job_queue
    for job in job_queue.jobs():
        if job.name == "DailyReport":
            job.schedule_removal()

    if not settings.get("is_active", True):
        logger.info("Bot pasif durumda.")
        return

    for t_str in settings.get("notification_times", []):
        try:
            h, m = map(int, t_str.split(':'))
            t = time(hour=h, minute=m, tzinfo=TZ_YEKATERINBURG)
            job_queue.run_daily(send_daily_report, time=t, name="DailyReport")
        except Exception as e:
            logger.error(f"Saat hatası ({t_str}): {e}")

async def portfolio_message(market):
    settings = load_settings()
    holdings = settings.get("portfolio", {})
    extra = await fetch_extra_prices(holdings, settings.get("manual_prices", {}))
    return format_portfolio(value_portfolio(holdings, market, extra))

async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    if not TARGET_CHAT_ID: return
    try:
        data = await get_all_data()
        await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=format_daily_message(data), parse_mode="HTML")
        # Portföy girildiyse günlük değerini de ayrı mesaj olarak gönder
        if load_settings().get("portfolio"):
            text = await portfolio_message(data.get("Piyasa", {}))
            await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Gönderim hatası: {e}")

# --- SAAT AYARLAMA SOHBETİ ---
async def start_time_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_times'] = []
    await update.message.reply_text(
        "⚙️ <b>Saat Ayarlama Sihirbazı</b>\n\n"
        "1. Bildirim saati ne zaman olsun? (Örn: 09:00)\n"
        "<i>İstemiyorsanız 'gec' yazın.</i>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_TIME_1

async def handle_time_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() != 'gec': context.user_data['temp_times'].append(text)
    await update.message.reply_text("2. Bildirim saati? (İstemiyorsanız 'gec')", parse_mode="HTML")
    return ASK_TIME_2

async def handle_time_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() != 'gec': context.user_data['temp_times'].append(text)
    await update.message.reply_text("3. Bildirim saati? (İstemiyorsanız 'gec')", parse_mode="HTML")
    return ASK_TIME_3

async def handle_time_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() != 'gec': context.user_data['temp_times'].append(text)
    
    settings = load_settings()
    times = context.user_data['temp_times']
    if times:
        settings['notification_times'] = times
        save_settings(settings)
    
    schedule_jobs(context.application)
    saatler = ", ".join(times) if times else "Hiçbiri"
    await update.message.reply_text(f"✅ Kurulum tamamlandı!\n⏰ Aktif Saatler: {saatler}", reply_markup=get_main_menu())
    return ConversationHandler.END

async def cancel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("İşlem iptal edildi.", reply_markup=get_main_menu())
    return ConversationHandler.END

# --- MENÜ BUTONLARI ---
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hoş geldin! Alt menüden işlemini seçebilirsin.", reply_markup=get_main_menu())

async def btn_rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Veriler çekiliyor...")
    data = await get_all_data()
    await update.message.reply_text(format_daily_message(data), parse_mode="HTML")

async def btn_durdur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = load_settings()
    settings['is_active'] = False
    save_settings(settings)
    schedule_jobs(context.application)
    await update.message.reply_text("🛑 Otomatik bildirimler durduruldu.")

async def btn_baslat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = load_settings()
    settings['is_active'] = True
    save_settings(settings)
    schedule_jobs(context.application)
    await update.message.reply_text("🟢 Otomatik bildirimler başlatıldı.")

async def btn_saatleri_gor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = load_settings()
    times = settings.get("notification_times", [])
    durum = "🟢 Çalışıyor" if settings.get("is_active", True) else "🛑 Durduruldu"
    mesaj = f"⏰ <b>Kayıtlı Saatler:</b> {', '.join(times) if times else 'Yok'}\n🤖 <b>Durum:</b> {durum}"
    await update.message.reply_text(mesaj, parse_mode="HTML")

# --- PORTFÖY ---
async def btn_portfoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Portföy hesaplanıyor...")
    data = await get_all_data()
    await update.message.reply_text(await portfolio_message(data.get("Piyasa", {})), parse_mode="HTML")

async def change_holding(update: Update, context: ContextTypes.DEFAULT_TYPE, sign):
    if len(context.args) != 2:
        komut = "ekle" if sign > 0 else "cikar"
        await update.message.reply_text(
            f"Kullanım: /{komut} <varlık> <miktar>\n"
            "Varlıklar: tl, altin, gumus, usd, eur, rub, hisse:KOD, fon:KOD\n"
            f"Örnek: /{komut} altin 2,5")
        return
    try:
        key = parse_asset(context.args[0])
        amount = parse_amount(context.args[1])
        if amount <= 0:
            raise ValueError("Miktar sıfırdan büyük olmalı")
        settings = load_settings()
        holdings = dict(settings.get("portfolio", {}))
        add_holding(holdings, key, sign * amount)
    except ValueError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return
    settings["portfolio"] = holdings
    save_settings(settings)
    await update.message.reply_text(f"✅ Kaydedildi. {key}: {holdings.get(key, 0):g}")

async def cmd_ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await change_holding(update, context, 1)

async def cmd_cikar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await change_holding(update, context, -1)

async def cmd_sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Kullanım: /sil <varlık>  (ör. /sil fon:AFT)")
        return
    try:
        key = parse_asset(context.args[0])
    except ValueError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return
    settings = load_settings()
    holdings = dict(settings.get("portfolio", {}))
    if holdings.pop(key, None) is None:
        await update.message.reply_text(f"Portföyde {key} yok.")
        return
    settings["portfolio"] = holdings
    save_settings(settings)
    await update.message.reply_text(f"🗑️ {key} portföyden silindi.")

async def cmd_fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text(
            "Kullanım: /fiyat <varlık> <TL fiyatı>\n"
            "Fon fiyatları otomatik alınamıyor; TEFAS veya bankadaki fiyatı buraya yaz.\n"
            "Örnek: /fiyat fon:AFT 2,3456")
        return
    try:
        key = parse_asset(context.args[0])
        price = parse_amount(context.args[1])
        if price <= 0:
            raise ValueError("Fiyat sıfırdan büyük olmalı")
    except ValueError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return
    settings = load_settings()
    prices = dict(settings.get("manual_prices", {}))
    prices[key] = price
    settings["manual_prices"] = prices
    save_settings(settings)
    await update.message.reply_text(f"✅ {key} fiyatı {price:g} TL olarak kaydedildi.")

def main():
    if not TELEGRAM_BOT_TOKEN: return
    
    # Sunucu uyumasın diye sahte sunucuyu başlat
    keep_alive()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⚙️ Saat Ayarları$"), start_time_setup)],
        states={
            ASK_TIME_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_1)],
            ASK_TIME_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_2)],
            ASK_TIME_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_3)],
        },
        fallbacks=[CommandHandler("cancel", cancel_setup)]
    )
    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(MessageHandler(filters.Regex("^📊 Anlık Rapor$"), btn_rapor))
    application.add_handler(MessageHandler(filters.Regex("^▶️ Başlat$"), btn_baslat))
    application.add_handler(MessageHandler(filters.Regex("^⏸️ Durdur$"), btn_durdur))
    application.add_handler(MessageHandler(filters.Regex("^⏰ Aktif Saatleri Gör$"), btn_saatleri_gor))
    application.add_handler(MessageHandler(filters.Regex("^💼 Portföyüm$"), btn_portfoy))
    application.add_handler(CommandHandler("portfoy", btn_portfoy))
    application.add_handler(CommandHandler("ekle", cmd_ekle))
    application.add_handler(CommandHandler("cikar", cmd_cikar))
    application.add_handler(CommandHandler("sil", cmd_sil))
    application.add_handler(CommandHandler("fiyat", cmd_fiyat))

    schedule_jobs(application)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()