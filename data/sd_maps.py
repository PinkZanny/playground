from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
import streamlit as st


@dataclass
class Holiday:
    date: str
    description: str

    def __post_init__(self):
        try:
            self.date = datetime.strptime(self.date, "%Y-%m-%d").date()
        except ValueError:
            pass


@dataclass
class ExchangeInfo:
    open_time: str
    close_time: str
    timezone: str
    timezone_offset: str
    weekend_days: List[int]
    holidays: List[Holiday]


@dataclass
class CompanyInfo:
    symbol: str
    company: str
    description: str
    website: str
    exchange: str
    exchange_info: ExchangeInfo
    decimals: int
    currency: str
    intraday: bool
    real_time_mode: int
    real_time_delay: int

    @staticmethod
    def from_json(data: Dict[str, Any]) -> 'CompanyInfo':
        exchange_info = ExchangeInfo(
            open_time=data["exchangeOpenTimeGMT"],
            close_time=data["exchangeClosingTimeGMT"],
            timezone=data["exchangeTimeZone"],
            timezone_offset=data["exchangeTimeZoneOffset"],
            weekend_days=[int(day) for day in data["weekendDays"].split(";")],
            holidays=[
                Holiday(**dict(zip(data["holidays"]["columns"], row)))
                for row in data["holidays"]["values"]
            ]
        )

        return CompanyInfo(
            symbol=data["symbol"],
            company=data["company"],
            description=data["description"],
            website=data["website"],
            exchange=data["exchange"],
            exchange_info=exchange_info,
            decimals=data["decimals"],
            currency=data["currency"],
            intraday=data["intraday"],
            real_time_mode=data["realTimeMode"],
            real_time_delay=data["realTimeDelay"]
        )


@dataclass
class HistoricalPrices:
    symbol: str
    company: str
    exchange: str
    prices: List[List[Any]]

    @staticmethod
    def from_json(data: Dict[str, Any]) -> 'HistoricalPrices':
        info = data["data"]
        prices = [
            [datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ").date(), *row[1:]]
            for row in info["prices"]["values"]
        ]
        return HistoricalPrices(
            symbol=info["symbol"],
            company=info["company"],
            exchange=info["exchange"],
            prices=prices
        )


@dataclass
class IndexHistoricalPrices:
    index: str
    name: str
    prices: List[List[Any]]

    @staticmethod
    def from_json(data: Dict[str, Any]) -> 'IndexHistoricalPrices':
        data = data["data"]
        prices = [
            [datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ").date(), *row[1:]]
            for row in data["prices"]["values"]
        ]
        return IndexHistoricalPrices(
            index=data["index"],
            name=data["name"],
            prices=prices
        )


@dataclass
class RelatedCompanies:
    symbol: str
    company: str
    exchange: str
    relation_type: str

    @staticmethod
    def from_json(data: Dict[str, Any]) -> 'RelatedCompanies':
        return RelatedCompanies(
            symbol=data["symbol"],
            company=data["company"],
            exchange=data["exchange"],
            relation_type=data["relationType"]
        )


@dataclass
class IndexInfo:
    index: str
    name: str

    @staticmethod
    def from_json(data: Dict[str, Any]) -> 'IndexInfo':
        return IndexInfo(
            index=data["data"]["Index"],
            name=data["data"]["Name"]
        )

@dataclass
class StockIndicators:
    symbol: str
    company: str
    exchange: str
    indicators: Dict[str, Any]

    @staticmethod
    def from_json(data: Dict[str, Any]) -> 'StockIndicators':
        columns = data["data"]["prices"]["columns"]
        values = data["data"]["prices"]["values"][0]
        indicators = dict(zip(columns, values))

        return StockIndicators(
            symbol=data["data"]["symbol"],
            company=data["data"]["company"],
            exchange=data["data"]["exchange"],
            indicators=indicators
        )

