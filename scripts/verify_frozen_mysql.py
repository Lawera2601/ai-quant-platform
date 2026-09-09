"""Real-MySQL frozen-sample in/read verification (offline, no AKShare calls).

Reads the frozen 600519 qfq snapshot + real A-share trade-date calendar from
``frozen/`` (JSON, unchanged), loads them into the ``ai_quant_test`` MySQL
database, reads them back through the ORM, and compares the full quant output
(direct computation vs DB read-back) under the canonical 4/2/6 precision.

Runs ONLY against ``ai_quant_test``; refuses to touch any other database.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("MYSQL_DATABASE", "ai_quant_test")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    from backend.app.core.config import get_settings
    from backend.app.db.migrations import apply_migrations
    from backend.app.db.session import SessionLocal, engine
    from backend.app.data.trading_calendar import TradingCalendarProvider
    from backend.app.quant.backtest import run_backtest
    from backend.app.quant.scoring import calculate_quant_score
    from backend.app.schemas.stock import DailyKlineSchema
    from backend.app.services.market_data_service import _round_daily, MarketDataRepository
    import pandas as pd

    settings = get_settings()
    database = settings.mysql_database
    if database != "ai_quant_test":
        raise SystemExit(f"refusing to run against non-test database: {database}")

    frozen = PROJECT_ROOT / "frozen"
    kline_file = frozen / "600519_qfq_20250101_20260831.json"
    calendar_file = frozen / "a_share_trade_dates.json"
    metadata = json.load((frozen / "metadata(1).json").open(encoding="utf-8"))

    # --- integrity check against metadata ---
    kline_hash = _sha256(kline_file)
    calendar_hash = _sha256(calendar_file)
    print("kline   sha256:", kline_hash, "| match:", kline_hash == metadata["kline"]["sha256"])
    print("calendar sha256:", calendar_hash, "| match:", calendar_hash == metadata["calendar"]["sha256"])

    kline = json.load(kline_file.open(encoding="utf-8"))
    calendar = json.load(calendar_file.open(encoding="utf-8"))
    print("frozen kline rows:", len(kline), "| calendar dates:", len(calendar))

    bars = [DailyKlineSchema(**record) for record in kline]
    cal = TradingCalendarProvider(trade_dates=[date.fromisoformat(day) for day in calendar])

    # --- migrate the test DB ---
    print("applying migrations to:", database)
    apply_migrations(engine)

    start = min(b.trade_date for b in bars)
    end = max(b.trade_date for b in bars)
    trading_count = cal.count_between(start, end)
    print("actual window:", start, "->", end, "| expected trading days:", trading_count)

    # --- load frozen sample into MySQL (upsert rounds to 4/2/6) ---
    db = SessionLocal()
    try:
        repository = MarketDataRepository(db)
        repository.upsert_daily(bars)
        readback = repository.list_daily("600519", start, end)
    finally:
        db.close()
    print("rows now in stock_daily:", len(readback))

    # --- direct computation (canonical precision) ---
    direct_bars = [_round_daily(b) for b in bars]
    direct_frame = pd.DataFrame([b.model_dump() for b in direct_bars])
    # --- read-back computation (already canonical from DB) ---
    readback_frame = pd.DataFrame([b.model_dump() for b in readback])

    print("direct data == read-back data:", direct_frame.reset_index(drop=True).equals(readback_frame.reset_index(drop=True)))

    direct_score = calculate_quant_score(direct_frame)
    readback_score = calculate_quant_score(readback_frame)
    direct_bt = run_backtest(direct_frame)
    readback_bt = run_backtest(readback_frame)

    def _summary_backtest(result):
        return {
            "total_return": result["total_return"],
            "trade_count": result.get("trade_count"),
            "final_equity": result["final_equity"],
            "equity_points": len(result["equity_curve"]),
        }

    score_ok = direct_score == readback_score
    backtest_ok = _summary_backtest(direct_bt) == _summary_backtest(readback_bt)
    print("score direct:", direct_score["score"], "| readback:", readback_score["score"], "| equal:", score_ok)
    print("backtest direct:", _summary_backtest(direct_bt))
    print("backtest readback:", _summary_backtest(readback_bt), "| equal:", backtest_ok)

    print("RESULT: score_equal=%s backtest_equal=%s data_equal=%s" % (score_ok, backtest_ok, direct_frame.reset_index(drop=True).equals(readback_frame.reset_index(drop=True))))
    return 0 if (score_ok and backtest_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
