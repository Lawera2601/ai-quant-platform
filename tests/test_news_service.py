from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.migrations import apply_migrations
from backend.app.schemas.ai import NewsItemContext
from backend.app.services.news_service import NewsRepository, NewsService

STOCK_CODE = "600519"


class FakeNewsProvider:
    def __init__(self, items):
        self.items = items
        self.calls = 0

    def get_stock_news(self, stock_code, limit=10):
        self.calls += 1
        return self.items[:limit]


def _session() -> Session:
    engine = create_engine("sqlite://")
    apply_migrations(engine)
    return Session(bind=engine)


def _raw_items():
    return [
        {
            "stock_code": STOCK_CODE,
            "title": "公司发布年度业绩预告",
            "summary": "业绩预增",
            "source": "东方财富",
            "publish_time": datetime(2026, 8, 31, 9, 30),
            "url": "http://finance.eastmoney.com/a/1.html",
        },
        {
            "stock_code": STOCK_CODE,
            "title": "召开临时股东大会",
            "summary": None,
            "source": "交易所",
            "publish_time": datetime(2026, 8, 30, 14, 0),
            "url": "http://finance.eastmoney.com/a/2.html",
        },
    ]


def test_get_news_fetches_persists_and_then_serves_from_db():
    provider = FakeNewsProvider(_raw_items())
    with _session() as session:
        repository = NewsRepository(session)
        service = NewsService(provider=provider, repository=repository)

        first = service.get_news(STOCK_CODE, limit=10)

        assert provider.calls == 1
        assert len(first) == 2
        assert all(isinstance(item, NewsItemContext) for item in first)
        assert first[0].title == "公司发布年度业绩预告"

        second = service.get_news(STOCK_CODE, limit=10)

        assert provider.calls == 1  # served from the DB cache, provider not called again
        assert len(second) == 2


def test_get_news_respects_limit():
    provider = FakeNewsProvider(_raw_items())
    with _session() as session:
        service = NewsService(provider=provider, repository=NewsRepository(session))

        items = service.get_news(STOCK_CODE, limit=1)

        assert len(items) == 1


def test_news_service_works_without_repository():
    provider = FakeNewsProvider(_raw_items())
    service = NewsService(provider=provider)

    items = service.get_news(STOCK_CODE, limit=10)

    assert len(items) == 2
    assert isinstance(items[0], NewsItemContext)
