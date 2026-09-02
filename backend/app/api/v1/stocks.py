from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from backend.app.data.providers.base import (
    InsufficientStockDataError,
    InvalidStockCodeError,
    StockDataProviderError,
)
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.stock import DailyKlineSchema
from backend.app.services.stock_service import StockService

router = APIRouter()
_service = StockService()


@router.get("/stocks/{stock_code}/kline", response_model=ApiResponse[List[DailyKlineSchema]])
def get_stock_kline(
    stock_code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> ApiResponse[List[DailyKlineSchema]]:
    try:
        data = _service.get_daily_kline(stock_code, start_date, end_date)
    except InvalidStockCodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except InsufficientStockDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except StockDataProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return ApiResponse(data=data)
