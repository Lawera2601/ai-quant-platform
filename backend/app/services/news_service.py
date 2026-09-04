"""News service: fetch (AKShare) -> normalize -> persist (stock_news) -> query.

Satisfies the ``NewsAnalysisService`` protocol consumed by D's AI context
(``get_news(stock_code, limit) -> Sequence[NewsItemContext]``), so the same
unified news structure feeds both the public news API and the AI pipeline.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from sqlalchemy.orm import Session

from backend.app.data.providers.akshare_provider import AKShareStockProvider
from backend.app.data.providers.base import StockDataProvider
from backend.app.models.stock_news import StockNews
from backend.app.schemas.ai import NewsItemContext

DEFAULT_NEWS_LIMIT = 10
MAX_NEWS_LIMIT = 50


class NewsRepository:
    """Persist and read ``stock_news`` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, items: Sequence[dict]) -> int:
        """Insert or update news items, deduplicated by stock + url/title."""
        count = 0
        for item in items:
            record = self._find(item)
            if record is None:
                self._session.add(
                    StockNews(
                        stock_code=item["stock_code"],
                        title=item["title"],
                        summary=item.get("summary"),
                        source=item.get("source"),
                        publish_time=item.get("publish_time"),
                        url=item.get("url"),
                    )
                )
            else:
                record.title = item["title"]
                record.summary = item.get("summary")
                record.source = item.get("source")
                record.publish_time = item.get("publish_time")
                record.url = item.get("url")
            count += 1
        self._session.commit()
        return count

    def list_by_stock(self, stock_code: str, limit: int) -> List[StockNews]:
        records = (
            self._session.query(StockNews)
            .filter(StockNews.stock_code == stock_code)
            .order_by(StockNews.publish_time.desc())
            .limit(limit)
            .all()
        )
        return records

    def _find(self, item: dict) -> Optional[StockNews]:
        query = self._session.query(StockNews).filter(
            StockNews.stock_code == item["stock_code"]
        )
        url = item.get("url")
        if url:
            query = query.filter(StockNews.url == url)
        else:
            query = query.filter(StockNews.title == item["title"])
        return query.first()


class NewsService:
    """Implements the ``NewsAnalysisService`` protocol over provider + repository."""

    def __init__(
        self,
        provider: Optional[StockDataProvider] = None,
        repository: Optional[NewsRepository] = None,
        limit: int = DEFAULT_NEWS_LIMIT,
    ) -> None:
        self._provider = provider or AKShareStockProvider()
        self._repository = repository
        self._default_limit = min(max(limit, 1), MAX_NEWS_LIMIT)

    def get_news(self, stock_code: str, limit: int = DEFAULT_NEWS_LIMIT) -> Sequence[NewsItemContext]:
        """Return a bounded, normalized news list.

        Reads from MySQL first; on an empty cache it fetches from AKShare and
        persists the result, then returns it.
        """
        bound = min(max(limit, 1), MAX_NEWS_LIMIT)
        if self._repository is not None:
            stored = self._repository.list_by_stock(stock_code, bound)
            if stored:
                return [self._to_item(record) for record in stored[:bound]]
        raw_items = self._provider.get_stock_news(stock_code, limit=bound)
        if self._repository is not None and raw_items:
            self._repository.upsert(raw_items)
        return [self._from_raw(item) for item in raw_items[:bound]]

    @staticmethod
    def _from_raw(item: dict) -> NewsItemContext:
        return NewsItemContext(
            title=item["title"],
            summary=item.get("summary"),
            source=item.get("source"),
            publish_time=item.get("publish_time"),
            url=item.get("url"),
        )

    @staticmethod
    def _to_item(record: StockNews) -> NewsItemContext:
        return NewsItemContext(
            title=record.title,
            summary=record.summary,
            source=record.source,
            publish_time=record.publish_time,
            url=record.url,
        )
