"""GitHub Actions에서 실행: SEIBro 국내 투자자 순매수 상위를 받아 snapshots/net_buy.json에 저장.

Streamlit Cloud 서버에서는 SEIBro 접속이 막혀 있어서, GitHub 서버에서 받아 저장소에 커밋한다.
커밋되면 Streamlit Cloud가 자동으로 새 파일을 반영하고, 웹페이지는 이 파일만 읽는다.

SEIBro 종목명은 옛 표기(예: 'SNDSK CRP ORD WI')라서, 티커로 Yahoo의 현재 회사명을 찾아 함께 저장한다.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import data  # noqa: E402

data.SEIBRO_TIMEOUT = (15, 40)  # 배치 작업은 좀 더 기다려도 된다


def fix_ticker(row: dict) -> dict:
    """미국 상장 티커가 아니면(예: 런던 0LO6.L) 종목명으로 다시 찾는다."""
    if not data.is_us_ticker(row.get("ticker")):
        q = data.yahoo_search(row["name"])
        row["ticker"] = q["symbol"] if q else None
    return row


def current_name(ticker: str):
    q = data.yahoo_search(ticker, exact=ticker)
    return (q.get("longname") or q.get("shortname")) if q else None


def main():
    result = data.fetch_net_buy_live()
    out = {"updated": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")}

    all_rows = {}
    for k in ("1w", "1m"):
        rows = data.attach_tickers([dict(r) for r in result[k]["rows"]])
        with ThreadPoolExecutor(max_workers=8) as ex:
            rows = list(ex.map(fix_ticker, rows))
        all_rows[k] = rows

    tickers = sorted({r["ticker"] for rows in all_rows.values() for r in rows if r.get("ticker")})
    with ThreadPoolExecutor(max_workers=8) as ex:
        names = dict(zip(tickers, ex.map(current_name, tickers)))

    for k, rows in all_rows.items():
        for r in rows:
            r["display_name"] = names.get(r.get("ticker")) or r["name"]
        v = result[k]
        out[k] = {"start": v["start"].isoformat(), "end": v["end"].isoformat(), "rows": rows}
        mapped = sum(1 for r in rows if r.get("ticker"))
        print(f"{k}: {v['start']} ~ {v['end']} {len(rows)}행, 티커 연결 {mapped}/{len(rows)}")
        for r in rows[:10]:
            print(f"  {r['rank']:>2} {str(r.get('ticker')):<6} {r['display_name']}")

    data.SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data.SNAPSHOT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"저장: {data.SNAPSHOT_FILE}")


if __name__ == "__main__":
    main()
