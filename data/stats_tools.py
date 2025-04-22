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

def compute_return_from_start(data: pd.Series) -> float:
    return (data.iloc[-1] / data.iloc[0]) - 1

def compute_sharpe_ratio(data: pd.Series, risk_free_rate: float = 0.0) -> float:
    excess_returns = data - risk_free_rate
    return np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) != 0 else np.nan

def compute_sortino_ratio(data: pd.Series, target_return: float = 0.0) -> float:
    excess_returns = data - target_return
    downside_returns = excess_returns[excess_returns < 0]
    return np.mean(excess_returns) / np.std(downside_returns) if np.std(downside_returns) != 0 else np.nan

def compute_max_drawdown(data: pd.Series) -> float:
    cumulative_returns = (1 + data).cumprod() - 1
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min() if not drawdown.isna().all() else np.nan

def normalize_value(value: float, min_val: float, max_val: float) -> float:
    if min_val == max_val:
        return 0 
    return (value - min_val) / (max_val - min_val) * 100

def compute_volatility_skew(price_data: pd.Series, window: int = 30) -> float:
    if price_data.empty:
        return 0 

    volatility = calculate_volatility(pd.DataFrame({'close': price_data}), window)
    volatility_high = volatility.quantile(0.75)
    volatility_low = volatility.quantile(0.25)
    volatility_mean = volatility.mean()
    
    return (volatility_high - volatility_low) / volatility_mean

def compute_rsi(price_data: pd.Series, window: int = 14) -> pd.Series:
    delta = price_data.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_obv(price_data: pd.Series, volume_data: pd.Series) -> pd.Series:
    obv = volume_data.where(price_data.diff() > 0, -volume_data)
    obv[price_data.diff() == 0] = 0 
    return obv.cumsum()

def normalize_data(data: pd.Series) -> float:
    min_val = data.min()
    max_val = data.max()
    return normalize_value(data.iloc[-1], min_val, max_val)

def compute_sip(price_data: pd.Series,
                volume_data: pd.Series,
                w1: float = 0.3,
                w2: float = 0.4,
                w3: float = 0.3,
                window_volatility: int = 30,
                window_rsi: int = 14) -> float:
    volatility_skew = compute_volatility_skew(price_data, window=window_volatility)
    rsi_value = compute_rsi(price_data, window=window_rsi).iloc[-1]
    obv_series = compute_obv(price_data, volume_data)
    
    normalized_volatility_skew = normalize_data(pd.Series([volatility_skew] * len(price_data)))
    normalized_rsi = normalize_data(pd.Series([rsi_value] * len(price_data)))
    normalized_obv = normalize_data(obv_series)
    
    return (w1 * normalized_volatility_skew) + (w2 * normalized_rsi) + (w3 * normalized_obv)