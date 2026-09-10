"""Assemble the V1 frozen acceptance package metadata + manifest.

Reads the C-provided frozen inputs (unchanged) plus B's read-back export and the
captured real 600519 stock snapshot, then writes an enhanced ``metadata.json``
(all fields D requested) and a ``MANIFEST.json`` with every file's SHA-256.

No network is used. Paths are under ``frozen/`` (git-ignored).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FROZEN = ROOT / "frozen"

# Real snapshot captured from push2.eastmoney.com/api/qt/stock/get
# (the endpoint ak.stock_individual_info_em wraps) during a successful window
# on 2026-09-10. The endpoint is intermittently HTTP 502 in this environment.
STOCK_SNAPSHOT = {
    "stock_code": "600519",
    "stock_name": "贵州茅台",
    "industry": "白酒Ⅱ",
    "total_market_cap": 1606517367893.1301,
    "float_market_cap": 1606517367893.1301,
}
STOCK_SOURCE = {
    "endpoint": "https://push2.eastmoney.com/api/qt/stock/get",
    "wrapped_by": "akshare.stock_individual_info_em",
    "captured_at_utc": "2026-09-10T00:00:00+00:00",
    "note": "endpoint intermittently returns HTTP 502 (HTML); captured during a successful window",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    from backend.app.quant.config import resolve_config

    c_meta = json.load((FROZEN / "metadata(1).json").open(encoding="utf-8"))

    stock_path = FROZEN / "stock_basic_600519.json"
    stock_path.write_text(json.dumps(STOCK_SNAPSHOT, ensure_ascii=False), encoding="utf-8")

    readback = FROZEN / "mysql_readback_600519.json"
    kline = FROZEN / c_meta["kline"]["file"]
    calendar = FROZEN / c_meta["calendar"]["file"]

    metadata = {
        "package": {
            "name": "V1 frozen acceptance package",
            "created_by": "B",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "target_db": "ai_quant_test",
            "note": "kline/calendar provided by C (unchanged); stock snapshot + read-back by B",
        },
        "quant_config": resolve_config().to_parameters(),
        "precision": {
            "price_ndigits": 4,
            "amount_ndigits": 2,
            "percent_ndigits": 6,
            "volume": "integer",
        },
        "expected_results": {
            "score": 33,
            "round_trips": 12,
            "orders": 24,
            "equity_points": 403,
            "total_return": -0.09165774117956027,
            "final_equity": 90834.22588204397,
        },
        "kline": dict(c_meta["kline"], sha256=sha256(kline)),
        "calendar": dict(c_meta["calendar"], sha256=sha256(calendar)),
        "stock_basic": dict(STOCK_SOURCE, file=stock_path.name, sha256=sha256(stock_path), **STOCK_SNAPSHOT),
        "readback": {
            "file": readback.name,
            "sha256": sha256(readback),
            "rows": 403,
            "mysql_version": "8.0.44",
            "target_db": "ai_quant_test",
        },
        "news_snapshot": "absent (no real news snapshot in this package)",
    }
    (FROZEN / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    package_files = [
        c_meta["kline"]["file"],
        c_meta["calendar"]["file"],
        stock_path.name,
        readback.name,
        "metadata.json",
    ]
    manifest = {
        "files": {name: sha256(FROZEN / name) for name in package_files},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (FROZEN / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
