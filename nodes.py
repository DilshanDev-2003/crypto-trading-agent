import ccxt
from state import TradingState
from data_fetcher import fetch_market_data

def fetch_data_node(state: TradingState) -> dict:
  """Node 1: get live market data."""
  try:
    data = fetch_market_data(state["symbol"], state["timeframe"])
    return {"market_data": data, "error": None}
  except ccxt.BaseError as e: # Network exchange problems
    return {"error": f"Data fetch failed: {e}"}