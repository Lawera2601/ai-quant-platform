from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, DECIMAL, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class StockBasic(Base):
    __tablename__ = "stock_basic"

    stock_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    stock_name: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    total_market_cap: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 2))
    float_market_cap: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 2))
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
