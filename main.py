import logging
from datetime import time
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

# Modüllerin İçeri Aktarılması
from config import TELEGRAM_BOT_TOKEN, TARGET_CHAT_ID, TZ_YEKATERINBURG, logger
from data_fetcher import get_all_data
from formatter import format_daily_message
from settings_manager import load_settings, save_settings

ASK_SYMBOLS, ASK_FUNDS = range(2)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başlatıldığında ayarları yapmak için kullanılır."""
    await update.message.reply_text(
        "Merhaba! Ben Finans Raporu botuyum.\n"
        "Her gün sana düzenli veriler sunabilirim.\n\n"
        "Öncelikle hangi değerli madenlerin, döviz kurlarının veya hisselerin bilgisini almak istersiniz?\n"
        "(Örn: Ons Altın:GC=F, Dolar:TRY=X, Apple:AAPL)\n"
        "Lütfen [İsim:Sembol] formatında virgülle ayırarak yazın veya varsayılanları kullanmak için 'gec' yazın:"
    )
    return ASK_SYMBOLS

async def handle_symbols(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    settings = load_settings()
    
    if text.lower() != 'gec':
        new_symbols = {}
        try:
            items = text.split(',')
            for item in items:
                name, symbol = item.split(':')
                new_symbols[name.strip()] = symbol.strip()
            settings['symbols'] = new_symbols
            save_settings(settings)
            await update.message.reply_text("Semboller başarıyla güncellendi!")
        except Exception as e:
            await update.message.reply_text("Hatalı format! Lütfen 'İsim:Sembol, İsim2:Sembol2' formatında girin. Değiştirmeden geçmek için 'gec' yazabilirsiniz.")
            return ASK_SYMBOLS
            
    await update.message.reply_text(
        "Harika! Peki takip etmek istediğiniz TEFAS fonları var mı?\n"
        "Sadece fon kodlarını virgülle ayırarak yazın (Örn: TI1, MAC, GMR)\n"
        "Veya varsayılanları korumak için 'gec' yazın:"
    )
    return ASK_FUNDS

async def handle_funds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    settings = load_settings()
    
    if text.lower() != 'gec':
        funds = [f.strip().upper() for f in text.split(',')]
        settings['tefas_funds'] = funds
        save_settings(settings)
        
    await update.message.reply_text("Kurulum tamamlandı! /rapor yazarak anlık veriyi alabilirsin.")
    return ConversationHandler.END

async def cancel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kurulum iptal edildi.")
    return ConversationHandler.END

async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    """Zamanlanmış görev olarak çalışan ve kanala/kullanıcıya asıl veriyi yollayan fonksiyon."""
    if not TARGET_CHAT_ID:
        logger.error("TARGET_CHAT_ID ortam değişkeni bulunamadı. Mesaj gönderilemez.")
        return

    logger.info("Zamanlanmış günlük rapor hazırlanıyor...")
    try:
        data = await get_all_data()
        message = format_daily_message(data)
        
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=message,
            parse_mode="HTML"
        )
        logger.info("Rapor başarıyla gönderildi.")
    except Exception as e:
        logger.error(f"Rapor gönderimi sırasında beklenmeyen bir hata oluştu: {str(e)}")

async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Test amaçlı veya anlık kontrol için manual tetikleme komutu (/rapor).
    Bu komut her çağırıldığında canlı verileri çeker.
    """
    await update.message.reply_text("Güncel veriler sunuculardan çekiliyor, lütfen bekleyin...")
    
    try:
        data = await get_all_data()
        message = format_daily_message(data)
        
        await update.message.reply_text(
            text=message,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Manual komut (/rapor) hatası: {str(e)}")
        await update.message.reply_text("Veriler çekilirken bir hata ile karşılaşıldı. Lütfen daha sonra tekrar deneyin.")

def main():
    """Uygulamanın giriş noktası. Botu ve zamanlanmış görevleri konfigüre eder."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN bulunamadı. Lütfen .env dosyasını kontrol edin.")
        return

    logger.info("Finans Botu başlatılıyor...")
    
    # Yeni v20+ asenkron uygulama yapısı
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Kurulum sohbeti (Conversation Handler)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            ASK_SYMBOLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_symbols)],
            ASK_FUNDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_funds)],
        },
        fallbacks=[CommandHandler("cancel", cancel_setup)]
    )
    application.add_handler(conv_handler)

    # Manuel tetikleyici komutu opsiyonel olarak ekliyoruz
    application.add_handler(CommandHandler("rapor", cmd_report))

    # JobQueue yapısını kurma
    job_queue = application.job_queue
    
    # 1. Görev: Sabah 09:00
    time_morning = time(hour=9, minute=0, tzinfo=TZ_YEKATERINBURG)
    job_queue.run_daily(send_daily_report, time=time_morning, name="MorningReport")
    
    # 2. Görev: Akşam 18:00
    time_evening = time(hour=18, minute=0, tzinfo=TZ_YEKATERINBURG)
    job_queue.run_daily(send_daily_report, time=time_evening, name="EveningReport")

    logger.info(f"Zamanlanmış görevler kuruldu: Günlük 09:00 ve 18:00 (Timezone: {TZ_YEKATERINBURG}).")

    # Botun sürekli dinleme (polling) döngüsünü başlat
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()