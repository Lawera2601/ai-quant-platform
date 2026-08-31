from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import BIGINT, DECIMAL, Date, DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class StockDaily(Base):
    __tablename__ = "stock_daily"
    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date", name="uk_stock_trade_date"),
        Index("idx_stock_code", "stock_code"),
        Index("idx_trade_date", "trade_date"),
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    high: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    low: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    close: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    volume: Mapped[Optional[int]] = mapped_column(BIGINT)
    amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(24, 2))
    turnover_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 6))
    change_pct: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 6))
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
