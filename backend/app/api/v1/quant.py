from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.data.providers.base import InvalidStockCodeError, StockDataProviderError
from backend.app.schemas.common import ApiResponse
from backend.app.services.quant_service import QuantService

router = APIRouter()
_service = QuantService()


class BacktestRequest(BaseModel):
    stock_code: str = Field(pattern=r"^\d{6}$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None


@router.get("/stocks/{stock_code}/indicators", response_model=ApiResponse[List[Dict[str, Any]]])
def get_stock_indicators(
    stock_code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> ApiResponse[List[Dict[str, Any]]]:
    try:
        data = _service.get_indicators(stock_code, start_date, end_date)
    except InvalidStockCodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except StockDataProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return ApiResponse(data=data)


@router.get("/stocks/{stock_code}/score", response_model=ApiResponse[Dict[str, Any]])
def get_stock_score(
    stock_code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> ApiResponse[Dict[str, Any]]:
    try:
        data = _service.get_score(stock_code, start_date, end_date)
    except InvalidStockCodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except StockDataProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return ApiResponse(data=data)


@router.post("/backtests", response_model=ApiResponse[Dict[str, Any]])
def run_stock_backtest(request: BacktestRequest) -> ApiResponse[Dict[str, Any]]:
    try:
        data = _service.run_backtest(request.stock_code, request.start_date, request.end_date)
    except InvalidStockCodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except StockDataProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return ApiResponse(data=data)
