from sqlalchemy import UniqueConstraint

from backend.app import models  # noqa: F401
from backend.app.db.base import Base


def test_all_v1_tables_are_registered():
    assert set(Base.metadata.tables) == {
        "stock_basic",
        "stock_daily",
        "stock_indicator",
        "stock_news",
        "backtest_result",
        "ai_analysis",
    }


def test_stock_daily_unique_constraint_matches_design():
    constraints = Base.metadata.tables["stock_daily"].constraints
    unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("stock_code", "trade_date") in unique_columns
