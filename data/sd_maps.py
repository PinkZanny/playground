from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class HistoricalPrices:
    symbol: str
    company: str
    exchange: str
    prices: List[List[Any]]

    @staticmethod
    def from_json(data: Dict[str, Any]) -> 'HistoricalPrices':
        parsed_prices = [
            [datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ").date(), *row[1:]]
            for row in data["prices"]["values"]
        ]

        return HistoricalPrices(
            symbol=data["symbol"],
            company=data["company"],
            exchange=data["exchange"],
            prices=parsed_prices
        )

@dataclass
class IndexHistoricalPrices:
    index: str
    name: str
    prices: List[List[Any]]

    @staticmethod
    def from_json(data: Dict[str, Any]) -> 'HistoricalPrices':
        parsed_prices = [
            [datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ").date(), *row[1:]]
            for row in data["prices"]["values"]
        ]

        return HistoricalPrices(
            index=data["index"],
            name=data["name"],
            prices=parsed_prices
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
class CompanyInfo:
    symbol: str
    company: str
    description: str
    website: str
    exchange: str
    exchange_info: 'CompanyInfo.ExchangeInfo'
    decimals: int
    currency: str
    intraday: bool
    real_time_mode: int
    real_time_delay: int

    @staticmethod
    def from_json(data: Dict[str, Any]) -> 'CompanyInfo':
        exchange_info = CompanyInfo.ExchangeInfo(
            open_time=data["exchangeOpenTimeGMT"],
            close_time=data["exchangeClosingTimeGMT"],
            timezone=data["exchangeTimeZone"],
            timezone_offset=data["exchangeTimeZoneOffset"],
            weekend_days=[int(day) for day in data["weekendDays"].split(";")],
            holidays=[
                CompanyInfo.Holiday(**dict(zip(data["holidays"]["columns"], row)))
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
        holidays: List['CompanyInfo.Holiday']
