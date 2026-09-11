"""Tests for the AKShare provider's transient retry + delayed-host fallback."""
import sys
import types
from datetime import date

import pandas as pd
import pytest

from backend.app.data.providers.akshare_provider import AKShareStockProvider
from backend.app.data.providers.base import StockDataProviderError


def _kline_frame():
    return pd.DataFrame(
        {
            "日期": ["2025-01-02", "2025-01-03"],
            "股票代码": ["600519", "600519"],
            "开盘": [100.0, 101.0],
            "收盘": [105.0, 106.0],
            "最高": [110.0, 111.0],
            "最低": [90.0, 91.0],
            "成交量": [1000, 1100],
            "成交额": [100000.0, 110000.0],
            "换手率": [1.0, 1.1],
            "涨跌幅": [0.5, 0.6],
        }
    )


def _fake_akshare(**funcs):
    module = types.ModuleType("akshare")
    for name, func in funcs.items():
        setattr(module, name, func)
    return module


def test_kline_retries_transient_error_then_succeeds(monkeypatch):
    monkeypatch.setattr(AKShareStockProvider, "retry_delay_seconds", 0)
    calls = {"n": 0}

    def hist(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("connection reset")
        return _kline_frame()

    monkeypatch.setitem(sys.modules, "akshare", _fake_akshare(stock_zh_a_hist=hist))

    frame = AKShareStockProvider().get_daily_kline("600519", date(2025, 1, 1), date(2025, 1, 5))

    assert len(frame) == 2
    assert calls["n"] == 2  # one transient failure, then success


def test_kline_raises_after_retries_exhausted(monkeypatch):
    monkeypatch.setattr(AKShareStockProvider, "retry_delay_seconds", 0)
    monkeypatch.setattr(AKShareStockProvider, "retry_attempts", 3)
    calls = {"n": 0}

    def hist(**kwargs):
        calls["n"] += 1
        raise ConnectionError("connection reset")

    monkeypatch.setitem(sys.modules, "akshare", _fake_akshare(stock_zh_a_hist=hist))

    with pytest.raises(StockDataProviderError):
        AKShareStockProvider().get_daily_kline("600519", date(2025, 1, 1), date(2025, 1, 5))

    assert calls["n"] == 3  # bounded attempts


def test_stock_info_falls_back_to_delayed_host(monkeypatch):
    import requests

    monkeypatch.setattr(AKShareStockProvider, "retry_delay_seconds", 0)

    def info(**kwargs):
        raise ConnectionError("connection reset")

    monkeypatch.setitem(sys.modules, "akshare", _fake_akshare(stock_individual_info_em=info))

    class _Response:
        def json(self):
            return {
                "data": {
                    "f57": "600519",
                    "f58": "贵州茅台",
                    "f116": 1606517367893.13,
                    "f117": 1606517367893.13,
                    "f127": "白酒Ⅱ",
                }
            }

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _Response())

    result = AKShareStockProvider().get_stock_info("600519")

    assert result["stock_code"] == "600519"
    assert result["stock_name"] == "贵州茅台"
    assert result["industry"] == "白酒Ⅱ"
    assert result["total_market_cap"] == 1606517367893.13


def test_stock_info_raises_when_fallback_also_fails(monkeypatch):
    import requests

    monkeypatch.setattr(AKShareStockProvider, "retry_delay_seconds", 0)

    def info(**kwargs):
        raise ConnectionError("connection reset")

    monkeypatch.setitem(sys.modules, "akshare", _fake_akshare(stock_individual_info_em=info))

    def failing_get(*args, **kwargs):
        raise ConnectionError("fallback down")

    monkeypatch.setattr(requests, "get", failing_get)

    with pytest.raises(StockDataProviderError):
        AKShareStockProvider().get_stock_info("600519")


def test_kline_falls_back_to_delayed_host(monkeypatch):
    import requests

    monkeypatch.setattr(AKShareStockProvider, "retry_delay_seconds", 0)

    def hist(**kwargs):
        raise ConnectionError("connection reset")

    monkeypatch.setitem(sys.modules, "akshare", _fake_akshare(stock_zh_a_hist=hist))

    class _Response:
        def json(self):
            return {
                "data": {
                    "klines": [
                        "2025-01-02,100.0,105.0,110.0,90.0,1000,100000.0,5.0,0.5,0.5,1.0",
                        "2025-01-03,101.0,106.0,111.0,91.0,1100,110000.0,5.0,0.6,0.6,1.1",
                    ]
                }
            }

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _Response())

    frame = AKShareStockProvider().get_daily_kline("600519", date(2025, 1, 1), date(2025, 1, 5))

    assert list(frame["trade_date"]) == [date(2025, 1, 2), date(2025, 1, 3)]
    assert list(frame["close"]) == [105.0, 106.0]

