import asyncio

import pandas as pd
import pytest

import data_fetcher

CLOSES = {
    "TRY=X": [40.0, 41.0],
    "GC=F": [3000.0, 3110.35],
    "RUB=X": [80.0, 82.0],
    "CNY=X": [7.0, 7.1],
}


class FakeTicker:
    def __init__(self, closes):
        self.closes = closes

    def history(self, period):
        if self.closes is None:
            raise ConnectionError
        return pd.DataFrame({"Close": self.closes})


class FakeTickers:
    def __init__(self, symbols):
        self.tickers = {symbol: FakeTicker(CLOSES.get(symbol)) for symbol in symbols.split()}


@pytest.fixture
def results(monkeypatch):
    symbols = {
        "USD/TRY": "TRY=X",
        "Ons Altın": "GC=F",
        "USD/RUB": "RUB=X",
        "USD/CNY": "CNY=X",
        "BIST 100": "XU100.IS",
    }
    monkeypatch.setattr(data_fetcher, "load_settings", lambda: {"symbols": symbols})
    monkeypatch.setattr(data_fetcher.yf, "Tickers", FakeTickers)
    return asyncio.run(data_fetcher.fetch_yfinance_data())


def test_change_is_calculated_from_last_two_closes(results):
    assert results["USD/TRY"]["price"] == 41.0
    assert results["USD/TRY"]["change"] == pytest.approx(2.5)


def test_gram_gold_uses_ounce_and_dollar(results):
    assert results["Gram Altın"]["price"] == pytest.approx(100 * 41.0)


def test_cross_rates(results):
    assert results["TRY/RUB"]["price"] == pytest.approx(82.0 / 41.0)
    assert results["CNY/RUB"]["price"] == pytest.approx(82.0 / 7.1)


def test_failed_symbol_has_zero_price(results):
    assert results["BIST 100"] == {"price": 0.0, "change": 0.0}
