import requests
import streamlit as st
import plotly.express as px
from data.sd_endpoints import StockDioUtils
from datetime import datetime
from data.sd_maps import HistoricalPrices, IndexHistoricalPrices
import pandas as pd

POLYGON_KEY = st.secrets["polygon_key"]
loader = StockDioUtils(app_key=st.secrets["sd_key"])

@st.cache_data(show_spinner=True)
def fetch_data(ticker: str):
    data: HistoricalPrices = loader.get_historical_prices(ticker, from_date="2020-01-01", to_date=datetime.now().strftime("%Y-%m-%d"))
    df = pd.DataFrame(data.prices, columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return {"name": data.company, "history": df}

def fetch_index_data(index: str):
    data: IndexHistoricalPrices = loader.get_index_historical_prices(index, from_date="2020-01-01", to_date=datetime.now().strftime("%Y-%m-%d"))
    df = pd.DataFrame(data.prices, columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return {"name": index, "history": df}

@st.cache_data(show_spinner=False)
def get_symbol_search(query: str):
    try:
        return loader.get_symbol_search(query)
    except Exception:
        url = (
            f"https://api.polygon.io/v3/reference/tickers"
            f"?search={query}&active=true&limit=10&apiKey={POLYGON_KEY}"
        )
        r = requests.get(url)
        data = r.json()
        return [(t["ticker"], t.get("name", "")) for t in data.get("results", [])]

def render_searchbar():
    st.session_state.setdefault("selected_asset", "AAPL")
    query = st.text_input("Search for an asset:", value="", key="search_input")

    if len(query) >= 2:
        results = get_symbol_search(query)
        if results:
            options = [f"{sym} - {name}" for sym, name in results]
            selected = st.session_state["selected_asset"]
            default_index = next((i for i, (sym, _) in enumerate(results) if sym == selected), 0)
            chosen = st.selectbox("Select an asset:", options, index=default_index, key="asset_searchbox")
            new_asset = chosen.split(" - ")[0]
            if new_asset != selected:
                st.session_state["selected_asset"] = new_asset
                st.rerun()

    return st.session_state["selected_asset"]
