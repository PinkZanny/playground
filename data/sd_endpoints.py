import requests
from typing import Optional
import streamlit as st
from data.sd_endpoints import CompanyInfo, IndexInfo, RelatedCompanies, HistoricalPrices, IndexHistoricalPrices

class StockDioUtils:
    def __init__(self, app_key: Optional[str] = None):
        self.base_url = "https://api.stockdio.com"
        self.app_key = st.secrets["sd_key"]

    def _build_url(self, endpoint: str, **params) -> str:
        params["app-key"] = self.app_key
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}{endpoint}?{query}"

    def get_company_info(self, asset: str) -> CompanyInfo:
        url = self._build_url("/data/financial/info/v1/GetCompanyInfo", symbol=asset)
        response = requests.get(url)
        response.raise_for_status()
        return CompanyInfo.from_json(response.json())

    def get_index_info(self, index_name: str) -> IndexInfo:
        url = self._build_url("/data/financial/info/v1/GetIndexInfo", index=index_name)
        response = requests.get(url)
        response.raise_for_status()
        return IndexInfo.from_json(response.json())

    def get_related_companies(self, asset: str) -> RelatedCompanies:
        url = self._build_url("/data/financial/info/v1/getRelatedSymbols", symbol=asset)
        response = requests.get(url)
        response.raise_for_status()
        return RelatedCompanies.from_json(response.json())

    def get_historical_prices(self, asset: str, from_date: str, to_date: str) -> HistoricalPrices:
        url = self._build_url("/data/financial/prices/v1/GetHistoricalPrices", symbol=asset, from_=from_date, to=to_date)
        url = url.replace("from_=", "from=")
        response = requests.get(url)
        response.raise_for_status()
        return HistoricalPrices.from_json(response.json())

    def get_index_historical_prices(self, index_name: str, from_date: str, to_date: str) -> IndexHistoricalPrices:
        url = self._build_url("/data/financial/prices/v1/GetHistoricalIndices", index=index_name, from_=from_date, to=to_date)
        url = url.replace("from_=", "from=")
        response = requests.get(url)
        response.raise_for_status()
        return IndexHistoricalPrices.from_json(response.json())
