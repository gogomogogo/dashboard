"""주요 매체 헤드라인: 수집 → 이슈 묶기 → 중요도 정렬 → 번역."""
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

import pandas as pd
import requests
import streamlit as st

from data import UA

# ---------------------------------------------------------------- 매체
_GN = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
_GN_TOPICS = "(markets OR stocks OR economy OR Fed OR earnings OR tariffs OR oil OR bonds)"

# 대표 헤드라인을 고를 때의 우선순위 순서이기도 하다
OUTLETS = {
    "Reuters": [_GN.format(q=quote_plus(f"site:reuters.com {_GN_TOPICS} when:2d"))],
    "Bloomberg": [_GN.format(q=quote_plus(f"site:bloomberg.com {_GN_TOPICS} when:2d"))],
    "WSJ": [
        "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
    ],
    "FT": ["https://www.ft.com/markets?format=rss", "https://www.ft.com/global-economy?format=rss"],
    "CNBC": [
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # Top News
        "https://www.cnbc.com/id/20910258/device/rss/rss.html",   # Economy
        "https://www.cnbc.com/id/10000664/device/rss/rss.html",   # Finance
        "https://www.cnbc.com/id/15839069/device/rss/rss.html",   # Investing
    ],
    "MarketWatch": [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
    ],
    "Yahoo Finance": ["https://finance.yahoo.com/news/rssindex"],
}
PRIORITY = {name: i for i, name in enumerate(OUTLETS)}
FEED_TIMEOUT = 5  # 이보다 느린 피드는 이번 회차에서 건너뛴다

# 특정 사건이 아닌 정기 요약·생활 정보성 기사 (점수 감점)
ROUNDUP = re.compile(
    r"things to know|what to watch|stock market today|live updates?|live:|morning brief|evening brief|"
    r"week ahead|here's what|heres what|before the bell|after the bell|newsletter|podcast|"
    r"how to |best .* to buy|should you buy|is it time to",
    re.I,
)


def _fetch_feed(outlet: str, url: str) -> list:
    try:
        r = requests.get(url, headers=UA, timeout=FEED_TIMEOUT)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception:
        return []
    out = []
    for it in root.iter("item"):
        title = re.sub(r"\s+", " ", (it.findtext("title") or "")).strip()
        if not title:
            continue
        src = (it.findtext("source") or "").strip()
        if "news.google.com" in url:
            # Google 뉴스는 다른 매체가 섞일 수 있으므로 출처를 확인하고 제목 끝의 ' - 매체'를 뗀다
            if outlet.lower() not in src.lower():
                continue
            title = re.sub(rf"\s+-\s+{re.escape(src)}$", "", title)
        pub = it.findtext("pubDate")
        out.append({
            "outlet": outlet,
            "title": title,
            "url": (it.findtext("link") or "").strip(),
            "time": pd.to_datetime(pub, utc=True, errors="coerce") if pub else pd.NaT,
        })
    return out


@st.cache_data(ttl=900, show_spinner=False)
def fetch_headlines(hours: int = 24) -> pd.DataFrame:
    jobs = [(o, u) for o, urls in OUTLETS.items() for u in urls]
    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        results = ex.map(lambda j: _fetch_feed(*j), jobs)
    df = pd.DataFrame([a for r in results for a in r])
    if df.empty:
        return df
    df = df.dropna(subset=["time"])
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=hours)
    df = df[df["time"] >= cutoff]
    df["key"] = df["title"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True)
    return df.sort_values("time").drop_duplicates(subset=["outlet", "key"]).reset_index(drop=True)


# ---------------------------------------------------------------- 단어 정리
STOP = set("""
a an the and or but of to in on at for from by with as is are was were be been being it its this that these those
into over after before about amid against than then up down out off new says said say report reports reported
update updates live latest how why what who when where will would could can may might should not no yes more most
you your we our they their his her he she them us i my just now week weeks day days today year years month months
here there first last next back still also amid via vs per inc corp co ltd plc s ago top big set sets get gets
""".split())
# 어디에나 나오는 시장 일반어: 묶기에는 약하게, 관련성 판단에는 사용
GENERIC = set("stock stocks market markets share shares investor investors trader traders wall street dow price prices".split())

SYNONYMS = {
    "u.s": "us", "u.s.": "us", "america": "us",
    "federal": "fed", "reserve": "fed", "powell": "fed", "fomc": "fed",
    "rates": "rate", "interest": "rate",
    "cuts": "cut", "cutting": "cut", "lowers": "cut", "lower": "cut",
    "hikes": "hike", "raises": "hike", "raise": "hike", "hiking": "hike",
    "holds": "hold", "keeps": "hold", "unchanged": "hold", "steady": "hold", "pause": "hold", "pauses": "hold",
    "inflation": "cpi", "consumer": "cpi",
    "jobs": "payroll", "payrolls": "payroll", "nonfarm": "payroll", "employment": "payroll", "unemployment": "payroll", "hiring": "payroll",
    "tariff": "tariff", "tariffs": "tariff", "trade": "tariff",
    "treasury": "yield", "treasuries": "yield", "yields": "yield", "bond": "yield", "bonds": "yield",
    "crude": "oil", "brent": "oil", "opec": "oil",
    "earnings": "earnings", "results": "earnings", "quarterly": "earnings", "profit": "earnings", "revenue": "earnings", "guidance": "earnings",
    "surge": "up", "surges": "up", "jump": "up", "jumps": "up", "soar": "up", "soars": "up", "rally": "up",
    "rallies": "up", "gain": "up", "gains": "up", "rise": "up", "rises": "up", "climb": "up", "climbs": "up",
    "fall": "down", "falls": "down", "drop": "down", "drops": "down", "slide": "down", "slides": "down",
    "tumble": "down", "tumbles": "down", "sink": "down", "sinks": "down", "plunge": "down", "plunges": "down",
    "slump": "down", "slumps": "down", "decline": "down", "declines": "down",
    "s&p": "sp500", "sp": "sp500", "nasdaq": "nasdaq", "bitcoin": "bitcoin", "crypto": "bitcoin",
    "china": "china", "chinese": "china", "beijing": "china", "japan": "japan", "yen": "japan", "boj": "japan",
    "ecb": "europe", "euro": "europe", "eurozone": "europe",
}
DIRECTION = {"up", "down"}
# 시장 영향이 큰 거시 키워드와 가산점
MACRO = {"fed": 1.5, "rate": 1.0, "cpi": 1.5, "payroll": 1.5, "gdp": 1.2, "tariff": 1.2, "yield": 1.0,
         "recession": 1.2, "oil": 0.8, "earnings": 0.6, "sp500": 0.6, "nasdaq": 0.5, "dollar": 0.6,
         "china": 0.5, "europe": 0.4, "japan": 0.4, "bitcoin": 0.3, "shutdown": 1.0, "debt": 0.6}

# 회사명 별칭 (S&P 500 목록으로 자동 생성한 것 외에 자주 쓰이는 이름)
EXTRA_ALIASES = {
    "google": "GOOGL", "alphabet": "GOOGL", "facebook": "META", "meta": "META", "amazon": "AMZN",
    "apple": "AAPL", "microsoft": "MSFT", "nvidia": "NVDA", "tesla": "TSLA", "netflix": "NFLX",
    "jpmorgan": "JPM", "berkshire": "BRK-B", "broadcom": "AVGO", "goldman": "GS", "boeing": "BA",
    "intel": "INTC", "amd": "AMD", "oracle": "ORCL", "walmart": "WMT", "costco": "COST",
    "exxon": "XOM", "chevron": "CVX", "disney": "DIS", "nike": "NKE", "starbucks": "SBUX",
    "pfizer": "PFE", "lilly": "LLY", "moderna": "MRNA", "palantir": "PLTR", "uber": "UBER",
    "salesforce": "CRM", "adobe": "ADBE", "qualcomm": "QCOM", "micron": "MU", "citigroup": "C",
    "citi": "C", "visa": "V", "mastercard": "MA", "paypal": "PYPL", "coinbase": "COIN",
}
COMMON_WORDS = set("""
american first general united international global national public digital energy health systems capital
financial service services group southern northern western eastern pacific realty technologies data
""".split())
NAME_SUFFIX = re.compile(r"\b(inc|incorporated|corp|corporation|co|company|ltd|plc|holdings?|group|the|class [ab]|n\.?v\.?|s\.?a\.?)\b\.?", re.I)


@st.cache_data(ttl=86400, show_spinner=False)
def build_aliases(cons: pd.DataFrame) -> dict:
    """S&P 500 회사명에서 '고유한 첫 단어'를 별칭으로 만든다 (예: Nvidia Corporation → nvidia)."""
    firsts = Counter()
    cleaned = {}
    for t, n in zip(cons["ticker"], cons["name"]):
        words = re.sub(r"[^a-z0-9 ]", " ", NAME_SUFFIX.sub(" ", str(n)).lower()).split()
        if words:
            cleaned[t] = words
            firsts[words[0]] += 1
    aliases = {}
    for t, words in cleaned.items():
        w = words[0]
        if firsts[w] == 1 and len(w) >= 4 and w not in COMMON_WORDS and w not in STOP and w not in GENERIC:
            aliases[w] = t
    aliases.update(EXTRA_ALIASES)
    return aliases


def tokenize(title: str, aliases: dict, tickers: set):
    """제목 → (단어 가중치 dict, 언급 종목 set)"""
    raw = re.findall(r"\$?[A-Za-z][A-Za-z0-9&.\-']*", title)
    weights, found = {}, set()
    for w in raw:
        sym = w.lstrip("$").rstrip(".").upper()
        # 대문자로 쓰인 3글자 이상 티커 (예: NVDA, $AAPL)
        if (w.startswith("$") or w.isupper()) and len(sym) >= 3 and sym in tickers:
            found.add(sym)
            weights[f"T:{sym}"] = 2.5
            continue
        lw = w.lower().strip("'.").replace("'s", "")
        if lw in aliases:
            found.add(aliases[lw])
            weights[f"T:{aliases[lw]}"] = 2.5
            continue
        lw = SYNONYMS.get(lw, lw)
        if lw in STOP or len(lw) < 2:
            continue
        if lw.endswith("s") and len(lw) > 4 and lw[:-1] not in STOP:
            lw = SYNONYMS.get(lw[:-1], lw[:-1])
        if lw in GENERIC:
            weights[lw] = max(weights.get(lw, 0), 0.3)
        elif lw in DIRECTION:
            weights[lw] = max(weights.get(lw, 0), 0.5)
        elif lw in MACRO:
            weights[lw] = max(weights.get(lw, 0), 1.8)
        else:
            weights[lw] = max(weights.get(lw, 0), 1.0)
    return weights, found


def _similar(a: dict, b: dict) -> bool:
    shared = set(a) & set(b)
    sw = sum(min(a[k], b[k]) for k in shared)
    if sw < 2.4:
        return False
    # 공통 단어가 일반어·방향어뿐이면 같은 이슈로 보지 않는다
    if all(k in GENERIC or k in DIRECTION for k in shared):
        return False
    overlap = sw / max(1e-9, min(sum(a.values()), sum(b.values())))
    return overlap >= 0.34


# ---------------------------------------------------------------- 묶기 + 점수
def cluster_and_rank(df: pd.DataFrame, cons: pd.DataFrame, caps: pd.Series, top_n: int = 8) -> list:
    if df.empty:
        return []
    aliases = build_aliases(cons)
    tickers = set(cons["ticker"])
    toks = [tokenize(t, aliases, tickers) for t in df["title"]]

    clusters = []  # {"idx": [...], "toks": [...]}
    for i in df.sort_values("time").index:
        w, _ = toks[i]
        if not w:
            continue
        best = None
        for c in clusters:
            if abs((df.at[i, "time"] - df.at[c["idx"][-1], "time"]).total_seconds()) > 20 * 3600:
                continue
            hits = sum(_similar(w, toks[j][0]) for j in c["idx"])
            if hits and (best is None or hits / len(c["idx"]) > best[0]):
                best = (hits / len(c["idx"]), c)
        if best and best[0] >= 0.34:
            best[1]["idx"].append(i)
        else:
            clusters.append({"idx": [i]})

    now = pd.Timestamp.now(tz="UTC")
    ranked = []
    for c in clusters:
        g = df.loc[c["idx"]]
        outlets = sorted(g["outlet"].unique(), key=PRIORITY.get)
        terms = Counter()
        stocks = Counter()
        for j in c["idx"]:
            w, found = toks[j]
            terms.update(k for k in w if not k.startswith("T:"))
            stocks.update(found)

        macro = sum(MACRO[k] for k in terms if k in MACRO)
        macro = min(macro, 3.0)
        cap_bonus = 0.0
        for t in stocks:
            cap = caps.get(t)
            if cap and cap > 0:
                cap_bonus = max(cap_bonus, min(2.0, max(0.0, math.log10(cap / 2e10))))
        market_related = macro > 0 or stocks or any(k in GENERIC for k in terms)
        first = g["time"].min()
        age_h = (now - first).total_seconds() / 3600
        score = 3.0 * len(outlets) + 0.5 * (len(g) - len(outlets)) + macro + cap_bonus
        score *= 0.5 ** (age_h / 12)          # 12시간마다 절반
        if not market_related:
            score *= 0.4                     # 시장과 무관해 보이는 기사는 크게 감점
        if g["title"].str.contains(ROUNDUP).all():
            score *= 0.35                    # 정기 요약·생활 정보 기사

        rep = g.assign(p=g["outlet"].map(PRIORITY)).sort_values(["p", "time"]).iloc[0]
        ranked.append({
            "score": score,
            "title": rep["title"],
            "url": rep["url"],
            "outlet": rep["outlet"],
            "outlets": outlets,
            "first": first,
            "latest": g["time"].max(),
            "stocks": [t for t, _ in stocks.most_common(4)],
            "articles": g.sort_values("time", ascending=False)[["outlet", "title", "url", "time"]]
                        .to_dict("records"),
        })
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_n]


# ---------------------------------------------------------------- 번역
def _anthropic_key():
    try:
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        return None


def _translate_claude(texts: list, key: str) -> list:
    import json
    prompt = (
        "다음 영어 금융 뉴스 헤드라인들을 자연스러운 한국어 경제 기사 제목으로 번역하세요. "
        "회사명·지수명은 한국 언론 표기를 따르고(예: Fed→연준, S&P 500→S&P500), 티커는 그대로 두세요. "
        "입력과 같은 순서·같은 개수의 JSON 문자열 배열만 출력하세요.\n\n"
        + json.dumps(texts, ensure_ascii=False)
    )
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 4000,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    r.raise_for_status()
    text = "".join(b.get("text", "") for b in r.json().get("content", []))
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    out = json.loads(text)
    if not isinstance(out, list) or len(out) != len(texts):
        raise ValueError("번역 개수가 맞지 않습니다")
    return [str(x) for x in out]


def _translate_google_chunk(lines: list) -> list:
    r = requests.get(
        "https://translate.googleapis.com/translate_a/single",
        params={"client": "gtx", "sl": "en", "tl": "ko", "dt": "t", "q": "\n".join(lines)},
        headers=UA, timeout=15,
    )
    r.raise_for_status()
    joined = "".join(seg[0] for seg in r.json()[0] if seg and seg[0])
    out = [s.strip() for s in joined.split("\n")]
    if len(out) != len(lines):
        raise ValueError("번역 줄 수가 맞지 않습니다")
    return out


def _chunks(texts: list, limit: int = 1500) -> list:
    out, chunk, size = [], [], 0
    for t in texts:
        if chunk and size + len(t) > limit:
            out.append(chunk)
            chunk, size = [], 0
        chunk.append(t)
        size += len(t) + 1
    if chunk:
        out.append(chunk)
    return out


def _google_chunk_safe(chunk: list) -> dict:
    """묶음 번역. 줄 수가 어긋나면 그 묶음만 한 줄씩 병렬로 다시 번역. 실패한 줄은 빠진다."""
    try:
        return dict(zip(chunk, _translate_google_chunk(chunk)))
    except Exception:
        if len(chunk) == 1:
            return {}
    with ThreadPoolExecutor(max_workers=min(8, len(chunk))) as ex:
        parts = ex.map(_google_chunk_safe, [[t] for t in chunk])
    return {k: v for d in parts for k, v in d.items()}


def _translate_google(texts: list) -> dict:
    chunks = _chunks(texts)
    if not chunks:
        return {}
    with ThreadPoolExecutor(max_workers=min(6, len(chunks))) as ex:
        parts = ex.map(_google_chunk_safe, chunks)
    return {k: v for d in parts for k, v in d.items()}


@st.cache_resource
def _translation_store() -> dict:
    """헤드라인 한 건 단위 번역 저장소 (앱 전체가 공유). 이미 번역한 문장은 다시 요청하지 않는다."""
    return {"ko": {}, "engine": None}


def translate(texts: tuple):
    """영→한 번역. 새로 들어온 헤드라인만 번역하고 나머지는 저장소에서 꺼낸다.
    Claude API 키가 있으면 Claude, 없으면 Google 번역. 실패한 문장은 원문 그대로."""
    store = _translation_store()
    ko = store["ko"]
    missing = [t for t in dict.fromkeys(texts) if t not in ko]
    if missing:
        new, engine = {}, None
        key = _anthropic_key()
        if key:
            try:
                new = dict(zip(missing, _translate_claude(missing, key)))
                engine = "Claude"
            except Exception:
                new = {}
        if len(new) < len(missing):
            rest = [t for t in missing if t not in new]
            got = _translate_google(rest)
            if got:
                new.update(got)
                engine = engine or "Google 번역"
        ko.update(new)
        if engine:
            store["engine"] = engine
        # 저장소가 너무 커지지 않게 오래된 것부터 정리
        if len(ko) > 5000:
            for k in list(ko)[: len(ko) - 4000]:
                ko.pop(k, None)
    out = [ko.get(t, t) for t in texts]
    engine = store["engine"] if any(t in ko for t in texts) else None
    return out, engine


@st.cache_data(ttl=900, show_spinner=False)
def _ranked(cons: pd.DataFrame, caps: pd.Series, hours: int, top_n: int):
    """수집 + 묶기·순위 (15분 캐싱). 화면의 다른 버튼을 눌러도 다시 계산하지 않는다."""
    df = fetch_headlines(hours)
    n_outlets = df["outlet"].nunique() if not df.empty else 0
    return cluster_and_rank(df, cons, caps, top_n), len(df), n_outlets


def top_issues(cons: pd.DataFrame, caps: pd.Series, hours: int = 24, top_n: int = 8):
    """수집 → 묶기·순위 → 번역까지 끝낸 결과.
    번역은 캐시 밖에서 하므로 한 번 실패해도 다음 새로고침 때 다시 시도된다."""
    issues, n_articles, n_outlets = _ranked(cons, caps, hours, top_n)
    texts = []
    for it in issues:
        texts.append(it["title"])
        texts += [a["title"] for a in it["articles"]]
    translated, engine = translate(tuple(texts))
    ko = dict(zip(texts, translated))
    for it in issues:
        it["title_ko"] = ko.get(it["title"], it["title"])
        for a in it["articles"]:
            a["title_ko"] = ko.get(a["title"], a["title"])
    return issues, engine, n_articles, n_outlets
