import gettext
import streamlit as st
from data.data_loader import fetch_data
import plotly.graph_objects as go
import pandas as pd

def render(asset: str = "AAPL", _: gettext.translation = None):
    st.header(_("Mean Reversion Heatmap"))
    st.write(_("This section provides a comprehensive overview of the Mean Reversion Heatmap, which is designed to help investors identify potential mean reversion opportunities in the market."))
    with st.expander(_("What is Mean Reversion?")):
        st.markdown(_("""
        Mean reversion is a financial theory suggesting that asset prices and historical returns eventually return to their long-term mean or average level. This concept is based on the idea that extreme price movements are often followed by a reversal towards the mean.

        The Mean Reversion Heatmap visualizes the current spread between pairs of cointegrated or correlated assets relative to their historical mean, helping investors identify potential trading opportunities. Colors indicate standardized deviations:

        - **Green**: Spread well below its mean → potential buy
        - **Yellow**: Slightly below mean → mild buy
        - **Orange**: Slightly above mean → mild sell
        - **Red**: Well above mean → potential sell
        """))

    with st.expander(_("How to use the Mean Reversion Heatmap")):
        st.markdown(_("""
        **1. Universe Selection**  
        Use the dropdown to pick one of three universes:
        - **Well Cointegrated**: Pairs known to share a stable long‑run relationship  
        - **Well Correlated**: Pairs that move together over time  
        - **Hedged**: An asset vs. a hedging instrument (bonds, gold, etc.)

        **2. Rolling Window**  
        Adjust the slider to set how many days of history to use when computing the mean and standard deviation of each pair’s spread.

        **3. Z‑Score Calculation**  
        For each selected pair `(i,j)`, we compute:
        ```
        spread = price_i - price_j
        z = (spread_today - mean(spread_last_N)) / std(spread_last_N)
        ```
        Cells are blank for non‑pairs. Diagonal = 0.

        **4. Color Coding**  
        - **Green** (z ≪ 0): spread far below its mean → potential **buy**  
        - **Yellow** (z slightly < 0): mild **buy** signal  
        - **Orange** (z slightly > 0): mild **sell** signal  
        - **Red** (z ≫ 0): spread far above its mean → potential **sell**

        **5. Interpretation**  
        A hot red cell means the spread is unusually wide—look for a convergence trade. A deep green cell means the spread is unusually narrow—consider the opposite.

        """))

    # Define pair universes
    universes = {
        _("Well Cointegrated"): [
            ("AAPL", "MSFT"),
            ("GOOG", "AMZN"),
            ("TSLA", "NVDA"),
        ],
        _("Well Correlated"): [
            ("AAPL", "MSFT"),
            ("GOOG", "META"),
            ("XOM", "CVX"),
        ],
        _("Hedged"): [
            ("SPY", "IEF"),   # equity vs. 7-10y Treasuries
            ("QQQ", "TLT"),   # tech vs. long bonds
            ("GLD", "TLT"),   # gold vs. bonds
        ]
    }

    choice = st.selectbox(_("Select universe:"), list(universes.keys()))
    pairs = universes[choice]

    window = st.slider(_("Rolling window (days)"), 20, 252, 126, 10, key="mr_window")

    # Fetch prices
    tickers = sorted({t for pair in pairs for t in pair})
    price_df = pd.concat(
        {t: fetch_data(t)["history"]["close"] for t in tickers},
        axis=1
    ).dropna()

    # Build z‑score matrix
    zmat = pd.DataFrame(index=tickers, columns=tickers, dtype=float)
    for i in tickers:
        for j in tickers:
            if i == j:
                zmat.loc[i, j] = 0.0
            elif (i, j) in pairs:
                spread = price_df[i] - price_df[j]
                m = spread.rolling(window).mean().iloc[-1]
                s = spread.rolling(window).std().iloc[-1]
                zmat.loc[i, j] = 0.0 if s == 0 or pd.isna(s) else (spread.iloc[-1] - m) / s
            else:
                zmat.loc[i, j] = None  # blank for non‑paired cells

    # Plotly heatmap
    fig = go.Figure(go.Heatmap(
        z=zmat.values,
        x=tickers,
        y=tickers,
        colorscale="RdYlGn_r",
        zmid=0,
        colorbar=dict(title=_("Z‑Score")),
        hovertemplate="%{y} vs %{x}<br>z = %{z:.2f}<extra></extra>"
    ))
    fig.update_layout(
        title=_(f"{choice} Mean Reversion Heatmap"),
        xaxis_nticks=len(tickers),
        yaxis_nticks=len(tickers),
        width=700,
        height=700,
        margin=dict(l=50, r=50, t=100, b=50)
    )
    st.plotly_chart(fig, use_container_width=True)
