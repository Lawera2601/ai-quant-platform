from datetime import date
from typing import Dict, Iterable

import pandas as pd

from backend.app.data.providers.base import (
    EmptyStockDataError,
    InvalidStockCodeError,
    StockDataProvider,
    StockDataProviderError,
    StockDataSchemaError,
)


class AKShareStockProvider(StockDataProvider):
    field_mapping: Dict[str, str] = {
        "日期": "trade_date",
        "股票代码": "stock_code",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "换手率": "turnover_rate",
        "涨跌幅": "change_pct",
    }
    required_source_fields = ("日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额")
    output_columns = (
        "stock_code",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
        "turnover_rate",
        "change_pct",
    )

    def get_daily_kline(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        stock_code = self._normalize_stock_code(stock_code)
        self._validate_dates(start_date, end_date)
        if adjust != "qfq":
            raise ValueError("V1 daily kline only supports qfq adjust")

        try:
            import akshare as ak

            raw_data = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust=adjust,
            )
        except StockDataProviderError:
            raise
        except Exception as exc:
            raise StockDataProviderError(f"AKShare request failed for {stock_code}: {exc}") from exc

        return self._normalize_daily_kline(raw_data, stock_code)

    def _normalize_daily_kline(self, raw_data: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        if raw_data is None or raw_data.empty:
            raise EmptyStockDataError(f"AKShare returned empty daily kline for {stock_code}")

        missing_fields = [field for field in self.required_source_fields if field not in raw_data.columns]
        if missing_fields:
            raise StockDataSchemaError(f"AKShare daily kline missing fields: {missing_fields}")

        data = raw_data.rename(columns=self.field_mapping).copy()
        if "stock_code" not in data.columns:
            data["stock_code"] = stock_code
        data["stock_code"] = data["stock_code"].astype(str).str.zfill(6)
        data["trade_date"] = pd.to_datetime(data["trade_date"], errors="coerce").dt.date

        for column in ("open", "high", "low", "close", "volume", "amount", "turnover_rate", "change_pct"):
            if column in data.columns:
                data[column] = pd.to_numeric(data[column], errors="coerce")

        for percent_column in ("turnover_rate", "change_pct"):
            if percent_column in data.columns:
                data[percent_column] = data[percent_column] / 100

        data = data.where(pd.notnull(data), None)
        if data["trade_date"].isna().any():
            raise StockDataSchemaError("AKShare daily kline contains invalid trade_date values")

        for column in self._numeric_required_columns():
            if column in data.columns and data[column].isna().any():
                raise StockDataSchemaError(f"AKShare daily kline contains invalid numeric values in {column}")

        for column in self.output_columns:
            if column not in data.columns:
                data[column] = None
        return data.loc[:, self.output_columns].sort_values("trade_date").reset_index(drop=True)

    @staticmethod
    def _normalize_stock_code(stock_code: str) -> str:
        if not isinstance(stock_code, str):
            raise InvalidStockCodeError("stock_code must be a string")
        normalized = stock_code.strip()
        if not (normalized.isdigit() and len(normalized) == 6):
            raise InvalidStockCodeError("stock_code must be a 6-digit string")
        return normalized

    @staticmethod
    def _validate_dates(start_date: date, end_date: date) -> None:
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            raise ValueError("start_date and end_date must be date instances")
        if start_date > end_date:
            raise ValueError("start_date must be earlier than or equal to end_date")

    @staticmethod
    def _numeric_required_columns() -> Iterable[str]:
        return ("open", "high", "low", "close", "volume", "amount")
