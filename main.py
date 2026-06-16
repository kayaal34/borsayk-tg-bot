import logging
from datetime import time
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import TELEGRAM_BOT_TOKEN, TARGET_CHAT_ID, TZ_YEKATERINBURG, logger
from data_fetcher import get_all_data
from formatter import format_daily_message
from settings_manager import load_settings, save_settings
from keep_alive import keep_alive

# Saat sorma adımları
ASK_TIME_1, ASK_TIME_2, ASK_TIME_3 = range(3)

def get_main_menu():
    """Ekranın altında kalıcı olarak duran ana menü butonları."""
    keyboard = [
        ["📊 Anlık Rapor", "⚙️ Saat Ayarları"],
        ["⏰ Aktif Saatleri Gör"],
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

async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    if not TARGET_CHAT_ID: return
    try:
        data = await get_all_data()
        await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=format_daily_message(data), parse_mode="HTML")
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

    schedule_jobs(application)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()