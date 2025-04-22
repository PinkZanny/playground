import requests
from typing import Optional, Dict, Any
import streamlit as st
from data.sd_maps import CompanyInfo, IndexInfo, StockIndicators, HistoricalPrices, IndexHistoricalPrices, RelatedCompanies

class StockDioUtils:
    def __init__(self, app_key: Optional[str] = None):
        self.base_url = "https://api.stockdio.com"
        self.app_key = app_key or st.secrets["sd_key"]

    def _build_url(self, endpoint: str, **params) -> str:
        query_params = [f"app-key={self.app_key}"]
        query_params.extend([f"{k}={v}" for k, v in params.items()])
        query = "&".join(query_params)
        url = f"{self.base_url}{endpoint}?{query}".replace("from_=", "from=")
        return url

    def _get(self, url: str) -> Dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/135.0.0.0 Safari/537.36",
            "Referer": "https://services.stockdio.com/",
            "Origin": "https://services.stockdio.com"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_company_info(self, asset: str) -> CompanyInfo:
        url = self._build_url("/data/financial/info/v1/GetCompanyInfo", symbol=asset)
        return CompanyInfo.from_json(self._get(url))

    def get_index_info(self, index_name: str) -> IndexInfo:
        url = self._build_url("/data/financial/info/v1/GetIndexInfo", index=index_name)
        return IndexInfo.from_json(self._get(url))

    def get_related_companies(self, asset: str) -> RelatedCompanies:
        url = self._build_url("/data/financial/info/v1/getRelatedSymbols", symbol=asset)
        return RelatedCompanies.from_json(self._get(url))

    def get_historical_prices(self, asset: str, from_date: str, to_date: str) -> HistoricalPrices:
        url = self._build_url("/data/financial/prices/v1/GetHistoricalPrices", symbol=asset, from_=from_date, to=to_date)
        return HistoricalPrices.from_json(self._get(url))

    def get_index_historical_prices(self, index_name: str, from_date: str, to_date: str) -> IndexHistoricalPrices:
        url = self._build_url("/data/financial/prices/v1/GetHistoricalIndices", index=index_name, from_=from_date, to=to_date)
        return IndexHistoricalPrices.from_json(self._get(url))

    def get_indicators(
        self,
        asset: str,
        from_date: str,
        to_date: str,
        chaikin_short: int = 3,
        chaikin_long: int = 10,
        emv_period1: int = 14,
        emv_period2: int = 9,
        macd_fast: int = 26,
        macd_slow: int = 12,
        macd_signal: int = 9,
        momentum_period: int = 12,
        pvi_period1: int = 10,
        pvi_period2: int = 1000,
        rsi_period: int = 10,
        stoch_k: int = 10,
        stoch_d: int = 10,
        atr_period: int = 14,
        cci_period: int = 14,
        envelopes_period: int = 10,
        envelopes_dev: float = 6.0,
        mass_period: int = 25,
        mfi_period: int = 10,
        proc_period: int = 10,
        sma_period: int = 30,
        tma_period: int = 30,
        vol_chaikins_short: int = 10,
        vol_chaikins_long: int = 10,
        wma_period: int = 10,
        bb_period: int = 10,
        bb_dev: float = 2.0,
        dpo_period: int = 10,
        ema_period: int = 30,
        nvi_period1: int = 10,
        nvi_period2: int = 1000,
        roc_period: int = 10,
        stddev_period: int = 12,
        trix_period: int = 12,
        trix_signal: int = 9,
        vol_osc_short: int = 5,
        vol_osc_long: int = 10,
        willr_period: int = 14
    ) -> StockIndicators:

        indicators = [
            "AccumulationDistribution()",
            f"ChaikinOscillator({chaikin_short},{chaikin_long})",
            f"EaseOfMovement({emv_period1},{emv_period2})",
            f"macd({macd_fast},{macd_slow},{macd_signal})",
            f"Momentum({momentum_period})",
            "OnBalanceVolume()",
            f"PositiveVolumeIndex({pvi_period1},{pvi_period2})",
            f"RelativeStrengthIndex({rsi_period})",
            f"Stochastics({stoch_k},{stoch_d})",
            "WeightedClose()",
            "TypicalPrice()",
            f"AverageTrueRange({atr_period})",
            f"CommodityChannelIndex({cci_period})",
            f"Envelopes({envelopes_period},{envelopes_dev})",
            f"MassIndex({mass_period})",
            f"MoneyFlowIndex({mfi_period})",
            f"PercentualRateOfChange({proc_period})",
            "PriceAndVolumeTrend()",
            f"SimpleMovingAverage({sma_period})",
            f"TriangularMovingAverage({tma_period})",
            f"VolatilityChaikins({vol_chaikins_short},{vol_chaikins_long})",
            f"WeightedMovingAverage({wma_period})",
            f"BollingerBands({bb_period},{bb_dev})",
            f"DetrendedPriceOscillator({dpo_period})",
            f"ExponentialMovingAverage({ema_period})",
            "MedianPrice()",
            f"NegativeVolumeIndex({nvi_period1},{nvi_period2})",
            "Performance()",
            f"RateOfChange({roc_period})",
            f"StandardDeviation({stddev_period})",
            f"TRIX({trix_period},{trix_signal})",
            f"VolumeOscillator({vol_osc_short},{vol_osc_long})",
            f"WilliamsR({willr_period})"
        ]

        indicator_str = ";".join(indicators)
        url = self._build_url(
            "/data/financial/studies/v1/MultipleIndicatorCalculations",
            symbol=asset,
            indicators=indicator_str,
            from_=from_date,
            to=to_date
        )
        return StockIndicators.from_json(self._get(url))
