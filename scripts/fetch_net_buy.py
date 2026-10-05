"""GitHub Actions에서 실행: SEIBro 국내 투자자 순매수 상위를 받아 snapshots/net_buy.json에 저장.

Streamlit Cloud 서버에서 SEIBro가 막혀 있을 때를 위한 대체 경로.
GitHub 서버에서는 SEIBro 접속이 된다. 저장소에 커밋되면 Streamlit Cloud가 자동으로 새 파일을 반영한다.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import data  # noqa: E402

data.SEIBRO_TIMEOUT = (15, 40)  # 배치 작업은 좀 더 기다려도 된다


def main():
    result = data.fetch_net_buy_live()
    out = {"updated": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")}
    for k in ("1w", "1m"):
        v = result[k]
        rows = data.attach_tickers([dict(r) for r in v["rows"]])
        out[k] = {"start": v["start"].isoformat(), "end": v["end"].isoformat(), "rows": rows}
        mapped = sum(1 for r in rows if r.get("ticker"))
        print(f"{k}: {v['start']} ~ {v['end']} {len(rows)}행, 티커 연결 {mapped}/{len(rows)}")
    data.SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data.SNAPSHOT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"저장: {data.SNAPSHOT_FILE}")


if __name__ == "__main__":
    main()
