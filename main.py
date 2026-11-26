from pprint import pprint
from graph import build_graph

if __name__ == "__main__":
  app = build_graph()
  result = app.invoke({"symbol": "BTC/USDT", "timeframe": "1h"})
  pprint(result)