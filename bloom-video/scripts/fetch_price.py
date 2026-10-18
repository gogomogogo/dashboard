"""BE(블룸에너지) 최근 3년 일봉 종가를 data/price.csv(date,close)로 저장."""
from pathlib import Path

import yfinance as yf

OUT = Path(__file__).resolve().parent.parent / "data" / "price.csv"

df = yf.download("BE", period="3y", interval="1d", auto_adjust=True, progress=False)
if df.empty:
    raise SystemExit("주가 데이터를 받지 못했습니다 (네트워크 확인).")
close = df["Close"]
if hasattr(close, "columns"):
    close = close.iloc[:, 0]
OUT.parent.mkdir(parents=True, exist_ok=True)
out = close.dropna().round(4).rename("close").to_frame()
out.index = out.index.strftime("%Y-%m-%d")
out.index.name = "date"
out.to_csv(OUT)
print(f"saved {len(out)} rows -> {OUT} ({out.index[0]} ~ {out.index[-1]})")
