"""M1 tests: State + CCXT data fetch + first graph.

Everything is offline (CCXT is faked), so tests are fast and repeatable.
One optional live test:  pytest -m live
"""
from typing import get_type_hints

import ccxt
import pytest

import data_fetcher
import nodes
from graph import build_graph
from state import TradingState


# ---------- helpers ----------
class FakeExchange:
    """Stands in for ccxt: no internet, fully predictable."""

    def __init__(self, closes):
        self.closes = closes

    def fetch_ticker(self, symbol):
        return {"last": 123.45, "percentage": 1.5}

    def fetch_ohlcv(self, symbol, timeframe, limit=100):
        return [[i, c, c, c, c, 10.0] for i, c in enumerate(self.closes)]


def zigzag(n=60):
    """100, 102, 100, 102 ... → SMA is exactly 101.0 and RSI is defined."""
    return [100.0 + 2 * (i % 2) for i in range(n)]


@pytest.fixture
def use_fake_exchange(monkeypatch):
    def _install(closes):
        monkeypatch.setattr(data_fetcher, "get_exchange",
                            lambda: FakeExchange(closes))
    return _install


INPUT = {"symbol": "BTC/USDT", "timeframe": "1h"}


# ---------- State ----------
def test_state_has_core_keys():
    keys = get_type_hints(TradingState)
    for k in ("symbol", "timeframe", "market_data", "signal", "error"):
        assert k in keys


# ---------- data_fetcher ----------
def test_fetch_market_data_values(use_fake_exchange):
    use_fake_exchange(zigzag())
    data = data_fetcher.fetch_market_data("BTC/USDT", "1h")
    assert data["symbol"] == "BTC/USDT"
    assert data["price"] == 123.45          # comes from fetch_ticker
    assert data["change_24h_pct"] == 1.5
    assert data["sma_20"] == 101.0
    assert data["sma_50"] == 101.0
    assert 0 < data["rsi_14"] < 100


def test_open_candle_is_dropped(use_fake_exchange):
    closes = zigzag()
    closes[-1] = 1_000_000.0                # fake "still forming" candle
    use_fake_exchange(closes)
    data = data_fetcher.fetch_market_data("BTC/USDT", "1h")
    assert data["sma_20"] == 101.0          # outlier was ignored


def test_rsi_edge_cases(use_fake_exchange):
    use_fake_exchange([100.0] * 60)         # flat → no gains, no losses
    assert data_fetcher.fetch_market_data("BTC/USDT")["rsi_14"] == 50.0
    use_fake_exchange([float(i) for i in range(1, 61)])  # only rising
    assert data_fetcher.fetch_market_data("BTC/USDT")["rsi_14"] == 100.0


# ---------- node ----------
def test_fetch_data_node_success(monkeypatch):
    monkeypatch.setattr(nodes, "fetch_market_data",
                        lambda symbol, timeframe: {"price": 1.0})
    out = nodes.fetch_data_node(INPUT)
    assert out == {"market_data": {"price": 1.0}, "error": None}


def test_fetch_data_node_catches_ccxt_error(monkeypatch):
    def boom(symbol, timeframe):
        raise ccxt.NetworkError("no internet")
    monkeypatch.setattr(nodes, "fetch_market_data", boom)
    out = nodes.fetch_data_node(INPUT)      # must not raise
    assert "Data fetch failed" in out["error"]
    assert "market_data" not in out


# ---------- graph ----------
def test_graph_happy_path(monkeypatch):
    monkeypatch.setattr(nodes, "fetch_market_data",
                        lambda symbol, timeframe: {"price": 1.0})
    result = build_graph().invoke({"symbol": "ETH/USDT", "timeframe": "4h"})
    assert result["symbol"] == "ETH/USDT"   # input stays in state
    assert result["market_data"] == {"price": 1.0}
    assert result["error"] is None


def test_graph_error_path(monkeypatch):
    def boom(symbol, timeframe):
        raise ccxt.ExchangeError("maintenance")
    monkeypatch.setattr(nodes, "fetch_market_data", boom)
    result = build_graph().invoke(INPUT)
    assert "Data fetch failed" in result["error"]
    assert "market_data" not in result


# ---------- live (skipped by default) ----------
@pytest.mark.live
def test_live_exchange_smoke():
    data = data_fetcher.fetch_market_data("BTC/USDT", "1h")
    assert data["price"] > 0
    assert 0 <= data["rsi_14"] <= 100