from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import BIGINT, DECIMAL, Date, DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class StockIndicator(Base):
    __tablename__ = "stock_indicator"
    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date", name="uk_indicator_stock_date"),
        Index("idx_indicator_stock", "stock_code"),
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    ma5: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    ma10: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    ma20: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    ma60: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    macd: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(16, 6))
    macd_signal: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(16, 6))
    macd_hist: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(16, 6))
    rsi14: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 6))
    boll_upper: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    boll_middle: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    boll_lower: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
