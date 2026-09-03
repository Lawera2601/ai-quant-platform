from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.app.core.errors import InsufficientStockDataError
from backend.app.quant.backtest import run_backtest
from backend.app.quant.config import ConfigInput
from backend.app.quant.indicators import INDICATOR_COLUMNS, calculate_indicators
from backend.app.quant.scoring import calculate_quant_score
from backend.app.quant.serialization import dataframe_records, to_json_safe
from backend.app.quant.validators import InsufficientDataError as QuantInsufficientDataError
from backend.app.services.stock_service import StockService


class QuantService:
    """FastAPI-layer wrapper around C's deterministic quant core.

    This service only fetches cleaned qfq daily data (via :class:`StockService`)
    and delegates indicators / scoring / backtest computation to C's quant module.
    It never re-implements the calculation.
    """

    def __init__(
        self,
        stock_service: Optional[StockService] = None,
        config: ConfigInput = None,
    ) -> None:
        self._stock = stock_service or StockService()
        self._config = config

    def get_indicators(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        frame = self._stock.get_daily_kline_frame(stock_code, start_date, end_date)
        indicators = self._run(calculate_indicators, frame, self._config)
        return dataframe_records(indicators.loc[:, INDICATOR_COLUMNS])

    def get_score(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        frame = self._stock.get_daily_kline_frame(stock_code, start_date, end_date)
        return to_json_safe(self._run(calculate_quant_score, frame, self._config))

    def run_backtest(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        frame = self._stock.get_daily_kline_frame(stock_code, start_date, end_date)
        return to_json_safe(self._run(run_backtest, frame, self._config))

    @staticmethod
    def _run(func, frame: pd.DataFrame, config: ConfigInput):
        try:
            return func(frame, config)
        except QuantInsufficientDataError as exc:
            raise InsufficientStockDataError(str(exc)) from exc
