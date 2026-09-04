from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.migrations import apply_migrations
from backend.app.schemas.stock import DailyKlineSchema, StockBasicSchema
from backend.app.services.market_data_service import MarketDataRepository

STOCK_CODE = "600519"


def _session() -> Session:
    engine = create_engine("sqlite://")
    apply_migrations(engine)
    return Session(bind=engine)


def _bar(stock_code, trade_date, close=105.0):
    return DailyKlineSchema(
        stock_code=stock_code,
        trade_date=trade_date,
        open=100.0,
        high=110.0,
        low=90.0,
        close=close,
        volume=1000,
        amount=100000.0,
        turnover_rate=0.01,
        change_pct=0.02,
    )


def test_upsert_daily_inserts_and_queries_back():
    with _session() as session:
        repository = MarketDataRepository(session)
        start = date(2025, 1, 1)
        rows = [_bar(STOCK_CODE, start + timedelta(days=i)) for i in range(3)]

        count = repository.upsert_daily(rows)

        assert count == 3
        back = repository.list_daily(STOCK_CODE, start, date(2025, 1, 3))
        assert len(back) == 3
        assert back[0].trade_date == start
        # ascending by trade_date
        assert back == sorted(back, key=lambda r: r.trade_date)


def test_upsert_daily_updates_instead_of_duplicating():
    with _session() as session:
        repository = MarketDataRepository(session)
        trade_date = date(2025, 1, 1)
        repository.upsert_daily([_bar(STOCK_CODE, trade_date, close=105.0)])
        repository.upsert_daily([_bar(STOCK_CODE, trade_date, close=108.5)])

        back = repository.list_daily(STOCK_CODE, trade_date, trade_date)
        assert len(back) == 1
        assert back[0].close == 108.5


def test_get_stock_basic_round_trips_and_returns_none_when_absent():
    with _session() as session:
        repository = MarketDataRepository(session)

        assert repository.get_stock_basic(STOCK_CODE) is None

        repository.upsert_stock_basic(
            StockBasicSchema(
                stock_code=STOCK_CODE,
                stock_name="贵州茅台",
                industry="酿酒行业",
                total_market_cap=1.0,
                float_market_cap=1.0,
            )
        )

        stored = repository.get_stock_basic(STOCK_CODE)
        assert stored is not None
        assert stored.stock_name == "贵州茅台"
        assert stored.industry == "酿酒行业"
