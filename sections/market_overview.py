# -*- coding: utf-8 -*-
import streamlit as st
from data.data_loader import fetch_data, fetch_index_data
from data.stats_tools import calculate_volatility, compute_pdf, compute_cdf, get_log_returns, get_first_difference
import plotly.express as px
import polars as pl
import pandas as pd
from plotly.subplots import make_subplots
import numpy as np
from scipy.stats import norm
import plotly.graph_objects as go
from statsmodels.nonparametric.smoothers_lowess import lowess
import gettext

#def generate_insights():


def render(asset:str = "AAPL", _: gettext.translation = None):
    st.title(_("Market Overview"))
    st.header(_("Market's Volatility Today"))

    sp500 = fetch_index_data("SPX")
    df_sp: pd.DataFrame = sp500["history"]
    window_sp = st.slider(_("Select the rolling window size (in days):"), min_value=1, max_value=100, value=21, step=1, key="sp500_window")
    df_sp['volatility'] = calculate_volatility(df_sp, window=window_sp)
    prevol = _("Today, S&P500 Volatility is ")
    if df_sp['volatility'].iloc[-1] > df_sp['volatility'].mean():
        prevol = _("Today, S&P500 Volatility is higher than average. ")
        aftervol = _("This means that the market is more volatile than usual, so it should be expected to be more risky.")
    elif df_sp['volatility'].iloc[-1] < df_sp['volatility'].mean():
        prevol = _("Today, S&P500 Volatility is lower than average. ")
        aftervol = _("This means that the market is less volatile than usual, so it should be expected to be less risky.")
    else:
        prevol = _("Today, S&P500 Volatility is equal to average. ")
        aftervol = _("This means that the market is as volatile as usual, so there is no need to worry.")

    st.write(f"{prevol} {aftervol}")

    start_index_sp = window_sp - 1
    fig_sp = make_subplots(rows=2, cols=1,
            shared_xaxes=True,
            subplot_titles=(_(f"Close Price for SP500"), _(f"Volatility for SP500")))
    fig_sp.add_trace(go.Scatter(x=df_sp.index[start_index_sp:], y=df_sp['close'][start_index_sp:], name='Close Price'), row=1, col=1)
    fig_sp.add_trace(go.Scatter(x=df_sp.index[start_index_sp:], y=df_sp['volatility'][start_index_sp:], name='Volatility'), row=2, col=1)
    fig_sp.update_layout(
        title="SP500 Volatility",
        xaxis_title="Date",
        yaxis_title="Volatility",
        annotations=[
            dict(
                text=_("Shaded Area = ±1σ (Volatility Band)"),
                xref="paper", yref="paper",
                x=0.01, y=1.05,
                showarrow=False,
                font=dict(size=12)
            )
        ]
    )
    st.plotly_chart(fig_sp)

    vol_explorer_tab, asset_screener_tab = st.tabs([_("Volatility Explorer"), _("Asset Screener")])

    with vol_explorer_tab:
        data = fetch_data(asset)
        headerstring = _("Volatility Explorer for ")
        st.header(f"{headerstring}{data['name']}")
        st.write(_("This is the Volatility Explorer section."))
        window = st.slider(_("Select the rolling window size (in days):"), min_value=1, max_value=100, value=21, step=1, key="volatility_window")
        df: pd.DataFrame = data["history"]
        df['volatility'] = calculate_volatility(df, window=window)

        start_index = window - 1

        fig = make_subplots(rows=2, cols=1,
                shared_xaxes=True,
                subplot_titles=(_(f"Close Price for {asset}"), _(f"Volatility for {asset}")))

        fig.add_trace(go.Scatter(x=df.index[start_index:], y=df['close'][start_index:], name='Close Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index[start_index:], y=df['volatility'][start_index:], name='Volatility'), row=2, col=1)

        log_returns = get_log_returns(df['close'])
        first_difference = get_first_difference(df['close'])

        choice = st.selectbox(_("Select the type of plot for returns:"), [_("Log Returns"), _("First Difference")])
                
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
        if st.checkbox(_("Show Rolling σ"), value=False):
            rolling_std = series.rolling(window=window).std()
            plot_series_with_shaded_std(fig, series[start_index:], rolling_std[start_index:], index_range, _("Rolling"))

        if st.checkbox(_("Show Smoothed σ"), value=False):
            smooth_window = st.slider("Smoothing window for σ", 2, 200, value=window//2)
            smoothed_std = get_smoothed_std(series, smooth_window)
            plot_series_with_shaded_std(fig, series[start_index:], smoothed_std[start_index:], index_range, _("Smoothed"), color='rgba(200,30,80,0.2)')

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=choice,
            annotations=[
                dict(
                    text=_("Shaded Area = ±1σ (Volatility Band)"),
                    xref="paper", yref="paper",
                    x=0.01, y=1.05,
                    showarrow=False,
                    font=dict(size=12)
                )
            ]
        )

        with st.expander("ℹ️ What does σ mean?"):
            st.markdown(_("""
            **σ (standard deviation)** is a statistical measure of volatility. The wider the bands, the more the asset's returns are varying.
            
            - **Rolling σ** reacts fast to new data, but can be noisy.
            - **Smoothed σ** shows long-term trends and regime shifts in risk.
            
            If the series breaks through these bands, something chaotic might be happening.
            """))

        st.plotly_chart(fig)

        st.write(_("Returns Distribution"))
        
        bins = st.slider(_("Select the number of bins for the histogram:"), min_value=1, max_value=100, value=50, step=1)
        show_normal = st.checkbox(_("Show Normal Distribution"), value=False)
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
        st.header(_("Asset Screener"))
        st.write(_("This is the Asset Screener section."))
        
