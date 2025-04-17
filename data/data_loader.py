import requests
import streamlit as st
import plotly.express as px
import polars as pl
from twelvedata import TDClient

TD_KEY = st.secrets["td_key"]
POLYGON_KEY = st.secrets["polygon_key"]
td = TDClient(apikey=TD_KEY)

@st.cache_data(show_spinner=False)
def fetch_data(ticker_str):
    ts = td.time_series(symbol=ticker_str, interval="1day", outputsize=500).as_pandas()
    ts_sorted = ts.sort_index(ascending=True)
    return {"name": ticker_str, "history": ts_sorted}

@st.cache_data(show_spinner=False)
def get_symbol_search(query):
    url = (
        f"https://api.polygon.io/v3/reference/tickers"
        f"?search={query}&active=true&limit=10&apiKey={POLYGON_KEY}"
    )
    r = requests.get(url)
    data = r.json()
    tickers = data.get("results", [])
    return [(t["ticker"], t.get("name", "")) for t in tickers]

def render_searchbar():
    st.session_state.setdefault("selected_asset", "AAPL")

    search_query = st.text_input("Search for an asset:", value="", key="search_input")

    if len(search_query) >= 2:
        results = get_symbol_search(search_query)
        if results:
            options = [f"{sym} - {name}" for sym, name in results]
            default = 0 if st.session_state["selected_asset"] not in [r[0] for r in results] else [
                r[0] for r in results
            ].index(st.session_state["selected_asset"])

            chosen_option = st.selectbox("Select an asset:", options, index=default, key="asset_searchbox")

            if chosen_option:
                new_asset = chosen_option.split(" - ")[0]
                if new_asset != st.session_state["selected_asset"]:
                    st.session_state["selected_asset"] = new_asset
                    st.rerun()
    
    return st.session_state["selected_asset"]