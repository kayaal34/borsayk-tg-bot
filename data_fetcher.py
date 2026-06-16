import logging
import yfinance as yf
from settings_manager import load_settings

logger = logging.getLogger("FinBot.DataFetcher")

async def fetch_yfinance_data():
    settings = load_settings()
    symbols = settings.get("symbols", {})
    results = {}
    if not symbols: return results

    try:
        tickers = yf.Tickers(" ".join(symbols.values()))
        for name, ticker_sym in symbols.items():
            try:
                hist = tickers.tickers[ticker_sym].history(period="5d")
                if len(hist) >= 2:
                    current_price = float(hist['Close'].iloc[-1])
                    prev_price = float(hist['Close'].iloc[-2])
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    results[name] = {"price": current_price, "change": change_pct}
                else:
                    results[name] = {"price": 0.0, "change": 0.0}
            except Exception:
                results[name] = {"price": 0.0, "change": 0.0}

        usd_try_price = results.get("USD/TRY", {}).get("price", 0)
        usd_try_change = results.get("USD/TRY", {}).get("change", 0)
        usd_try_prev = usd_try_price / (1 + usd_try_change/100) if usd_try_change != 0 else usd_try_price

        # Altın Hesabı
        if "Ons Altın" in results and usd_try_price > 0:
            ons_au = results["Ons Altın"]["price"]
            ons_au_prev = ons_au / (1 + results["Ons Altın"]["change"]/100) if results["Ons Altın"]["change"] != 0 else ons_au
            gram_au = (ons_au / 31.1035) * usd_try_price
            gram_au_prev = (ons_au_prev / 31.1035) * usd_try_prev
            results["Gram Altın"] = {"price": gram_au, "change": ((gram_au - gram_au_prev) / gram_au_prev) * 100 if gram_au_prev else 0}

        # Gümüş Hesabı
        if "Ons Gümüş" in results and usd_try_price > 0:
            ons_ag = results["Ons Gümüş"]["price"]
            ons_ag_prev = ons_ag / (1 + results["Ons Gümüş"]["change"]/100) if results["Ons Gümüş"]["change"] != 0 else ons_ag
            gram_ag = (ons_ag / 31.1035) * usd_try_price
            gram_ag_prev = (ons_ag_prev / 31.1035) * usd_try_prev
            results["Gram Gümüş"] = {"price": gram_ag, "change": ((gram_ag - gram_ag_prev) / gram_ag_prev) * 100 if gram_ag_prev else 0}
            
        # Çapraz Kur Hesaplamaları (Ruble üzerinden)
        if "USD/RUB" in results and results["USD/RUB"]["price"] > 0:
            rub_price = results["USD/RUB"]["price"]
            rub_prev = rub_price / (1 + results["USD/RUB"]["change"]/100)

            # Hatasız TL/Ruble (TRY/RUB) Çapraz Kuru
            if "USD/TRY" in results and usd_try_price > 0:
                try_rub_price = rub_price / usd_try_price 
                try_rub_prev = rub_prev / usd_try_prev
                try_rub_change = ((try_rub_price - try_rub_prev) / try_rub_prev) * 100 if try_rub_prev else 0
                results["TRY/RUB"] = {"price": try_rub_price, "change": try_rub_change}

            # Hatasız Yuan/Ruble (CNY/RUB) Çapraz Kuru
            if "USD/CNY" in results and results["USD/CNY"]["price"] > 0:
                cny_price = results["USD/CNY"]["price"]
                cny_prev = cny_price / (1 + results["USD/CNY"]["change"]/100)
                
                cny_rub_price = rub_price / cny_price
                cny_rub_prev = rub_prev / cny_prev
                cny_rub_change = ((cny_rub_price - cny_rub_prev) / cny_rub_prev) * 100 if cny_rub_prev else 0
                results["CNY/RUB"] = {"price": cny_rub_price, "change": cny_rub_change}
            
    except Exception as e:
        logger.error(f"YFinance hata: {str(e)}")
    return results

async def get_all_data():
    yfinance_res = await fetch_yfinance_data()
    return {"Piyasa": yfinance_res}