from datetime import date

import pandas as pd
import pytest

from backend.app.data.providers.akshare_provider import AKShareStockProvider
from backend.app.data.providers.base import InvalidStockCodeError, StockDataSchemaError


def test_normalize_daily_kline_converts_fields_and_percentages():
    provider = AKShareStockProvider()
    raw_data = pd.DataFrame(
        [
            {
                "日期": "2026-08-28",
                "开盘": "1400.00",
                "收盘": "1420.00",
                "最高": "1430.00",
                "最低": "1395.00",
                "成交量": "100000",
                "成交额": "142000000",
                "换手率": "0.35",
                "涨跌幅": "1.2",
            }
        ]
    )

    result = provider._normalize_daily_kline(raw_data, "600519")

    assert list(result.columns) == list(provider.output_columns)
    assert result.loc[0, "stock_code"] == "600519"
    assert result.loc[0, "trade_date"] == date(2026, 8, 28)
    assert result.loc[0, "turnover_rate"] == pytest.approx(0.0035)
    assert result.loc[0, "change_pct"] == pytest.approx(0.012)


def test_normalize_stock_code_requires_string():
    provider = AKShareStockProvider()

    with pytest.raises(InvalidStockCodeError):
        provider.get_daily_kline(600519, date(2026, 1, 1), date(2026, 1, 2))


def test_normalize_daily_kline_rejects_missing_required_fields():
    provider = AKShareStockProvider()

    with pytest.raises(StockDataSchemaError):
        provider._normalize_daily_kline(pd.DataFrame([{"日期": "2026-08-28"}]), "600519")
