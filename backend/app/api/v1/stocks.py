from datetime import date
from typing import List, Optional

from fastapi import APIRouter

from backend.app.core.errors import DataProviderError, InvalidParameterError
from backend.app.data.providers.base import InvalidStockCodeError, StockDataProviderError
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.stock import DailyKlineSchema
from backend.app.services.stock_service import StockService

router = APIRouter()
_service = StockService()

_SUPPORTED_PERIOD = "daily"


@router.get("/stocks/{stock_code}/kline", response_model=ApiResponse[List[DailyKlineSchema]])
def get_stock_kline(
    stock_code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = "daily",
) -> ApiResponse[List[DailyKlineSchema]]:
    if period != _SUPPORTED_PERIOD:
        raise InvalidParameterError("V1 kline only supports the daily period")
    try:
        data = _service.get_daily_kline(stock_code, start_date, end_date)
    except InvalidStockCodeError as exc:
        raise InvalidParameterError(str(exc)) from exc
    except StockDataProviderError as exc:
        raise DataProviderError(str(exc)) from exc
    return ApiResponse(data=data)
