from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class StockDataProviderError(RuntimeError):
    """Base exception for stock data provider failures."""


class InvalidStockCodeError(StockDataProviderError):
    """Raised when stock code format is invalid."""


class EmptyStockDataError(StockDataProviderError):
    """Raised when the data source returns no rows."""


class StockDataSchemaError(StockDataProviderError):
    """Raised when the data source schema is unexpected."""


class InsufficientStockDataError(StockDataProviderError):
    """Raised when the data source returns fewer rows than the caller requires."""


class StockDataProvider(ABC):
    @abstractmethod
    def get_daily_kline(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """Fetch daily kline data and return normalized snake_case columns."""
