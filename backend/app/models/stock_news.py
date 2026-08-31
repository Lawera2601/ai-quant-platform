from datetime import datetime
from typing import Optional

from sqlalchemy import BIGINT, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class StockNews(Base):
    __tablename__ = "stock_news"
    __table_args__ = (
        Index("idx_news_stock", "stock_code"),
        Index("idx_news_publish_time", "publish_time"),
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(200))
    publish_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
