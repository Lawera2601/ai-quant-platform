"""A-share trading-day calendar helper.

This is the *real* completeness basis for :class:`MarketDataService.query_daily` —
a ``(start, end) -> expected trading-day count`` callable derived from the actual
A-share trade-date calendar (via AKShare), so the cache-completeness judgment is
not a fixed test value.

The calendar list is loaded once per provider instance and cached in-process.
For offline tests, a deterministic ``trade_dates`` list (or a ``fetch`` callable)
can be injected instead of hitting AKShare.
"""

from __future__ import annotations

from datetime import date
from typing import Callable, List, Optional

import pandas as pd


class TradingCalendarProvider:
    """Provide the A-share trading-day list and count days in a window."""

    def __init__(
        self,
        trade_dates: Optional[List[date]] = None,
        fetch: Optional[Callable[[], List[date]]] = None,
    ) -> None:
        self._trade_dates = trade_dates
        self._fetch = fetch

    def get_trade_dates(self) -> List[date]:
        if self._trade_dates is None:
            self._trade_dates = (
                self._fetch() if self._fetch is not None else self._load_from_akshare()
            )
        return self._trade_dates

    def count_between(self, start: date, end: date) -> int:
        """Number of trading days in the closed interval ``[start, end]``."""
        return sum(1 for day in self.get_trade_dates() if start <= day <= end)

    def as_callable(self) -> Callable[[date, date], int]:
        """Return ``(start, end) -> int`` for injection as ``trading_days``."""
        return self.count_between

    @staticmethod
    def _load_from_akshare() -> List[date]:
        import akshare as ak

        raw = ak.tool_trade_date_hist_sina()
        column = "trade_date" if "trade_date" in raw.columns else raw.columns[0]
        return sorted(pd.to_datetime(raw[column]).dt.date.tolist())
