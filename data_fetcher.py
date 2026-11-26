import ccxt
import pandas as pd

EXCHANGE_ID = "binance"

def get_exchange():
  return getattr(ccxt, EXCHANGE_ID)({"enableRateLimit": True})

def _rsi(close: pd.Series, n: int = 14) -> float:
  # RSI: > 70 overbought, < 30 oversold
  delta = close.diff()
  gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
  loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
  rs = gain.iloc[-1] / loss.iloc[-1]
  return float(100 - 100 / (1 + rs))

def fetch_market_data(symbol: str, timeframe: str = "1h", limit: int = 100) -> dict:
  ex = get_exchange()
  ticker = ex.fetch_ticker(symbol)
  candles = ex.fetch_ohlcv(symbol, timeframe, limit=limit)
  cols = ["ts", "open", "high", "low", "close", "volume"]
  df = pd.DataFrame(candles, columns=cols).iloc[:-1]  # Drop open candle
  close = df["close"]
  return {
    "symbol": symbol,
    "timeframe": timeframe,
    "price": ticker["last"],
    "change_24h_pct": ticker.get("percentage"),
    "sma_20": round(float(close.tail(20).mean()), 2),
    "sma_50": round(float(close.tail(50).mean()), 2),
    "rsi_14": round(_rsi(close), 1),
  }