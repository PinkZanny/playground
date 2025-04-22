import gettext
import streamlit as st
import numpy as np
from data.data_loader import fetch_index_data, fetch_data
import plotly.graph_objects as go

def render(asset: str = "AAPL", _: gettext.translation = None):
    st.header(_("Market Regime Detector"))
    st.write(_("This section provides a comprehensive overview of the Market Regime Detector, which is designed to help investors identify the current market regime based on various indicators."))
    
    with st.expander(_("What is Market Regime Detection?")):
        st.markdown(_("""
        Market regime detection is a method used to identify different phases or regimes in financial markets, such as bull, bear, or sideways markets. By analyzing historical price movements and other indicators, investors can gain insights into the prevailing market conditions and adjust their strategies accordingly.
        
        The Market Regime Detector uses a combination of technical indicators and statistical thresholds to classify the current market regime. This information can be valuable for making informed investment decisions.
        """))
        
    with st.expander(_("How to use the Market Regime Detector")):
        st.markdown(_("""
        1. **Select an Index**: Choose a major index (e.g., S&P 500, FTSE100).  
        2. **Set Parameters**:  
           - Rolling window for smoothing returns and volatility.  
           - Return threshold to distinguish up/down trends.  
           - Volatility threshold to identify high-risk periods.  
        3. **Run Detection**: The app computes rolling mean returns and volatility, then classifies each day as:
           - **Bull**: positive trend & low volatility  
           - **Bear**: negative trend & high volatility  
           - **Ranged**: everything else  
        4. **Visualize**: View the price chart shaded by regime, and see the regime distribution over time.
        """))

    index = st.selectbox(_("Select Index for Regime Detection"), ["SPX", "FTSE100", "N225", "DAX", "NDX"])
    window = st.slider(_("Rolling window (days)"), 10, 252, 126)
    ret_th = st.slider(_("Return threshold (%)"), 0.0, 5.0, 1.0, step=0.1) / 100
    vol_th = st.slider(_("Volatility threshold (%)"), 0.0, 5.0, 1.0, step=0.1) / 100

    df = fetch_index_data(index)["history"]
    df["return"] = df["close"].pct_change()
    df["ret_roll"] = df["return"].rolling(window=window).mean()
    df["vol_roll"] = df["return"].rolling(window=window).std()

    cond_bull = (df["ret_roll"] > ret_th) & (df["vol_roll"] < vol_th)
    cond_bear = (df["ret_roll"] < -ret_th) & (df["vol_roll"] > vol_th)
    df["regime"] = np.select([cond_bull, cond_bear], ["Bull", "Bear"], "Ranged")

    fig = go.Figure(go.Scatter(x=df.index, y=df["close"], name="Price"))
    colors = {"Bull": "rgba(0,255,0,0.1)", "Bear": "rgba(255,0,0,0.1)", "Ranged": "rgba(255,255,0,0.1)"}
    for regime, color in colors.items():
        seg_start = None
        for dt, reg in df["regime"].items():
            if reg == regime and seg_start is None:
                seg_start = dt
            if seg_start and reg != regime:
                fig.add_vrect(x0=seg_start, x1=prev_dt, fillcolor=color, line_width=0)
                seg_start = None
            prev_dt = dt
        if seg_start:
            fig.add_vrect(x0=seg_start, x1=prev_dt, fillcolor=color, line_width=0)
    fig.update_layout(title=_("Market Regime Shading"), xaxis_title="Date", yaxis_title=_("Index Price"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(_("Regime Distribution"))
    counts = df["regime"].value_counts().reindex(["Bull","Ranged","Bear"]).fillna(0)
    st.bar_chart(counts)

    st.markdown("---")
    st.subheader(_("Asset Regime Detector for ") + asset)
    asset_df = fetch_data(asset)["history"]
    asset_df["return"] = asset_df["close"].pct_change()
    asset_df["ret_roll"] = asset_df["return"].rolling(window=window).mean()
    asset_df["vol_roll"] = asset_df["return"].rolling(window=window).std()

    asset_df["regime"] = np.select(
        [(asset_df["ret_roll"] > ret_th) & (asset_df["vol_roll"] < vol_th),
         (asset_df["ret_roll"] < -ret_th) & (asset_df["vol_roll"] > vol_th)],
        ["Bull", "Bear"],
        "Ranged"
    )

    fig2 = go.Figure(go.Scatter(x=asset_df.index, y=asset_df["close"], name=asset))
    for regime, color in colors.items():
        seg_start = None
        for dt, reg in asset_df["regime"].items():
            if reg == regime and seg_start is None:
                seg_start = dt
            if seg_start and reg != regime:
                fig2.add_vrect(x0=seg_start, x1=prev_dt, fillcolor=color, line_width=0)
                seg_start = None
            prev_dt = dt
        if seg_start:
            fig2.add_vrect(x0=seg_start, x1=prev_dt, fillcolor=color, line_width=0)
    fig2.update_layout(
        title=_(f"{asset} Regime Shading"),
        xaxis_title="Date",
        yaxis_title=_("Price")
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader(_("Asset Regime Distribution"))
    asset_counts = asset_df["regime"].value_counts().reindex(["Bull","Ranged","Bear"]).fillna(0)
    st.bar_chart(asset_counts)
