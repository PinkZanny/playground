import streamlit as st
from sections import market_overview, sip, mean_reversion, market_regime
from data.data_loader import render_searchbar

st.set_page_config(page_title="ZANQOR Playground", layout="wide")

"""
This is the playground for my website, zanqor.com
Visualization: 
- Streamlit (under the hood)
- Plotly
- Matplotlib
- Seaborn

Data Handling:
- Pandas
- Polars

Statistics:
- Numpy
- Scipy
- Statsmodels

Sections:
- Market Overview
-- Volatility Explorer
-- Asset Screener with z-scores, sharpe ratios, and other metrics
- SIP (Should I Panic?)
- Mean Reversion Heatmap (Correlation and Cointegration)
- Market Regime Detector
"""

st.sidebar.title("ZANQOR Playground")
st.sidebar.image("assets/portfolio_logo_variant.png", width=200)
section = st.sidebar.radio("Choose a section:", ["Market Overview", "SIP (Should I Panic?)", "Mean Reversion Heatmap", "Market Regime Detector"])
st.sidebar.write("Select an asset:")
with st.sidebar:
    asset = render_searchbar()

if section == "Market Overview":
    market_overview.render(asset=asset)
elif section == "SIP (Should I Panic?)":
    sip.render()
elif section == "Mean Reversion Heatmap":
    mean_reversion.render()
elif section == "Market Regime Detector":
    market_regime.render()