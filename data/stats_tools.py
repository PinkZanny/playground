import pandas as pd
import numpy as np

def calculate_volatility(df: pd.DataFrame, window: int = 21) -> float:
    log_returns = np.log(df['close'] / df['close'].shift(1))
    rolling_std = log_returns.rolling(window=window).std()
    annualized_volatility = rolling_std * np.sqrt(252)
    return annualized_volatility

def get_log_returns(data: pd.Series) -> pd.Series:
    return np.log(data / data.shift(1)).dropna()

def get_first_difference(data: pd.Series) -> pd.Series:
    return data.diff().dropna()

def compute_pdf(data: pd.Series, bins: int = 50) -> tuple:
    hist, bin_edges = np.histogram(data, bins=bins, density=True)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    return hist, bin_centers

def compute_cdf(data: pd.Series, bins: int = 50) -> tuple:
    hist, bin_edges = np.histogram(data, bins=bins, density=True)
    cdf = np.cumsum(hist) * np.diff(bin_edges)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    return cdf, bin_centers