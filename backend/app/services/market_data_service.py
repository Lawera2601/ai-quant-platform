"""Market-data (stock_basic / stock_daily) persistence: MySQL upsert + query.

This is the DB half of the V1 data pipeline: the API keeps its existing
contract, while this module lets B pull real qfq data into MySQL and read it
back (System Design :: Service 层：查询 MySQL -> 缺失时调 Provider -> 标准化 ->
Upsert MySQL -> 返回).

Repository methods are portable across the SQLite test database and MySQL 8
(no MySQL-specific DDL is used), so the upsert/query logic is unit-testable
without a running MySQL instance.

All ``SQLAlchemyError`` failures are translated into ``DatabaseOperationError``
(business code 50002) and the session is rolled back, so callers observe a
stable business error instead of a raw driver exception.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import List, Optional, Protocol, Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.core.errors import DatabaseOperationError
from backend.app.models.stock_basic import StockBasic
from backend.app.models.stock_daily import StockDaily
from backend.app.schemas.stock import DailyKlineSchema, StockBasicSchema
from backend.app.services.stock_service import DEFAULT_MIN_KLINE_ROWS, StockService

#: A cache is considered fresh only if its latest bar is within this many days
#: of the requested ``end_date`` (also covers the earliest-bar gap to ``start``).
DEFAULT_MAX_STALE_DAYS = 3

#: Canonical decimal precision ("口径") for persisted daily bars. Prices are
#: stored at 4 decimals, amount at 2 and turnover/change at 6, matching the
#: ``DATABASE_DESIGN.md`` DECIMAL columns. Rounding is applied explicitly in
#: Python so both MySQL and SQLite round-trip identically (DB-agnostic).
PRICE_NDIGITS = 4
AMOUNT_NDIGITS = 2
PERCENT_NDIGITS = 6


class MarketDataSource(Protocol):
    """Injectable market-data source consumed by the AI pipeline / API layer."""

    def query_daily(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_rows: int = DEFAULT_MIN_KLINE_ROWS,
        max_stale_days: int = DEFAULT_MAX_STALE_DAYS,
    ) -> List[DailyKlineSchema]:
        """Return a >= ``min_rows`` valid qfq daily window, filling the cache
        from the provider when the cached range is incomplete or stale."""
        ...

    def sync_daily(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
        min_rows: int = DEFAULT_MIN_KLINE_ROWS,
    ) -> List[DailyKlineSchema]:
        """Fetch + clean + widen via ``StockService``, then upsert into MySQL."""
        ...


class MarketDataRepository:
    """Upsert/read access to ``stock_basic`` and ``stock_daily``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_stock_basic(self, item: StockBasicSchema) -> None:
        try:
            record = self._session.get(StockBasic, item.stock_code)
            if record is None:
                self._session.add(
                    StockBasic(
                        stock_code=item.stock_code,
                        stock_name=item.stock_name,
                        industry=item.industry,
                        total_market_cap=item.total_market_cap,
                        float_market_cap=item.float_market_cap,
                    )
                )
            else:
                record.stock_name = item.stock_name
                record.industry = item.industry
                record.total_market_cap = item.total_market_cap
                record.float_market_cap = item.float_market_cap
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise DatabaseOperationError() from exc

    def get_stock_basic(self, stock_code: str) -> Optional[StockBasicSchema]:
        try:
            record = self._session.get(StockBasic, stock_code)
            if record is None:
                return None
            return StockBasicSchema(
                stock_code=record.stock_code,
                stock_name=record.stock_name,
                industry=record.industry,
                total_market_cap=record.total_market_cap,
                float_market_cap=record.float_market_cap,
            )
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise DatabaseOperationError() from exc

    def upsert_daily(self, rows: Sequence[DailyKlineSchema]) -> int:
        """Insert or update daily bars keyed by ``(stock_code, trade_date)``.

        Numeric fields are rounded to the canonical precision (see module docs)
        before writing, so the DB round-trip is deterministic on MySQL and SQLite.
        """
        try:
            count = 0
            for row in rows:
                fields = self._rounded_daily_fields(row)
                record = (
                    self._session.query(StockDaily)
                    .filter_by(stock_code=row.stock_code, trade_date=row.trade_date)
                    .one_or_none()
                )
                if record is None:
                    self._session.add(StockDaily(**fields))
                else:
                    fields.pop("stock_code", None)
                    fields.pop("trade_date", None)
                    for field, value in fields.items():
                        setattr(record, field, value)
                count += 1
            self._session.commit()
            return count
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise DatabaseOperationError() from exc

    def list_daily(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[DailyKlineSchema]:
        try:
            query = self._session.query(StockDaily).filter(
                StockDaily.stock_code == stock_code
            )
            if start_date is not None:
                query = query.filter(StockDaily.trade_date >= start_date)
            if end_date is not None:
                query = query.filter(StockDaily.trade_date <= end_date)
            records = query.order_by(StockDaily.trade_date.asc()).all()
            return [self._to_schema(record) for record in records]
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise DatabaseOperationError() from exc

    @staticmethod
    def _rounded_daily_fields(row: DailyKlineSchema) -> dict:
        return {
            "stock_code": row.stock_code,
            "trade_date": row.trade_date,
            "open": MarketDataRepository._round_value(row.open, PRICE_NDIGITS),
            "high": MarketDataRepository._round_value(row.high, PRICE_NDIGITS),
            "low": MarketDataRepository._round_value(row.low, PRICE_NDIGITS),
            "close": MarketDataRepository._round_value(row.close, PRICE_NDIGITS),
            "volume": row.volume,
            "amount": MarketDataRepository._round_value(row.amount, AMOUNT_NDIGITS),
            "turnover_rate": MarketDataRepository._round_value(row.turnover_rate, PERCENT_NDIGITS),
            "change_pct": MarketDataRepository._round_value(row.change_pct, PERCENT_NDIGITS),
        }

    @staticmethod
    def _round_value(value, ndigits: int):
        return round(value, ndigits) if value is not None else None

    @staticmethod
    def _to_schema(record: StockDaily) -> DailyKlineSchema:
        return DailyKlineSchema(
            stock_code=record.stock_code,
            trade_date=record.trade_date,
            open=MarketDataRepository._round_value(record.open, PRICE_NDIGITS),
            high=MarketDataRepository._round_value(record.high, PRICE_NDIGITS),
            low=MarketDataRepository._round_value(record.low, PRICE_NDIGITS),
            close=MarketDataRepository._round_value(record.close, PRICE_NDIGITS),
            volume=record.volume,
            amount=MarketDataRepository._round_value(record.amount, AMOUNT_NDIGITS),
            turnover_rate=MarketDataRepository._round_value(record.turnover_rate, PERCENT_NDIGITS),
            change_pct=MarketDataRepository._round_value(record.change_pct, PERCENT_NDIGITS),
        )

    @staticmethod
    def _cached_rows_valid(cached: Sequence[DailyKlineSchema]) -> bool:
        """True when every cached bar has finite OHLC meeting OHLC ordering and
        a non-negative volume. Invalid rows must not be treated as a full hit.
        """
        for row in cached:
            for field in ("open", "high", "low", "close"):
                value = getattr(row, field)
                if value is None or not math.isfinite(value):
                    return False
            if (
                row.high < row.open
                or row.high < row.close
                or row.low > row.open
                or row.low > row.close
                or row.high < row.low
            ):
                return False
            if row.volume is not None and row.volume < 0:
                return False
        return True


class MarketDataService:
    """Orchestrates fetch-from-provider -> upsert -> query for daily bars.

    Reuses :class:`StockService` for cleaning and automatic window-widening, so
    the returned window always satisfies the >= ``min_rows`` valid-day contract;
    ``InsufficientStockDataError`` (40003) is raised when it cannot be met.
    """

    def __init__(
        self,
        stock_service: Optional[StockService] = None,
        repository: Optional[MarketDataRepository] = None,
    ) -> None:
        self._stock = stock_service or StockService()
        self._repository = repository

    def sync_daily(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
        min_rows: int = DEFAULT_MIN_KLINE_ROWS,
    ) -> List[DailyKlineSchema]:
        """Fetch + clean + widen via StockService, then upsert into MySQL."""
        rows = self._stock.get_daily_kline(
            stock_code, start_date, end_date, min_rows=min_rows
        )
        if self._repository is not None:
            self._repository.upsert_daily(rows)
        return rows

    def query_daily(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_rows: int = DEFAULT_MIN_KLINE_ROWS,
        max_stale_days: int = DEFAULT_MAX_STALE_DAYS,
    ) -> List[DailyKlineSchema]:
        """Query MySQL first, treating the cache as a full hit only when it is
        (a) at least ``min_rows`` bars, (b) covers the start of the requested
        range, and (c) fresh relative to ``end_date`` (within ``max_stale_days``).

        Otherwise it fetches via :class:`StockService` (which cleans and widens
        the window to guarantee ``min_rows`` valid rows) and upserts the result.
        Raises ``InsufficientStockDataError`` (40003) when even the widest fetch
        cannot produce ``min_rows`` valid rows.
        """
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=366))
        if self._repository is not None:
            cached = self._repository.list_daily(stock_code, start_date, end_date)
            if self._is_cache_complete(cached, start_date, end_date, min_rows, max_stale_days):
                return cached
        return self.sync_daily(stock_code, start_date, end_date, min_rows=min_rows)

    @staticmethod
    def _is_cache_complete(
        cached: Sequence[DailyKlineSchema],
        start: date,
        end: date,
        min_rows: int,
        max_stale_days: int,
    ) -> bool:
        """True when the cached window has enough bars, all bars are valid (finite
        OHLC ordering, non-negative volume), it reaches back to ``start``, and it
        ends within ``max_stale_days`` of ``end`` (freshness).
        """
        if len(cached) < min_rows:
            return False
        if not MarketDataRepository._cached_rows_valid(cached):
            return False  # invalid cached bars must not count as a full hit
        first = cached[0].trade_date
        last = cached[-1].trade_date
        if (first - start).days > max_stale_days:
            return False  # cache does not cover the beginning of the range
        if (end - last).days > max_stale_days:
            return False  # cache is stale relative to the requested end
        return True
