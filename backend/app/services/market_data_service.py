"""Market-data (stock_basic / stock_daily) persistence: MySQL upsert + query.

This is the DB half of the V1 data pipeline: the API keeps its existing
contract, while this module lets B pull real qfq data into MySQL and read it
back (System Design :: Service 层：查询 MySQL -> 缺失时调 Provider -> 标准化 ->
Upsert MySQL -> 返回).

Repository methods are portable across the SQLite test database and MySQL 8
(no MySQL-specific DDL is used), so the upsert/query logic is unit-testable
without a running MySQL instance.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional, Sequence

from sqlalchemy.orm import Session

from backend.app.core.errors import StockNotFoundError
from backend.app.data.providers.akshare_provider import AKShareStockProvider
from backend.app.data.providers.base import StockDataProvider
from backend.app.models.stock_basic import StockBasic
from backend.app.models.stock_daily import StockDaily
from backend.app.schemas.stock import DailyKlineSchema, StockBasicSchema


class MarketDataRepository:
    """Upsert/read access to ``stock_basic`` and ``stock_daily``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_stock_basic(self, item: StockBasicSchema) -> None:
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

    def get_stock_basic(self, stock_code: str) -> Optional[StockBasicSchema]:
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

    def upsert_daily(self, rows: Sequence[DailyKlineSchema]) -> int:
        """Insert or update daily bars keyed by ``(stock_code, trade_date)``."""
        count = 0
        for row in rows:
            record = (
                self._session.query(StockDaily)
                .filter_by(stock_code=row.stock_code, trade_date=row.trade_date)
                .one_or_none()
            )
            if record is None:
                self._session.add(StockDaily(**row.model_dump()))
            else:
                payload = row.model_dump()
                payload.pop("stock_code", None)
                payload.pop("trade_date", None)
                for field, value in payload.items():
                    setattr(record, field, value)
            count += 1
        self._session.commit()
        return count

    def list_daily(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[DailyKlineSchema]:
        query = self._session.query(StockDaily).filter(
            StockDaily.stock_code == stock_code
        )
        if start_date is not None:
            query = query.filter(StockDaily.trade_date >= start_date)
        if end_date is not None:
            query = query.filter(StockDaily.trade_date <= end_date)
        records = query.order_by(StockDaily.trade_date.asc()).all()
        return [self._to_schema(record) for record in records]

    @staticmethod
    def _to_schema(record: StockDaily) -> DailyKlineSchema:
        return DailyKlineSchema(
            stock_code=record.stock_code,
            trade_date=record.trade_date,
            open=record.open,
            high=record.high,
            low=record.low,
            close=record.close,
            volume=record.volume,
            amount=record.amount,
            turnover_rate=record.turnover_rate,
            change_pct=record.change_pct,
        )


class MarketDataService:
    """Orchestrates fetch-from-provider -> upsert -> query for daily bars."""

    def __init__(
        self,
        provider: Optional[StockDataProvider] = None,
        repository: Optional[MarketDataRepository] = None,
    ) -> None:
        self._provider = provider or AKShareStockProvider()
        self._repository = repository

    def sync_daily(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyKlineSchema]:
        frame = self._provider.get_daily_kline(
            stock_code, start_date, end_date, adjust="qfq"
        )
        rows = [DailyKlineSchema(**record) for record in frame.to_dict("records")]
        if self._repository is not None:
            self._repository.upsert_daily(rows)
        return rows

    def query_daily(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[DailyKlineSchema]:
        """Query MySQL first; sync from the provider when the cache is empty.

        Raises ``StockNotFoundError`` (40002) when the provider also has no data.
        """
        if self._repository is not None:
            cached = self._repository.list_daily(stock_code, start_date, end_date)
            if cached:
                return cached
        fetched = self.sync_daily(
            stock_code,
            start_date or date(1970, 1, 1),
            end_date or date.today(),
        )
        if not fetched:
            raise StockNotFoundError(f"no daily data found for {stock_code}")
        return fetched
