"""종목 분석: 티커 검색 → 캔들 차트 + 지표, 기본 정보, 뉴스."""
import pandas as pd
import streamlit as st

import charts
import data
from common import embed_html

INDICATORS = ["거래량", "이동평균선", "볼린저밴드", "RSI", "MACD"]
INTERVALS = {"일봉": "1d", "주봉": "1wk", "월봉": "1mo"}


# ---------------------------------------------------------------- 검색창
@st.cache_data(ttl=86400, show_spinner=False)
def search_options() -> list:
    try:
        cons = data.get_sp500_constituents().sort_values("ticker")
        return [f"{t}  {n}" for t, n in zip(cons["ticker"], cons["name"])]
    except Exception:
        return ["AAPL  Apple Inc.", "MSFT  Microsoft", "NVDA  Nvidia"]


options = search_options()

# 히트맵·실적 캘린더에서 넘어온 티커 (?ticker=XXX)
qp = st.query_params.get("ticker")
if qp and st.session_state.get("_from_qp") != qp:
    st.session_state["_from_qp"] = qp
    qp = qp.upper()
    match = next((o for o in options if o.split()[0] == qp), qp)
    if match not in options:
        options = [match] + options
    st.session_state["ticker_search"] = match
elif "ticker_search" not in st.session_state:
    st.session_state["ticker_search"] = next((o for o in options if o.startswith("AAPL ")), options[0])
elif st.session_state["ticker_search"] not in options:
    options = [st.session_state["ticker_search"]] + options

st.title("종목 분석")
top = st.columns([3, 1.3, 4], vertical_alignment="bottom")
choice = top[0].selectbox(
    "티커 검색",
    options,
    key="ticker_search",
    accept_new_options=True,
    placeholder="티커나 회사명을 입력하세요",
    help="S&P 500 종목은 회사명으로도 찾을 수 있고, 목록에 없는 티커(예: QQQ, TSM)는 직접 입력하면 됩니다.",
)
ticker = (choice or "AAPL").split()[0].upper().strip()
interval_label = top[1].segmented_control("봉", list(INTERVALS), default="일봉", key="interval") or "일봉"
interval = INTERVALS[interval_label]
show = set(top[2].pills(
    "지표", INDICATORS, selection_mode="multi", default=["거래량", "이동평균선"], key="ind",
) or [])

with st.sidebar:
    st.header("지표 설정")
    ma_periods = st.multiselect("이동평균 기간", [5, 10, 20, 50, 60, 100, 120, 200],
                                default=[20, 60, 120])
    bb_period = st.number_input("볼린저밴드 기간", 5, 100, 20)
    bb_k = st.number_input("볼린저밴드 표준편차 배수", 1.0, 4.0, 2.0, step=0.5)
    rsi_period = st.number_input("RSI 기간", 2, 50, 14)
    c = st.columns(3)
    m_fast = c[0].number_input("MACD 단기", 2, 50, 12)
    m_slow = c[1].number_input("장기", 5, 100, 26)
    m_sig = c[2].number_input("시그널", 2, 50, 9)
    st.caption("마우스 휠로 기간 줌, 드래그로 이동, 더블클릭으로 초기화.")

# ---------------------------------------------------------------- 차트
with st.spinner(f"{ticker} 데이터를 불러오는 중"):
    hist = data.get_history(ticker, interval)
    info = data.get_info(ticker)

if hist.empty:
    st.error(f"'{ticker}' 시세를 찾을 수 없습니다. 티커 철자를 확인해 주세요. (예: 버크셔해서웨이 B주는 BRK-B)")
    st.stop()

name = info.get("longName") or info.get("shortName") or ticker
last, prev = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
h1, h2 = st.columns([3, 2], vertical_alignment="bottom")
h1.subheader(f"{name} ({ticker})")
h2.metric(
    f"현재가 · {hist.index[-1]:%Y-%m-%d}",
    f"${last:,.2f}",
    f"{last - prev:+,.2f} ({(last / prev - 1) * 100:+.2f}%)",
)

html, height = charts.candle_chart_html(
    hist, ticker, show,
    ma_periods=sorted(ma_periods) or [20],
    bb=(bb_period, bb_k),
    rsi_period=rsi_period,
    macd_params=(m_fast, m_slow, m_sig),
    interval=interval,
)
embed_html(html, height=height + 5)


# ---------------------------------------------------------------- 기본 지표
def money(v):
    if v is None or pd.isna(v):
        return "-"
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6)):
        if abs(v) >= div:
            return f"${v / div:,.2f}{unit}"
    return f"${v:,.0f}"


def num(v, fmt="{:,.2f}"):
    return "-" if v is None or (isinstance(v, float) and pd.isna(v)) else fmt.format(v)


price = info.get("currentPrice") or info.get("regularMarketPrice") or last
div_rate = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
div_yield = (div_rate / price * 100) if div_rate and price else info.get("_dividendYieldPct")

st.subheader("기본 지표")
if not any(info.get(k) for k in ("marketCap", "trailingPE", "sector")):
    st.info("이 종목은 기본 지표를 제공하지 않습니다. ETF나 지수는 일부 값이 비어 있을 수 있습니다.")
row1 = st.columns(6)
row1[0].metric("시가총액", money(info.get("marketCap")))
row1[1].metric("PER (TTM)", num(info.get("trailingPE")))
row1[2].metric("선행 PER", num(info.get("forwardPE")))
row1[3].metric("EPS (TTM)", num(info.get("trailingEps"), "${:,.2f}"))
row1[4].metric("배당수익률", num(div_yield, "{:.2f}%") if div_yield else "-")
row1[5].metric("베타", num(info.get("beta")))
row2 = st.columns(6)
row2[0].metric("섹터", info.get("sector") or info.get("quoteType", "-"))
row2[1].metric("산업", info.get("industry") or "-")
row2[2].metric("52주 최고", num(info.get("fiftyTwoWeekHigh"), "${:,.2f}"))
row2[3].metric("52주 최저", num(info.get("fiftyTwoWeekLow"), "${:,.2f}"))
row2[4].metric("PBR", num(info.get("priceToBook")))
row2[5].metric("목표주가 (평균)", num(info.get("targetMeanPrice"), "${:,.2f}"))
if info.get("_sources"):
    st.caption("출처 " + ", ".join(info["_sources"]))

# ---------------------------------------------------------------- 뉴스
st.subheader("최근 뉴스")
news = data.get_news(ticker)
if not news:
    st.caption("표시할 뉴스가 없습니다.")
for n in news:
    when = n["time"].tz_convert("Asia/Seoul").strftime("%m/%d %H:%M") if n["time"] is not None else ""
    clean = n["title"].replace("$", "\\$").replace("[", "(").replace("]", ")")
    title = f"[{clean}]({n['url']})" if n["url"] else clean
    meta = " | ".join(x for x in (n["source"], when) if x)
    st.markdown(f"**{title}**  \n:gray[{meta}]")
