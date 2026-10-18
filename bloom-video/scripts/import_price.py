"""인베스팅닷컴 등에서 받은 CSV("날짜","종가",...)를 data/price.csv(date,close)로 변환.
사용: python3 scripts/import_price.py <받은파일.csv>"""
import csv
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "price.csv"

rows = []
with open(sys.argv[1], encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        date = "-".join(p.strip().zfill(2) for p in r["날짜"].split("-"))
        rows.append((date, float(r["종가"].replace(",", ""))))
rows.sort()
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "close"])
    w.writerows(rows)
print(f"saved {len(rows)} rows -> {OUT} ({rows[0][0]} ~ {rows[-1][0]})")
