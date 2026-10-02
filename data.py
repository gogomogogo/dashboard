"""데이터 수집 모듈: S&P 500 히트맵용 데이터와 거시 지표 시계열."""
import io
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}


# ---------------------------------------------------------------- S&P 500
@st.cache_data(ttl=86400, show_spinner=False)
def get_sp500_constituents() -> pd.DataFrame:
    """위키피디아의 S&P 500 구성종목 표 (티커, 회사명, 섹터)."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    html = requests.get(url, headers=UA, timeout=20).text
    df = pd.read_html(io.StringIO(html), attrs={"id": "constituents"})[0]
    df = df.rename(
        columns={
            "Symbol": "ticker",
            "Security": "name",
            "GICS Sector": "sector",
            "GICS Sub-Industry": "industry",
        }
    )
    # Yahoo는 BRK.B 대신 BRK-B 형식을 씀
    df["ticker"] = df["ticker"].str.replace(".", "-", regex=False)
    return df[["ticker", "name", "sector", "industry"]]


def _market_cap(ticker: str):
    try:
        return ticker, float(yf.Ticker(ticker).fast_info.market_cap)
    except Exception:
        return ticker, None


@st.cache_data(ttl=86400, show_spinner=False)
def get_market_caps(tickers: tuple) -> pd.Series:
    """종목별 시가총액. 종목마다 따로 조회해야 해서 느리므로 하루 캐싱."""
    with ThreadPoolExecutor(max_workers=16) as ex:
        result = dict(ex.map(_market_cap, tickers))
    return pd.Series(result, dtype="float64")


@st.cache_data(ttl=900, show_spinner=False)
def get_closes(tickers: tuple) -> pd.DataFrame:
    """최근 1년 일별 종가 (열 = 티커). 15분 캐싱."""
    df = yf.download(
        list(tickers),
        period="1y",
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    close = df["Close"] if isinstance(df.columns, pd.MultiIndex) else df[["Close"]]
    close.index = _naive(close.index)
    return close.dropna(how="all")


def compute_returns(close: pd.DataFrame, period: str) -> pd.Series:
    """기간별 등락률(%)."""
    close = close.ffill()
    last = close.iloc[-1]
    if period == "1D":
        base = close.iloc[-2]
    elif period == "1W":
        base = close.iloc[-6]
    elif period == "1M":
        base = close.iloc[-22]
    else:  # YTD: 작년 마지막 거래일 종가 대비
        year = close.index[-1].year
        prev = close[close.index < pd.Timestamp(year=year, month=1, day=1)]
        base = prev.iloc[-1] if len(prev) else close.iloc[0]
    return (last / base - 1) * 100


# ---------------------------------------------------------------- 지표
def _naive(index) -> pd.DatetimeIndex:
    idx = pd.to_datetime(index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    return idx.normalize()


def _yf_series(symbol: str) -> pd.Series:
    hist = yf.Ticker(symbol).history(period="max", auto_adjust=False)
    s = hist["Close"].dropna()
    s.index = _naive(s.index)
    return s[~s.index.duplicated(keep="last")]


@st.cache_data(ttl=3600, show_spinner=False)
def get_us10y():
    """미국 10년물 국채금리(%). FRED 공식 데이터, 실패하면 Yahoo ^TNX."""
    try:
        r = requests.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10",
            headers=UA,
            timeout=20,
        )
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        s = pd.Series(
            pd.to_numeric(df.iloc[:, -1], errors="coerce").values,
            index=pd.to_datetime(df.iloc[:, 0]),
        ).dropna()
        if len(s) > 100:
            return s, "FRED DGS10"
    except Exception:
        pass
    return _yf_series("^TNX"), "Yahoo ^TNX"


@st.cache_data(ttl=3600, show_spinner=False)
def get_vix() -> pd.Series:
    return _yf_series("^VIX")


@st.cache_data(ttl=3600, show_spinner=False)
def get_usdkrw() -> pd.Series:
    return _yf_series("KRW=X")


FG_HISTORY_CSV = (
    "https://raw.githubusercontent.com/whit3rabbit/fear-greed-data/main/fear-greed.csv"
)
CNN_FG_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"


def _cnn_fear_greed():
    """CNN 엔드포인트. 너무 오래된 시작일을 넣으면 500 에러가 나므로 날짜 없이 먼저 시도."""
    headers = {
        **UA,
        "Accept": "application/json",
        "Referer": "https://edition.cnn.com/",
        "Origin": "https://edition.cnn.com",
    }
    recent = (pd.Timestamp.today() - pd.Timedelta(days=300)).strftime("%Y-%m-%d")
    for url in (CNN_FG_URL, f"{CNN_FG_URL}/{recent}"):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            js = r.json()
            points = js["fear_and_greed_historical"]["data"]
            s = pd.Series(
                {pd.to_datetime(p["x"], unit="ms").normalize(): float(p["y"]) for p in points}
            ).sort_index()
            return s, js.get("fear_and_greed", {}).get("rating", "")
        except Exception:
            continue
    return None, ""


@st.cache_data(ttl=3600, show_spinner=False)
def get_fear_greed():
    """공포와 탐욕 지수.
    과거 데이터(2011~)는 매일 갱신되는 공개 CSV에서, 최신값은 CNN에서 받아 합친다.
    둘 중 하나만 성공해도 표시된다."""
    hist, rating = None, ""
    try:
        df = pd.read_csv(io.StringIO(requests.get(FG_HISTORY_CSV, timeout=20).text))
        hist = pd.Series(df.iloc[:, 1].astype(float).values, index=pd.to_datetime(df.iloc[:, 0]))
        rating = str(df.iloc[-1, 2])
    except Exception:
        pass

    live, live_rating = _cnn_fear_greed()
    if hist is None and live is None:
        raise RuntimeError("CNN과 과거 데이터 CSV 모두에서 데이터를 받지 못했습니다.")
    if live is not None:
        rating = live_rating or rating
        hist = live if hist is None else live.combine_first(hist)
    s = hist.sort_index()
    return s[~s.index.duplicated(keep="last")], rating


# ---------------------------------------------------------------- 종목 분석
@st.cache_data(ttl=900, show_spinner=False)
def get_history(ticker: str, interval: str = "1d") -> pd.DataFrame:
    """OHLCV. 일봉은 10년, 주봉·월봉은 전체 기간."""
    period = "10y" if interval == "1d" else "max"
    df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
    if df.empty:
        return df
    df.index = _naive(df.index)
    df = df[~df.index.duplicated(keep="last")]
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])


@st.cache_data(ttl=3600, show_spinner=False)
def get_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


@st.cache_data(ttl=1800, show_spinner=False)
def get_news(ticker: str, count: int = 10) -> list:
    """yfinance 뉴스를 {title, url, source, time} 형태로 정리. 신·구 응답 형식 모두 처리."""
    try:
        raw = yf.Ticker(ticker).get_news(count=count)
    except Exception:
        return []
    items = []
    for n in raw or []:
        c = n.get("content", n)
        title = c.get("title")
        if not title:
            continue
        url = (c.get("canonicalUrl") or {}).get("url") or (c.get("clickThroughUrl") or {}).get("url") \
            or c.get("link")
        source = (c.get("provider") or {}).get("displayName") or c.get("publisher", "")
        t = c.get("pubDate") or c.get("displayTime")
        if t:
            ts = pd.to_datetime(t, utc=True)
        elif c.get("providerPublishTime"):
            ts = pd.to_datetime(c["providerPublishTime"], unit="s", utc=True)
        else:
            ts = None
        items.append({"title": title, "url": url, "source": source, "time": ts})
    return items


# ---------------------------------------------------------------- 캘린더
def _paged(fetch, max_rows: int = 2000) -> pd.DataFrame:
    """Yahoo 캘린더는 한 번에 100건까지라 offset으로 나눠 받는다."""
    frames, offset = [], 0
    while offset < max_rows:
        df = fetch(offset)
        if df is None or df.empty:
            break
        frames.append(df.reset_index())
        if len(df) < 100:
            break
        offset += 100
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _to_utc(series: pd.Series) -> pd.Series:
    s = pd.to_datetime(series, errors="coerce")
    if s.dt.tz is None:
        s = s.dt.tz_localize("UTC")
    return s.dt.tz_convert("UTC")


@st.cache_data(ttl=3600, show_spinner=False)
def get_economic_calendar(start: str, end: str) -> pd.DataFrame:
    """주요국 경제지표 발표 일정. 열: event, region, time(UTC), period, actual, expected, last"""
    cal = yf.Calendars(start=start, end=end)
    df = _paged(lambda off: cal.get_economic_events_calendar(
        start=start, end=end, limit=100, offset=off, force=True))
    if df.empty:
        return df
    df = df.rename(columns={
        "Event": "event", "Region": "region", "Event Time": "time", "For": "period",
        "Actual": "actual", "Expected": "expected", "Last": "last", "Revised": "revised",
    })
    df["time"] = _to_utc(df["time"])
    for col in ("period", "actual", "expected", "last"):
        if col not in df:
            df[col] = None
    return df.dropna(subset=["time"]).drop_duplicates(subset=["event", "region", "time"])


@st.cache_data(ttl=3600, show_spinner=False)
def get_earnings_calendar(start: str, end: str, min_cap: float) -> pd.DataFrame:
    """미국 실적발표 일정. 열: ticker, company, cap, time(UTC), timing, eps_est, eps_act, surprise"""
    cal = yf.Calendars(start=start, end=end)
    df = _paged(lambda off: cal.get_earnings_calendar(
        market_cap=min_cap, filter_most_active=False, start=start, end=end,
        limit=100, offset=off, force=True))
    if df.empty:
        return df
    df = df.rename(columns={
        "Symbol": "ticker", "Company": "company", "Marketcap": "cap",
        "Event Start Date": "time", "Timing": "timing", "EPS Estimate": "eps_est",
        "Reported EPS": "eps_act", "Surprise(%)": "surprise",
    })
    df["time"] = _to_utc(df["time"])
    for col in ("timing", "eps_est", "eps_act", "surprise", "cap", "company"):
        if col not in df:
            df[col] = None
    return df.dropna(subset=["time"]).drop_duplicates(subset=["ticker", "time"])
