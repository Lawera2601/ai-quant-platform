from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class StockBasicSchema(BaseModel):
    stock_code: str = Field(pattern=r"^\d{6}$")
    stock_name: str
    industry: Optional[str] = None
    total_market_cap: Optional[float] = None
    float_market_cap: Optional[float] = None


class DailyKlineSchema(BaseModel):
    stock_code: str = Field(pattern=r"^\d{6}$")
    trade_date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    change_pct: Optional[float] = None
