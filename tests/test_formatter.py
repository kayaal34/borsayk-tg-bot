from datetime import datetime

from formatter import format_change, format_daily_message, format_number, get_emoji

NOW = datetime(2026, 11, 8, 9, 0)


def test_emoji_follows_direction():
    assert get_emoji(1.5) == "📈"
    assert get_emoji(-1.5) == "📉"
    assert get_emoji(0) == "➖"


def test_numbers_use_turkish_separators():
    assert format_number(10500.5, 2) == "10.500,50"
    assert format_number(41.25, 4) == "41,2500"


def test_change_has_arrow():
    assert format_change(0.5) == "▲ %0,50"
    assert format_change(-1.2) == "▼ %1,20"
    assert format_change(0) == "• %0,00"


def test_message_lists_prices():
    message = format_daily_message({"Piyasa": {
        "USD/TRY": {"price": 41.25, "change": 0.5},
        "BIST 100": {"price": 10500.5, "change": -1.2},
    }}, now=NOW)

    assert "🇺🇸 <b>Dolar / TL</b>" in message
    assert "<code>41,2500</code>  📈 ▲ %0,50" in message
    assert "<code>10.500,50</code>  📉 ▼ %1,20" in message
    assert "08.11.2026 09:00" in message


def test_sections_without_data_are_hidden():
    message = format_daily_message({"Piyasa": {"USD/TRY": {"price": 41.0, "change": 0.0}}}, now=NOW)

    assert "Döviz Kurları" in message
    assert "Değerli Madenler" not in message
    assert "Borsa İstanbul" not in message


def test_failed_symbol_is_not_shown_as_zero():
    message = format_daily_message({"Piyasa": {"USD/TRY": {"price": 0.0, "change": 0.0}}}, now=NOW)

    assert "veri yok" in message
    assert "0,0000" not in message


def test_empty_data_says_so():
    assert "piyasa verisi alınamadı" in format_daily_message({}, now=NOW)
