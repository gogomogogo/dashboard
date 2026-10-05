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


NASDAQ_HEADERS = {
    **UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}


def _nasdaq(path: str, params: dict | None = None) -> dict:
    r = requests.get(f"https://api.nasdaq.com/api/{path}", params=params,
                     headers=NASDAQ_HEADERS, timeout=12)
    r.raise_for_status()
    js = r.json()
    return js.get("data") or {}


def _num(v):
    """'$1,234.5', '(0.12)', '0.44%', '3.2T' 같은 문자열을 숫자로. 실패하면 None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return None if pd.isna(v) else float(v)
    s = str(v).replace("&nbsp;", "").replace("$", "").replace(",", "").replace("%", "").strip()
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    mult = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}.get(s[-1:].upper(), 1) if s else 1
    if mult != 1:
        s = s[:-1]
    try:
        x = float(s) * mult
    except ValueError:
        return None
    return -x if neg else x


def _clean(v):
    """경제지표 값처럼 단위가 붙은 문자열은 그대로 두고 빈 값만 None으로."""
    if v is None:
        return None
    s = str(v).replace("&nbsp;", "").strip()
    return s if s and s.upper() not in ("N/A", "NA", "-", "--") else None


def _nasdaq_info(ticker: str) -> dict:
    """Nasdaq 종목 요약 → yfinance info와 같은 키 이름으로 변환."""
    for assetclass in ("stocks", "etf"):
        try:
            d = _nasdaq(f"quote/{ticker}/summary", {"assetclass": assetclass})
        except Exception:
            continue
        sd = d.get("summaryData") or {}
        if not sd:
            continue
        val = lambda k: (sd.get(k) or {}).get("value")
        out = {
            "marketCap": _num(val("MarketCap")),
            "trailingPE": _num(val("PERatio")),
            "forwardPE": _num(val("ForwardPE1Yr")),
            "trailingEps": _num(val("EarningsPerShare")),
            "dividendRate": _num(val("AnnualizedDividend")),
            "beta": _num(val("Beta")),
            "sector": _clean(val("Sector")),
            "industry": _clean(val("Industry")),
            "targetMeanPrice": _num(val("OneYrTarget")),
        }
        hl = _clean(val("FiftTwoWeekHighLow")) or _clean(val("FiftyTwoWeekHighLow"))
        if hl and "/" in hl:
            hi, lo = hl.split("/", 1)
            out["fiftyTwoWeekHigh"], out["fiftyTwoWeekLow"] = _num(hi), _num(lo)
        y = _num(val("Yield"))
        if y is not None:
            out["_dividendYieldPct"] = y
        return {k: v for k, v in out.items() if v is not None}
    return {}


@st.cache_data(ttl=3600, show_spinner=False)
def get_info(ticker: str) -> dict:
    """기본 지표. Yahoo를 먼저 시도하고, 비어 있는 값은 Nasdaq과 fast_info로 채운다.
    (Streamlit Cloud 같은 서버에서는 Yahoo가 'Invalid Crumb'으로 막히는 경우가 많다.)"""
    info, sources = {}, []
    try:
        info = dict(yf.Ticker(ticker).info or {})
        if info.get("marketCap") or info.get("trailingPE"):
            sources.append("Yahoo Finance")
    except Exception:
        info = {}

    needed = ["marketCap", "trailingPE", "forwardPE", "trailingEps", "dividendRate",
              "beta", "sector", "industry", "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "targetMeanPrice"]
    if any(info.get(k) in (None, "") for k in needed):
        nd = _nasdaq_info(ticker)
        if nd:
            sources.append("Nasdaq")
            for k, v in nd.items():
                if info.get(k) in (None, ""):
                    info[k] = v

    if info.get("marketCap") is None or info.get("fiftyTwoWeekHigh") is None:
        try:
            fi = yf.Ticker(ticker).fast_info
            for k, attr in (("marketCap", "market_cap"), ("fiftyTwoWeekHigh", "year_high"),
                            ("fiftyTwoWeekLow", "year_low"), ("currentPrice", "last_price")):
                if info.get(k) is None:
                    info[k] = getattr(fi, attr, None)
            sources.append("Yahoo 시세")
        except Exception:
            pass
    info["_sources"] = sources
    return info


def _rss(url: str, source_default: str = "") -> list:
    import xml.etree.ElementTree as ET
    r = requests.get(url, headers=UA, timeout=12)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        if not title:
            continue
        src = (it.findtext("source") or source_default).strip()
        # Google 뉴스 제목은 '헤드라인 - 매체' 형식
        if src and title.endswith(f" - {src}"):
            title = title[: -len(src) - 3]
        pub = it.findtext("pubDate")
        items.append({
            "title": title,
            "url": (it.findtext("link") or "").strip(),
            "source": src,
            "time": pd.to_datetime(pub, utc=True, errors="coerce") if pub else None,
        })
    return items


def _yf_news(ticker: str, count: int) -> list:
    raw = yf.Ticker(ticker).get_news(count=count)
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


@st.cache_data(ttl=1800, show_spinner=False)
def get_news(ticker: str, count: int = 10) -> list:
    """최근 뉴스. yfinance → Yahoo RSS → Google 뉴스 RSS 순서로 시도."""
    attempts = [
        lambda: _yf_news(ticker, count),
        lambda: _rss(f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
                     "Yahoo Finance"),
        lambda: _rss(f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"),
    ]
    for fetch in attempts:
        try:
            items = fetch()
        except Exception:
            continue
        if items:
            items.sort(key=lambda n: n["time"] or pd.Timestamp(0, tz="UTC"), reverse=True)
            return items[:count]
    return []


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


NASDAQ_COUNTRY = {
    "United States": "US", "Euro Zone": "EU", "Eurozone": "EU", "European Union": "EU",
    "Japan": "JP", "China": "CN", "United Kingdom": "GB", "Germany": "DE", "France": "FR",
    "Italy": "IT", "Spain": "ES", "South Korea": "KR", "Korea": "KR", "Canada": "CA",
    "Australia": "AU", "New Zealand": "NZ", "Switzerland": "CH", "India": "IN", "Brazil": "BR",
    "Mexico": "MX", "Singapore": "SG", "Hong Kong": "HK", "Taiwan": "TW", "Sweden": "SE",
    "Norway": "NO", "South Africa": "ZA", "Turkey": "TR", "Russia": "RU", "Indonesia": "ID",
}


def _days(start: str, end: str) -> list:
    return [d.date() for d in pd.date_range(start, end, freq="D")]


def _per_day(fetch_day, start: str, end: str) -> pd.DataFrame:
    """Nasdaq 캘린더는 하루 단위라 기간의 날짜별로 병렬 조회."""
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(fetch_day, _days(start, end)))
    errors = [r for r in results if isinstance(r, Exception)]
    frames = [r for r in results if isinstance(r, pd.DataFrame) and not r.empty]
    if not frames and errors and len(errors) == len(results):
        raise errors[0]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _nasdaq_econ_day(d) -> pd.DataFrame:
    try:
        rows = (_nasdaq("calendar/economicevents", {"date": d.isoformat()}).get("rows")) or []
    except Exception as e:
        return e
    out = []
    for r in rows:
        country = _clean(r.get("country")) or ""
        gmt = _clean(r.get("gmt")) or _clean(r.get("time")) or ""
        hhmm = gmt.replace("GMT", "").strip()
        tbd = not (len(hhmm) == 5 and hhmm[2] == ":")
        if tbd:
            # 시간 미정이면 한국 날짜 기준 0시로 두어 날짜가 밀리지 않게 한다
            t = pd.Timestamp(d).tz_localize("Asia/Seoul").tz_convert("UTC")
        else:
            t = pd.Timestamp(f"{d} {hhmm}").tz_localize("UTC")
        out.append({
            "event": _clean(r.get("eventName")) or "",
            "region": NASDAQ_COUNTRY.get(country, country),
            "time": t, "tbd": tbd, "period": None,
            "actual": _clean(r.get("actual")),
            "expected": _clean(r.get("consensus")),
            "last": _clean(r.get("previous")),
        })
    return pd.DataFrame(out)


def _yahoo_econ(start: str, end: str) -> pd.DataFrame:
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
    df["tbd"] = False
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_economic_calendar(start: str, end: str) -> pd.DataFrame:
    """주요국 경제지표 발표 일정. Yahoo → Nasdaq 순서로 시도.
    열: event, region, time(UTC), tbd, period, actual, expected, last, source"""
    errors = []
    for name, fetch in (("Yahoo Finance", _yahoo_econ),
                        ("Nasdaq", lambda s_, e_: _per_day(_nasdaq_econ_day, s_, e_))):
        try:
            df = fetch(start, end)
        except Exception as e:
            errors.append(f"{name}: {e}")
            continue
        if df.empty:
            continue
        for col in ("period", "actual", "expected", "last", "tbd"):
            if col not in df:
                df[col] = None
        df["source"] = name
        return df.dropna(subset=["time"]).drop_duplicates(subset=["event", "region", "time"])
    if errors:
        raise RuntimeError(" / ".join(errors))
    return pd.DataFrame()


NASDAQ_TIMING = {"time-pre-market": "BMO", "time-after-hours": "AMC"}


def _nasdaq_earn_day(d) -> pd.DataFrame:
    try:
        rows = (_nasdaq("calendar/earnings", {"date": d.isoformat()}).get("rows")) or []
    except Exception as e:
        return e
    noon_ny = pd.Timestamp(f"{d} 12:00").tz_localize("America/New_York").tz_convert("UTC")
    out = []
    for r in rows:
        out.append({
            "ticker": _clean(r.get("symbol")),
            "company": _clean(r.get("name")),
            "cap": _num(r.get("marketCap")),
            "time": noon_ny,
            "timing": NASDAQ_TIMING.get(str(r.get("time")), "TNS"),
            "eps_est": _num(r.get("epsForecast")),
            "eps_act": _num(r.get("eps")),
            "surprise": _num(r.get("surprise")),
        })
    return pd.DataFrame(out)


def _yahoo_earn(start: str, end: str, min_cap: float) -> pd.DataFrame:
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
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_earnings_calendar(start: str, end: str, min_cap: float) -> pd.DataFrame:
    """미국 실적발표 일정. Yahoo → Nasdaq 순서로 시도.
    열: ticker, company, cap, time(UTC), timing, eps_est, eps_act, surprise, source"""
    errors = []
    for name, fetch in (("Yahoo Finance", lambda s_, e_: _yahoo_earn(s_, e_, min_cap)),
                        ("Nasdaq", lambda s_, e_: _per_day(_nasdaq_earn_day, s_, e_))):
        try:
            df = fetch(start, end)
        except Exception as e:
            errors.append(f"{name}: {e}")
            continue
        if df.empty:
            continue
        for col in ("timing", "eps_est", "eps_act", "surprise", "cap", "company"):
            if col not in df:
                df[col] = None
        df = df.dropna(subset=["time", "ticker"])
        df = df[pd.to_numeric(df["cap"], errors="coerce").fillna(0) >= min_cap]
        df["source"] = name
        return df.drop_duplicates(subset=["ticker", "time"])
    if errors:
        raise RuntimeError(" / ".join(errors))
    return pd.DataFrame()


# ---------------------------------------------------------------- 섹터 ETF
SECTOR_ETFS = {
    "XLE": "에너지", "XLB": "소재", "XLI": "산업재", "XLY": "경기소비재", "XLP": "필수소비재",
    "XLV": "헬스케어", "XLF": "금융", "XLK": "정보기술", "XLC": "커뮤니케이션 서비스",
    "XLU": "유틸리티", "XLRE": "부동산",
}


@st.cache_data(ttl=900, show_spinner=False)
def get_sector_closes() -> pd.DataFrame:
    """11개 섹터 ETF의 최근 6개월 일별 종가 (열 = 티커)."""
    df = yf.download(list(SECTOR_ETFS), period="6mo", interval="1d",
                     auto_adjust=True, progress=False, threads=True)
    close = df["Close"] if isinstance(df.columns, pd.MultiIndex) else df[["Close"]]
    close.index = _naive(close.index)
    return close.dropna(how="all").ffill()


def sector_returns(close: pd.DataFrame, months: float = 1) -> pd.DataFrame:
    """기준일(오늘로부터 months개월 전 마지막 거래일) 종가를 0%로 한 누적 등락률(%)."""
    end = close.index[-1]
    start = end - (pd.DateOffset(weeks=1) if months < 1 else pd.DateOffset(months=int(months)))
    base_idx = close.index[close.index <= start]
    base_day = base_idx[-1] if len(base_idx) else close.index[0]
    window = close.loc[base_day:]
    return (window / window.iloc[0] - 1) * 100
