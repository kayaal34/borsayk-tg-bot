from formatter import format_daily_message, get_emoji


def test_emoji_follows_direction():
    assert get_emoji(1.5) == "🟢"
    assert get_emoji(-1.5) == "🔴"
    assert get_emoji(0) == "⚪"


def test_message_lists_prices():
    message = format_daily_message({"Piyasa": {
        "USD/TRY": {"price": 41.25, "change": 0.5},
        "BIST 100": {"price": 10500.5, "change": -1.2},
    }})

    assert "<code>41.2500</code>" in message
    assert "(+0.50%)" in message
    assert "<code>10,500.50</code>" in message
    assert "(-1.20%)" in message


def test_failed_symbol_is_not_shown_as_zero():
    message = format_daily_message({"Piyasa": {"USD/TRY": {"price": 0.0, "change": 0.0}}})

    assert "veri yok" in message
    assert "0.0000" not in message


def test_empty_data_keeps_headers():
    assert "Döviz Kurları" in format_daily_message({})
