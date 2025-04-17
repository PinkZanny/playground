import streamlit as st
from data.data_loader import fetch_data, render_searchbar
from data.stats_tools import calculate_volatility, compute_pdf, compute_cdf, get_log_returns, get_first_difference
import plotly.express as px
import polars as pl
import pandas as pd
from plotly.subplots import make_subplots
import numpy as np
from scipy.stats import norm
import plotly.graph_objects as go
from statsmodels.nonparametric.smoothers_lowess import lowess


def render(asset:str = "AAPL"):
    st.title("Market Overview")

    """
    add a SP500 section 
    """

    vol_explorer_tab, asset_screener_tab = st.tabs(["Volatility Explorer", "Asset Screener"])

    with vol_explorer_tab:
        
        st.header(f"Volatility Explorer for {asset}")
        st.write("This is the Volatility Explorer section.")


        window = st.slider("Select the rolling window size (in days):", min_value=1, max_value=100, value=21, step=1)

        data = fetch_data(asset)
        df: pd.DataFrame = data["history"]
        df['volatility'] = calculate_volatility(df, window=window)

        start_index = window - 1

        fig = make_subplots(rows=2, cols=1,
                shared_xaxes=True,
                subplot_titles=(f"Close Price for {asset}", f"Volatility for {asset}"))

        fig.add_trace(go.Scatter(x=df.index[start_index:], y=df['close'][start_index:], name='Close Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index[start_index:], y=df['volatility'][start_index:], name='Volatility'), row=2, col=1)

        log_returns = get_log_returns(df['close'])
        first_difference = get_first_difference(df['close'])

        choice = st.selectbox("Select the type of plot for returns:", ["Log Returns", "First Difference"])
                
        def get_smoothed_std(series: pd.Series, smooth_window: int) -> pd.Series:
            smoothed = lowess(series.dropna(), np.arange(len(series.dropna())), 
                            frac=smooth_window / len(series), return_sorted=False)
            smoothed_series = pd.Series(smoothed, index=series.dropna().index)
            return smoothed_series.rolling(window=smooth_window).std()

        def plot_series_with_shaded_std(fig, series, std, index_range, label_prefix, color='rgba(0,100,80,0.2)'):
            upper = series + std
            lower = series - std
            fig.add_trace(go.Scatter(
                x=index_range, y=upper,
                mode='lines',
                line=dict(width=0),
                name=f'{label_prefix} Upper σ',
                showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=index_range, y=lower,
                mode='lines',
                fill='tonexty',
                fillcolor=color,
                line=dict(width=0),
                name=f'{label_prefix} σ Band'
            ))

        series = log_returns if choice == "Log Returns" else first_difference
        title = f"{choice} for {asset}"
        index_range = df.index[start_index+1:]
        series_to_plot = series[start_index:]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=index_range, y=series_to_plot,
            mode='lines', name=choice,
            line=dict(color='black', width=1)
        ))

        # Rolling σ
        if st.checkbox("Show Rolling σ", value=False):
            rolling_std = series.rolling(window=window).std()
            plot_series_with_shaded_std(fig, series[start_index:], rolling_std[start_index:], index_range, "Rolling")

        if st.checkbox("Show Smoothed σ", value=False):
            smooth_window = st.slider("Smoothing window for σ", 2, 200, value=window//2)
            smoothed_std = get_smoothed_std(series, smooth_window)
            plot_series_with_shaded_std(fig, series[start_index:], smoothed_std[start_index:], index_range, "Smoothed", color='rgba(200,30,80,0.2)')

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=choice,
            annotations=[
                dict(
                    text="Shaded Area = ±1σ (Volatility Band)",
                    xref="paper", yref="paper",
                    x=0.01, y=1.05,
                    showarrow=False,
                    font=dict(size=12)
                )
            ]
        )

        with st.expander("ℹ️ What does σ mean?"):
            st.markdown("""
            **σ (standard deviation)** is a statistical measure of volatility. The wider the bands, the more the asset's returns are varying.
            
            - **Rolling σ** reacts fast to new data, but can be noisy.
            - **Smoothed σ** shows long-term trends and regime shifts in risk.
            
            If the series breaks through these bands, something chaotic might be happening.
            """)

        st.plotly_chart(fig)

        st.write("Returns Distribution")
        
        bins = st.slider("Select the number of bins for the histogram:", min_value=1, max_value=100, value=50, step=1)
        show_normal = st.checkbox("Show Normal Distribution", value=False)
        asset_cdf = compute_cdf(log_returns, bins=bins)
        asset_pdf = compute_pdf(log_returns, bins=bins)
        fig = make_subplots(rows=1, cols=2,
            subplot_titles=("PDF", "CDF"))
        fig.add_trace(go.Scatter(x=asset_pdf[1], y=asset_pdf[0], name='PDF'), row=1, col=1)
        fig.add_trace(go.Scatter(x=asset_cdf[1], y=asset_cdf[0], name='CDF'), row=1, col=2)

        if show_normal:
            m = log_returns.mean()
            s = log_returns.std()
            xs_pdf = np.linspace(min(asset_pdf[1]), max(asset_pdf[1]), 100)
            xs_cdf = np.linspace(min(asset_cdf[1]), max(asset_cdf[1]), 100)
            normal_pdf = norm.pdf(xs_pdf, loc=m, scale=s)
            normal_cdf = norm.cdf(xs_cdf, loc=m, scale=s)
            fig.add_trace(go.Scatter(x=xs_pdf, y=normal_pdf, mode='lines',
                         line=dict(color='red'), name='Normal PDF'),
                         row=1, col=1)
            fig.add_trace(go.Scatter(x=xs_cdf, y=normal_cdf, mode='lines',
                         line=dict(color='red'), name='Normal CDF'),
                         row=1, col=2)
        st.plotly_chart(fig)
        

    with asset_screener_tab:
        st.header("Asset Screener")
        st.write("This is the Asset Screener section.")
        
