from langgraph.graph import StateGraph, START, END
from state import TradingState
from nodes import fetch_data_node

def build_graph():
  builder = StateGraph(TradingState)
  builder.add_node("fetch_data", fetch_data_node)
  builder.add_edge(START, "fetch_data")
  builder.add_edge("fetch_data", END)
  return builder.compile()