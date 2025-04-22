# -*- coding: utf-8 -*-
import streamlit as st
from data.data_loader import fetch_data, fetch_index_data, fetch_related_companies_data
from data.stats_tools import calculate_volatility, compute_pdf, compute_cdf, get_log_returns, get_first_difference, compute_return_from_start, compute_sharpe_ratio, compute_sortino_ratio, compute_max_drawdown
import plotly.express as px
import polars as pl
import pandas as pd
from plotly.subplots import make_subplots
import numpy as np
from scipy.stats import norm
import plotly.graph_objects as go
from statsmodels.nonparametric.smoothers_lowess import lowess
import gettext
from typing import List
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def render(asset:str = "AAPL", _: gettext.translation = None):
    st.title(_("Market Overview"))
    st.header(_("Market's Volatility Today"))

    sp500 = fetch_index_data("SPX")
    vix = fetch_index_data("VIX")
    df_vix: pd.DataFrame = vix["history"]
    df_sp: pd.DataFrame = sp500["history"]
    window_sp = st.slider(_("Select the rolling window size (in days):"), min_value=1, max_value=100, value=21, step=1, key="sp500_window")

    df_sp['volatility'] = calculate_volatility(df_sp, window=window_sp) * 100
    df_vix = df_vix.rename(columns={'close': 'vix'})
    df_vix = df_vix[['vix']]
    df_combined = df_sp.join(df_vix, how='inner')

    current_vol = df_combined['volatility'].iloc[-1]
    average_vol = df_combined['volatility'].mean()

    if current_vol > average_vol:
        insight = _("S&P 500 rolling volatility is currently above its historical average. ")
        meaning = _("This suggests increased market uncertainty and higher perceived risk. Traders may demand more premium for risk exposure.")
    elif current_vol < average_vol:
        insight = _("S&P 500 rolling volatility is currently below its historical average. ")
        meaning = _("This indicates a calmer market environment with lower perceived risk—often associated with stable or bullish periods.")
    else:
        insight = _("S&P 500 rolling volatility is in line with its historical average. ")
        meaning = _("No major deviation in risk expectations—market conditions are within expected ranges.")

    st.markdown(f"{insight} {meaning}")

    show_vix = st.checkbox("Overlay VIX (Implied Volatility)", value=True)

    vol_diff = df_combined['vix'] - df_combined['volatility']
    vol_diff = vol_diff.rename("Volatility Difference (VIX - Realized)")
    df_combined = df_combined.join(vol_diff, how='inner')
    df_combined = df_combined.rename(columns={'close': 'sp500_close'})
    df_combined = df_combined[['sp500_close', 'volatility', 'vix', 'Volatility Difference (VIX - Realized)']]
    df_combined = df_combined.dropna()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_combined.index, y=df_combined['volatility'], name='Rolling Volatility (Realized)', line=dict(color='blue')))
    if show_vix:
        fig.add_trace(go.Scatter(x=df_combined.index, y=df_combined['vix'], name='VIX (Implied)', line=dict(color='orange', dash='dash')))

    fig.update_layout(
        title='S&P 500 Realized vs Implied Volatility',
        xaxis_title='Date',
        yaxis_title='Volatility (%)',
        legend_title='Metric',
        template='plotly_dark'
    )

    st.plotly_chart(fig, use_container_width=True)

    fig_corr = go.Figure()
    fig_corr.add_trace(go.Scatter(x=df_combined.index, y=df_combined['Volatility Difference (VIX - Realized)'], name='Volatility Difference (VIX - Realized)', line=dict(color='purple')))
    fig_corr.update_layout(
        title='Volatility Difference (VIX - Realized)',
        xaxis_title='Date',
        yaxis_title='Difference',
        legend_title='Metric',
        template='plotly_dark'
    )
    st.plotly_chart(fig_corr, use_container_width=True)
    st.write(_("The VIX is a measure of the market's expectation of future volatility, derived from the prices of S&P 500 index options. A higher VIX indicates higher expected volatility, while a lower VIX suggests lower expected volatility."))
    st.write(_("This means that whenever the VIX is higher than the rolling volatility, the market is expecting more volatility than what is actually happening. This can be interpreted as a sign of uncertainty or fear in the market. On the other hand, when the VIX is lower than the rolling volatility, it indicates that the market is expecting less volatility than what is actually happening. This can be interpreted as a sign of confidence or complacency in the market."))
    st.write(_("What can you do with this? You can use this information to make informed decisions about your investments. For example, if the VIX is higher than the rolling volatility, you might want to consider hedging your portfolio or reducing your exposure to risky assets, whereas if the VIX is lower than the rolling volatility, you might want to consider increasing your exposure to risky assets or taking advantage of the low volatility environment."))


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
        st.write(_("Here, you can check your selected asset's metrics against the related companies. This includes companies in the same sector and competitors."))
        
        sel_asset = st.session_state["selected_asset"]
        st.write(_("Selected asset: "), sel_asset)

        with st.expander("What are the computed metrics?"):
            st.markdown(_("""
            - **Cumulative Return**: The total return of the asset from the start date to the end date.
            - **Sharpe Ratio**: A measure of risk-adjusted return. It indicates how much excess return you receive for the extra volatility you endure for holding a riskier asset.
            - **Sortino Ratio**: Similar to the Sharpe ratio, but it only considers downside volatility. It is a measure of risk-adjusted return that focuses on negative returns.
            - **Max Drawdown**: The maximum observed loss from a peak to a trough of a portfolio, before a new peak is attained. It is used to assess the risk of a particular investment.
                          
            This screener is useful when you want to compare your asset with its competitors or related companies, to maybe confirm an edge or just win an argument with your friends.
            """))

        df['return'] = df['close'].pct_change()
        cumulative_return = compute_return_from_start(df['close']) if not df.empty else None

        rate = st.slider(_("Select the Risk Free Rate and Target Return:"), min_value=0.0, max_value=0.1, value=0.01, step=0.01, key="risk_free_rate")

        sharpe_selected = compute_sharpe_ratio(df['return'], risk_free_rate=rate)
        sortino_selected = compute_sortino_ratio(df['return'], target_return=rate)
        max_dd_selected = compute_max_drawdown(df['return'])

        metrics_df = pd.DataFrame({
            _("Cumulative Return"): [cumulative_return],
            _("Sharpe Ratio"): [sharpe_selected],
            _("Sortino Ratio"): [sortino_selected],
            _("Max Drawdown"): [max_dd_selected]
        }, index=[sel_asset])

        st.subheader(_("Base Asset Metrics"))
        st.dataframe(metrics_df.style.format(precision=4), use_container_width=True)

        st.write(_("Now, let's check the related companies."))
        related_companies = fetch_related_companies_data(sel_asset)

        related_companies = related_companies.rename(columns={"symbol": "Ticker", "company": "Company", "exchange": "Exchange", "relation_type": "Relation Type"})
        related_companies = related_companies[["Ticker", "Company", "Exchange", "Relation Type"]].dropna()
        related_companies = related_companies[related_companies["Relation Type"].isin(["C", "R"])]

        def compute_metrics_for_group(companies_df, relation_type):
            rel_type = "Competitor" if relation_type == "C" else "Related"
            st.subheader(_(f"Metrics for {rel_type} Companies"))
            group = companies_df[companies_df["Relation Type"] == relation_type]
            results = []

            for x, row in group.iterrows():
                ticker = row["Ticker"]
                data_rel = fetch_data(ticker)
                df_rel = data_rel.get("history")
                name = data_rel.get("name")
                if df_rel is None or df_rel.empty:
                    continue
                df_rel['return'] = df_rel['close'].pct_change()
                results.append({
                    "Ticker": ticker,
                    _("Cumulative Return"): compute_return_from_start(df_rel['close']),
                    _("Sharpe Ratio"): compute_sharpe_ratio(df_rel['return'], risk_free_rate=rate),
                    _("Sortino Ratio"): compute_sortino_ratio(df_rel['return'], target_return=rate),
                    _("Max Drawdown"): compute_max_drawdown(df_rel['return'])
                })

            
            if results:
                group_df = pd.DataFrame(results).set_index("Ticker")
                base_row = metrics_df.rename_axis("Ticker")
                combined_df = pd.concat([base_row, group_df])
                tooltip_map = {row["Ticker"]: fetch_data(row["Ticker"]).get("name", "") for _, row in group.iterrows()}
                tooltip_map[sel_asset] = fetch_data(sel_asset).get("name", sel_asset)
                combined_df = combined_df.reset_index()
                combined_df["Name"] = combined_df["Ticker"].map(tooltip_map)
                cols = ["Name"] + [col for col in combined_df.columns if col != "Name"]
                combined_df = combined_df[cols]

                gb = GridOptionsBuilder.from_dataframe(combined_df)

                gb.configure_columns([col for col in combined_df.columns], cellStyle={'font-family': 'sans-serif'})

                for col in combined_df.columns:
                    gb.configure_column(col, wrapText=True, autoHeight=True)

                highlight_js = JsCode(f"""
                function(params) {{
                    if (params.data.Ticker === '{sel_asset}') {{
                        return {{
                            'backgroundColor': '{st.get_option("theme.primaryColor")}',
                            'color': 'white',
                            'fontWeight': 'normal'  // Remove boldness
                        }}
                    }}
                }}
                """)

                for col in combined_df.columns:
                    gb.configure_column(col, cellStyle=highlight_js)

                grid_options = gb.build()

                AgGrid(
                    combined_df,
                    gridOptions=grid_options,
                    fit_columns_on_grid_load=True,
                    allow_unsafe_jscode=True,
                    enable_enterprise_modules=False
                )

            else:
                st.write(_("No data available for this group."))

        compute_metrics_for_group(related_companies, "R")
        compute_metrics_for_group(related_companies, "C")
