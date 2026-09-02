from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from backend.app.data.providers.akshare_provider import AKShareStockProvider
from backend.app.data.providers.base import InsufficientStockDataError, StockDataProvider
from backend.app.schemas.stock import DailyKlineSchema

DEFAULT_MIN_KLINE_ROWS = 60
DEFAULT_WINDOW_DAYS = 366
MAX_FETCH_YEARS = 5


class StockService:
    """Interface/adapter layer that guarantees a minimum window of qfq daily K-line.

    C's quant core requires at least ``DEFAULT_MIN_KLINE_ROWS`` (60) rows of qfq
    daily data. This service widens the fetch window when the requested range is
    too short and raises :class:`InsufficientStockDataError` when the stock does
    not have enough history.
    """

    def __init__(self, provider: Optional[StockDataProvider] = None) -> None:
        self._provider = provider or AKShareStockProvider()

    def get_daily_kline(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_rows: int = DEFAULT_MIN_KLINE_ROWS,
    ) -> List[DailyKlineSchema]:
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=DEFAULT_WINDOW_DAYS))
        hard_start = end_date - timedelta(days=MAX_FETCH_YEARS * 366)

        frame = self._provider.get_daily_kline(stock_code, start_date, end_date, adjust="qfq")
        while len(frame) < min_rows and start_date > hard_start:
            start_date = self._widen(start_date, hard_start)
            frame = self._provider.get_daily_kline(stock_code, start_date, end_date, adjust="qfq")

        if len(frame) < min_rows:
            raise InsufficientStockDataError(
                f"stock {stock_code} daily kline has {len(frame)} rows; "
                f"at least {min_rows} required"
            )

        return [DailyKlineSchema(**row) for row in frame.to_dict("records")]

    @staticmethod
    def _widen(start_date: date, hard_start: date) -> date:
        candidate = start_date - timedelta(days=366)
        return candidate if candidate > hard_start else hard_start
