import asyncio
import pytest

import portfolio
from formatter import format_portfolio

MARKET = {
    "Gram Altın": {"price": 4000.0, "change": 1.0},
    "USD/TRY": {"price": 40.0, "change": 0.0},
    "TRY/RUB": {"price": 2.0, "change": 0.0},
    "EUR/TRY": {"price": 0.0, "change": 0.0},
}


@pytest.mark.parametrize("text, key", [
    ("altin", "altin"),
    ("Altın", "altin"),
    ("dolar", "usd"),
    ("hisse:thyao", "hisse:THYAO"),
    ("fon:aft", "fon:AFT"),
])
def test_parse_asset(text, key):
    assert portfolio.parse_asset(text) == key


@pytest.mark.parametrize("text", ["bitcoin", "fon:", "hisse:A-B"])
def test_parse_asset_rejects_unknown(text):
    with pytest.raises(ValueError):
        portfolio.parse_asset(text)


def test_parse_amount_accepts_comma():
    assert portfolio.parse_amount("2,5") == 2.5


@pytest.mark.parametrize("text", ["nan", "inf", "abc"])
def test_parse_amount_rejects_bad_numbers(text):
    with pytest.raises(ValueError):
        portfolio.parse_amount(text)


def test_add_and_remove_holding():
    holdings = {}
    portfolio.add_holding(holdings, "altin", 10)
    portfolio.add_holding(holdings, "altin", 2.5)
    assert holdings == {"altin": 12.5}

    portfolio.add_holding(holdings, "altin", -12.5)
    assert holdings == {}


def test_cannot_remove_more_than_held():
    with pytest.raises(ValueError):
        portfolio.add_holding({"usd": 10}, "usd", -20)


def test_value_portfolio():
    holdings = {"altin": 10, "usd": 100, "tl": 500, "rub": 1000}

    result = portfolio.value_portfolio(holdings, MARKET)

    values = {row["key"]: row["value"] for row in result["rows"]}
    assert values == {"altin": 40000.0, "usd": 4000.0, "tl": 500.0, "rub": 500.0}
    assert result["total"] == pytest.approx(45000.0)
    # Sadece altın 1% yükseldi
    assert result["prev_total"] == pytest.approx(40000 / 1.01 + 5000)
    assert result["missing"] == []


def test_ruble_change_is_inverted():
    market = {"TRY/RUB": {"price": 2.0, "change": 25.0}}

    row = portfolio.value_portfolio({"rub": 1}, market)["rows"][0]

    # TL rubleye göre %25 değer kazandıysa ruble TL'ye göre %20 değer kaybetmiştir
    assert row["change"] == pytest.approx(-20.0)


def test_missing_prices_are_reported():
    holdings = {"eur": 50, "fon:AFT": 100, "hisse:THYAO": 5}
    extra = {"hisse:THYAO": {"price": 300.0, "change": -2.0}}

    result = portfolio.value_portfolio(holdings, MARKET, extra)

    assert result["total"] == pytest.approx(1500.0)
    assert sorted(result["missing"]) == ["eur", "fon:AFT"]


def test_format_portfolio():
    result = portfolio.value_portfolio({"altin": 10, "usd": 100}, MARKET)

    message = format_portfolio(result)

    assert "40.000,00 TL" in message
    assert "Toplam:</b> <code>44.000,00 TL</code>" in message
    assert "(+1.00%)" in message


def test_format_empty_portfolio_shows_help():
    message = format_portfolio(portfolio.value_portfolio({}, MARKET))

    assert "/ekle altin 10" in message


def test_format_mentions_missing():
    message = format_portfolio(portfolio.value_portfolio({"fon:AFT": 1}, {}))

    assert "fiyat alınamadı" in message


def test_manual_price_is_used():
    prices = asyncio.run(portfolio.fetch_extra_prices(
        {"fon:AFT": 1000}, {"fon:AFT": 2.5, "fon:TTE": 3.0}))

    assert prices == {"fon:AFT": {"price": 2.5, "change": 0.0, "manual": True}}

    result = portfolio.value_portfolio({"fon:AFT": 1000}, MARKET, prices)
    assert result["total"] == 2500.0
    assert "elle girilen fiyat" in format_portfolio(result)


def test_failed_stock_is_reported_missing(monkeypatch):
    class Broken:
        def __init__(self, symbols):
            raise ConnectionError

    monkeypatch.setattr(portfolio.yf, "Tickers", Broken)

    assert portfolio._stock_prices(["THYAO"]) == {}
