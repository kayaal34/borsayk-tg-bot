import asyncio
import logging
import yfinance as yf
import aiohttp
from bs4 import BeautifulSoup
from settings_manager import load_settings

logger = logging.getLogger("FinBot.DataFetcher")

async def fetch_yfinance_data():
    """Yfinance üzerinden döviz ve ons altın verilerini asenkron bir yapıda çeker."""
    settings = load_settings()
    symbols = settings.get("symbols", {})
    
    results = {}
    if not symbols:
        return results
    try:
        # yfinance çağrıları I/O engellemesini azaltmak için async içinde thread benzeri çalıştırılabilir
        # Ancak burada basitlik ve I/O uyumluluğu için mevcut haliyle kullanıyoruz.
        tickers = yf.Tickers(" ".join(symbols.values()))
        
        for name, ticker_sym in symbols.items():
            try:
                # Günlük değişimi hesaplamak için son 5 günlük verinin 2'sini alıyoruz
                hist = tickers.tickers[ticker_sym].history(period="5d")
                if len(hist) >= 2:
                    current_price = float(hist['Close'].iloc[-1])
                    prev_price = float(hist['Close'].iloc[-2])
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    results[name] = {
                        "price": current_price,
                        "change": change_pct
                    }
                else:
                    results[name] = {"price": 0.0, "change": 0.0}
            except Exception as e:
                logger.error(f"YFinance {name} çekilirken hata oluştu: {str(e)}")
                results[name] = {"price": 0.0, "change": 0.0}

        # Gram Altın Hesabı: (Ons / 31.1035) * USD/TRY
        if "Ons Altın" in results and "USD/TRY" in results:
            ons = results["Ons Altın"]["price"]
            usd = results["USD/TRY"]["price"]
            
            # Değişim oranlarından bir önceki günün fiyatlarını tahmin et
            ons_prev = ons / (1 + results["Ons Altın"]["change"]/100) if results["Ons Altın"]["change"] != 0 else ons
            usd_prev = usd / (1 + results["USD/TRY"]["change"]/100) if results["USD/TRY"]["change"] != 0 else usd
            
            gram_current = (ons / 31.1035) * usd
            gram_prev = (ons_prev / 31.1035) * usd_prev
            
            gram_change = ((gram_current - gram_prev) / gram_prev) * 100 if gram_prev != 0 else 0
            
            results["Gram Altın"] = {
                "price": gram_current,
                "change": gram_change
            }
            
    except Exception as e:
        logger.error(f"YFinance genel hata: {str(e)}")
        
    return results

async def fetch_tefas_fund(session, fund_code):
    """TEFAS üzerinden tek bir fonun fiyat ve günlük değişimini çeker."""
    url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fund_code}"
    
    # Gerçek bir tarayıcı gibi davranması için headers eklendi
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        async with session.get(url, headers=headers, timeout=15) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                # Fiyat ve değişim verilerini seç (TEFAS HTML yapısı)
                indicators = soup.select(".top-list > li > span")
                if len(indicators) >= 2:
                    price_str = indicators[0].text.replace(',', '.')
                    change_str = indicators[1].text.replace('%', '').replace(',', '.')
                    
                    return {
                        "price": float(price_str) if price_str.replace('.','',1).isdigit() else 0.0,
                        "change": float(change_str) if change_str.replace('-','').replace('.','',1).isdigit() else 0.0
                    }
    except Exception as e:
        logger.error(f"TEFAS {fund_code} çekilirken web scraping hatası: {str(e)}")
        
    return {"price": 0.0, "change": 0.0}

async def fetch_all_tefas():
    """Belirtilen tüm TEFAS fonlarını asenkron olarak çeker."""
    settings = load_settings()
    funds = settings.get("tefas_funds", [])
    results = {}
    
    if not funds:
        return results
    
    # Asenkron HTTP Session havuzu
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_tefas_fund(session, code) for code in funds]
        gathered = await asyncio.gather(*tasks)
        
        for code, data in zip(funds, gathered):
            results[code] = data
            
    return results

async def get_all_data():
    """Tüm dış veri kaynaklarını eşzamanlı çalıştırır."""
    yfinance_task = fetch_yfinance_data()
    tefas_task = fetch_all_tefas()
    
    # İki ayrı kaynağı aynı anda bekle
    yfinance_res, tefas_res = await asyncio.gather(yfinance_task, tefas_task)
    
    return {
        "Piyasa": yfinance_res,
        "Fonlar": tefas_res
    }