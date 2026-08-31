"""Run a real AKShare daily-kline smoke test for one A-share stock."""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.data.providers.akshare_provider import AKShareStockProvider  # noqa: E402


def parse_args() -> argparse.Namespace:
    today = date.today()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock-code", default="600519")
    parser.add_argument("--start-date", type=date.fromisoformat, default=today - timedelta(days=30))
    parser.add_argument("--end-date", type=date.fromisoformat, default=today)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provider = AKShareStockProvider()

    try:
        data = provider.get_daily_kline(
            stock_code=args.stock_code,
            start_date=args.start_date,
            end_date=args.end_date,
        )
    except Exception as exc:  # Provider errors are reported verbatim for smoke-test diagnosis.
        print(f"AKShare validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"AKShare validation succeeded: stock_code={args.stock_code}, "
        f"rows={len(data)}, start={data['trade_date'].min()}, "
        f"end={data['trade_date'].max()}"
    )
    print(data.tail(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
