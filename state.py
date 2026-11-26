from typing import Optional, TypedDict

class TradingState(TypedDict, total=False):
  # Input
  symbol: str                 # "BTC/USDT"
  timeframe: str              # "1h"
  # M1 - Data
  market_data: dict           # summary from CCXT
  # M2 - AI Analyst
  signal: str                 # "BUY" | "SELL" | "HOLD"
  confidence: float           # 0.0 – 1.0
  reasoning: str              # shown to the human
  # M3/M4 - execution
  approved: Optional[bool]
  order_result: dict
  # Errors
  error: Optional[str]