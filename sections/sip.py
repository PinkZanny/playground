import gettext
import streamlit as st
from data.data_loader import fetch_index_data, fetch_data
import plotly.graph_objects as go
from data.stats_tools import compute_sip
import pandas as pd

def render(asset: str = "AAPL", _: gettext.translation = None):
    st.header(_("SIP (Should I Panic?)"))
    st.write(_("This section provides a comprehensive overview of the SIP (Should I Panic?) indicator, which is designed to help investors assess the current market sentiment and make informed decisions."))
    with st.expander("What is SIP?"):
            st.markdown(_("""
            The SIP (Should I Panic?) indicator is a proprietary metric that combines various market indicators, with custom weights, to provide a single value that reflects the current market sentiment. This section is divided into two main parts:
            
            1. **Indices Comparison**: This part compares the SIP values of major indices, allowing you to see how they are performing relative to each other.
            2. **Asset SIP**: This part focuses on the selected asset, providing its SIP value and a comparison with the indices.
            
            The SIP value is calculated using the following formula:
            
            $$ SIP = w_1 \\cdot \\text{RSI} + w_2 \\cdot \\text{Volatility} + w_3 \\cdot \\text{Volume} $$
            
            Where:
            - \(w_1\), \(w_2\), and \(w_3\) are the weights assigned to each component.
            - RSI is the Relative Strength Index, a momentum oscillator that measures the speed and change of price movements.
            - Volatility is a measure of the price fluctuations of the asset.
            - Volume is the total number of shares traded during a specific period.
            
            The SIP value is normalized to a scale of 0 to 100, where:
            - 0-33: Low panic level (green)
            - 34-66: Moderate panic level (orange)
            - 67-100: High panic level (red)
            """))

    st.subheader(_("Indices Comparison"))
    
    idx_symbols = {"SPX": "SPX", "FTSE": "FTSE100", "N225": "N225", "DAX": "DAX", "NDX": "NYA"}
    idx_hist = {}
    progress = st.progress(0)
    for i, (name, sym) in enumerate(idx_symbols.items(), start=1):
        idx_hist[name] = fetch_index_data(sym)["history"]
        progress.progress(int(i / len(idx_symbols) * 100))
    progress.empty()
    
    latest_date = max(df.index.max() for df in idx_hist.values()).date()
    selected_date = st.date_input(_("Select a Date"), value=st.session_state.get("selected_date", latest_date))
    st.session_state["selected_date"] = selected_date
    selected_ts = pd.to_datetime(selected_date)
    
    norm_fig = go.Figure()
    for name, df in idx_hist.items():
        df50 = df.tail(50).copy()
        df50["normalized"] = df50["close"] / df50["close"].iloc[0] * 100
        norm_fig.add_trace(go.Scatter(x=df50.index, y=df50["normalized"], mode="lines", name=name))
    norm_fig.update_layout(
        title="Normalized Close Prices (Last 50)",
        xaxis_title="Date",
        yaxis_title="Base=100",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,
            xanchor="center",
            x=0.5
        )
    )
    st.plotly_chart(norm_fig)
    
    sip_today = {}
    sip_yesterday = {}
    for name, df in idx_hist.items():
        hist = df[df.index <= selected_ts]
        if len(hist) < 2:
            sip_today[name] = None
            sip_yesterday[name] = None
            continue
        sip_today[name] = compute_sip(
            price_data=hist["close"], volume_data=hist["volume"],
            w1=0.3, w2=0.4, w3=0.3,
            window_rsi=14, window_volatility=30
        )
        hist_prev = hist.iloc[:-1]
        sip_yesterday[name] = compute_sip(
            price_data=hist_prev["close"], volume_data=hist_prev["volume"],
            w1=0.3, w2=0.4, w3=0.3,
            window_rsi=14, window_volatility=30
        )

    valid_today = [v for v in sip_today.values() if v is not None]
    valid_yesterday = [sip_yesterday[n] for n in sip_today if sip_today[n] is not None]
    aggregated_today = sum(valid_today) / len(valid_today) if valid_today else None
    aggregated_yesterday = sum(valid_yesterday) / len(valid_yesterday) if valid_yesterday else None
    
    col1, col2 = st.columns(2)
    
    def display_sip_gauge(today, yesterday, title, container):
        delta_conf = {}
        if today is not None and yesterday is not None and yesterday != 0:
            delta_conf = {
                'reference': yesterday,
                'relative': True,
                'position': 'bottom',
                'valueformat': '.2%',
                'increasing': {'color': 'red'},
                'decreasing': {'color': 'green'}
            }
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=today or 0,
            delta=delta_conf,
            title={'text': title, 'font': {'size': 18}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#E4C7B8"},
                'steps': [
                    {'range': [0, 33], 'color': "#00A676"},
                    {'range': [33, 66], 'color': "#FF7300"},
                    {'range': [66, 100], 'color': "#F93943"}
                ],
                'threshold': {'line': {'color': "#000000", 'width': 1}, 'value': today or 0}
            }
        ))
        with container:
            st.plotly_chart(fig, use_container_width=True)
    
    display_sip_gauge(aggregated_today, aggregated_yesterday, _("Aggregated SIP"), col1)
    
    asset_df = fetch_data(asset)["history"]
    asset_hist = asset_df[asset_df.index <= selected_ts]
    if len(asset_hist) >= 2:
        sip_asset_today = compute_sip(
            price_data=asset_hist["close"], volume_data=asset_hist["volume"],
            w1=0.3, w2=0.4, w3=0.3,
            window_rsi=14, window_volatility=30
        )
        sip_asset_yesterday = compute_sip(
            price_data=asset_hist.iloc[:-1]["close"], volume_data=asset_hist.iloc[:-1]["volume"],
            w1=0.3, w2=0.4, w3=0.3,
            window_rsi=14, window_volatility=30
        )
        display_sip_gauge(sip_asset_today, sip_asset_yesterday, asset, col2)
    else:
        with col2:
            st.write(_("No data available for the selected date."))
