from datetime import date, timedelta

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.data.providers.base import StockDataProvider
from backend.app.main import app
from backend.app.services.quant_service import QuantService
from backend.app.services.stock_service import StockService

STOCK_CODE = "600519"
START_DATE = date(2025, 1, 1)
ROWS = 120


def _make_frame(rows, start_date, stock_code=STOCK_CODE):
    dates = [start_date + timedelta(days=i) for i in range(rows)]
    return pd.DataFrame(
        {
            "stock_code": [stock_code] * rows,
            "trade_date": dates,
            "open": [100.0] * rows,
            "high": [110.0] * rows,
            "low": [90.0] * rows,
            "close": [105.0] * rows,
            "volume": [1000] * rows,
            "amount": [100000.0] * rows,
            "turnover_rate": [0.01] * rows,
            "change_pct": [0.02] * rows,
        }
    )


class FakeProvider(StockDataProvider):
    def get_daily_kline(self, stock_code, start_date, end_date, adjust="qfq"):
        return _make_frame(ROWS, start_date, stock_code)


def _client():
    import backend.app.api.v1.quant as quant_module

    service = QuantService(stock_service=StockService(provider=FakeProvider()))
    quant_module._service = service
    return TestClient(app)


def test_indicators_returns_series():
    response = _client().get(f"/api/v1/stocks/{STOCK_CODE}/indicators")

    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) == ROWS
    item = data[-1]
    for key in ("trade_date", "ma5", "ma10", "ma20", "ma60", "macd", "rsi14"):
        assert key in item


def test_score_returns_scoring_fields():
    response = _client().get(f"/api/v1/stocks/{STOCK_CODE}/score")

    assert response.status_code == 200
    data = response.json()["data"]
    for key in ("stock_code", "score", "trend_score", "momentum_score", "volume_score", "risk_score", "level", "reasons"):
        assert key in data
    assert isinstance(data["score"], (int, float))


def test_backtest_returns_equity_curve_and_summary():
    response = _client().post(
        "/api/v1/backtests", json={"stock_code": STOCK_CODE}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "equity_curve" in data
    assert "initial_cash" in data
    assert "final_equity" in data
    assert "total_return" in data
    assert data["initial_cash"] == 100000.0
    first_point = data["equity_curve"][0]
    assert set(first_point.keys()) == {"trade_date", "equity"}


def test_backtest_rejects_invalid_stock_code():
    response = _client().post("/api/v1/backtests", json={"stock_code": "abc"})

    assert response.status_code == 400
    assert response.json()["code"] == 40001
