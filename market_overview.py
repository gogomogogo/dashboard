"""시장 개요: S&P 500 히트맵 + 거시 지표."""
from datetime import datetime

import pandas as pd
import streamlit as st

import charts
import data
import news
from common import embed_html

VIEWS = ["원본", "1차 미분", "2차 미분"]

with st.sidebar:
    st.header("시장 개요 설정")
    period = st.radio(
        "히트맵 등락률 기준",
        ["1D", "1W", "1M", "YTD"],
        format_func={"1D": "1일", "1W": "1주", "1M": "1개월", "YTD": "연초 대비"}.get,
        horizontal=True,
    )
    news_hours = st.radio("주요 이슈 범위", [12, 24, 48], index=1, horizontal=True,
                          format_func=lambda h: f"{h}시간")
    window = st.number_input("미분용 이동평균 기간 (거래일)", 5, 250, 30, step=5)
    smooth = st.number_input(
        "2차 미분 추가 평활화 (거래일, 0 = 끔)", 0, 60, 0, step=5,
        help="2차 미분은 값이 많이 출렁이므로, 필요하면 한 번 더 이동평균을 적용합니다.",
    )
    if st.button("데이터 새로고침", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption(
        "시세는 Yahoo Finance 기준이며 약 15분 지연됩니다. "
        "차트에서 마우스 휠로 기간을 줌, 드래그로 이동, 더블클릭으로 초기화할 수 있습니다."
    )


def transform(s: pd.Series, view: str) -> pd.Series:
    """원본 / 이동평균의 1차 미분 / 2차 미분 (거래일 단위 변화량)."""
    if view == "원본":
        return s
    ma = s.rolling(window, min_periods=window).mean()
    d1 = ma.diff()
    if view == "1차 미분":
        return d1.dropna()
    d2 = d1.diff()
    if smooth:
        d2 = d2.rolling(smooth, min_periods=smooth).mean()
    return d2.dropna()


def indicator_panel(key, title, loader, color, unit="", decimals=2):
    """지표 하나: 제목 + 현재값 + 보기 전환 + 선 차트."""
    with st.container(border=True):
        try:
            s, note = loader()
        except Exception as e:
            st.subheader(title)
            st.error(f"데이터를 불러오지 못했습니다: {e}")
            return

        head, ctrl = st.columns([3, 2], vertical_alignment="bottom")
        last, prev = s.iloc[-1], s.iloc[-2]
        head.metric(
            title,
            f"{last:,.{decimals}f}{unit}",
            f"{last - prev:+,.{decimals}f}{unit}",
            delta_color="off",
            help=f"{note} · 마지막 데이터 {s.index[-1]:%Y-%m-%d}",
        )
        view = ctrl.segmented_control(
            "보기", VIEWS, default="원본", key=f"view_{key}", label_visibility="collapsed"
        ) or "원본"

        shown = transform(s, view)
        if shown.empty:
            st.info("이동평균 기간보다 데이터가 짧아 미분값을 계산할 수 없습니다.")
            return
        is_diff = view != "원본"
        html = charts.line_chart_html(
            shown,
            color=color,
            unit="" if is_diff else unit,
            decimals=decimals + (2 if is_diff else 0),
            zero_line=is_diff,
        )
        embed_html(html, height=345)
        if is_diff:
            st.caption(f"{window}거래일 이동평균의 {view} · 하루당 변화량")


st.title("미국 시장 개요")
st.caption(f"마지막 갱신 {datetime.now():%Y-%m-%d %H:%M}")

st.subheader("S&P 500 히트맵")
try:
    with st.spinner("S&P 500 종목 데이터를 불러오는 중입니다. 처음 한 번은 1~2분 걸릴 수 있습니다."):
        cons = data.get_sp500_constituents()
        tickers = tuple(cons["ticker"])
        caps = data.get_market_caps(tickers)
        closes = data.get_closes(tickers)
    rets = data.compute_returns(closes, period)
    hm = cons.assign(
        market_cap=cons["ticker"].map(caps),
        ret=cons["ticker"].map(rets),
    )
    missing = hm[["market_cap", "ret"]].isna().any(axis=1).sum()
    embed_html(charts.heatmap_html(hm, period, height=760), height=765)
    note = "박스 크기는 시가총액, 색은 등락률입니다. 종목을 클릭하면 새 탭에서 종목 분석이 열립니다."
    if missing:
        note += f" 데이터를 받지 못한 {missing}개 종목은 제외했습니다."
    st.caption(note)
except Exception as e:
    st.error(f"히트맵 데이터를 불러오지 못했습니다: {e}")


# ---------------------------------------------------------------- 주요 이슈
def _md(text: str) -> str:
    """마크다운에서 깨지는 문자 정리 ($는 수식, []는 링크로 해석됨)."""
    return str(text).replace("$", "\\$").replace("[", "(").replace("]", ")")


def _ago(ts) -> str:
    mins = int((pd.Timestamp.now(tz="UTC") - ts).total_seconds() // 60)
    if mins < 60:
        return f"{max(mins, 1)}분 전"
    if mins < 60 * 24:
        return f"{mins // 60}시간 전"
    return f"{mins // 1440}일 전"


def issue_card(rank: int, it: dict):
    with st.container(border=True):
        st.markdown(f"**{rank}. [{_md(it['title_ko'])}]({it['url']})**")
        if it["title_ko"] != it["title"]:
            st.caption(_md(it["title"]))
        badges = " ".join(f":blue-badge[{o}]" for o in it["outlets"])
        stocks = " ".join(f"[{t}](/stock?ticker={t})" for t in it["stocks"])
        meta = f"{badges} &nbsp; :gray[{len(it['outlets'])}개 매체 · 첫 보도 {_ago(it['first'])}]"
        if stocks:
            meta += f" &nbsp; {stocks}"
        st.markdown(meta)
        if len(it["articles"]) > 1:
            with st.expander(f"매체별 기사 {len(it['articles'])}건"):
                for a in it["articles"]:
                    line = f":gray-badge[{a['outlet']}] [{_md(a['title_ko'])}]({a['url']})"
                    sub = _md(a["title"]) if a["title_ko"] != a["title"] else ""
                    st.markdown(f"{line}  \n:gray[{sub}{' · ' if sub else ''}{_ago(a['time'])}]")


st.subheader("주요 이슈")
issues_slot = st.container()  # 자리만 먼저 잡고, 지표 차트를 그린 뒤 맨 마지막에 채운다

st.subheader("시장 지표")
c1, c2 = st.columns(2)
with c1:
    indicator_panel("us10y", "미국 10년물 국채금리", data.get_us10y, "#e0a43a", unit="%")
with c2:
    def _fg():
        s, rating = data.get_fear_greed()
        return s, f"현재 {rating}" if rating else "CNN"

    indicator_panel("fg", "공포와 탐욕 지수", _fg, "#9b7fe6", decimals=0)

c3, c4 = st.columns(2)
with c3:
    indicator_panel(
        "krw", "원/달러 환율", lambda: (data.get_usdkrw(), "Yahoo KRW=X"),
        "#3fa7d6", unit="원", decimals=1,
    )
with c4:
    indicator_panel(
        "vix", "VIX", lambda: (data.get_vix(), "Yahoo ^VIX"), "#e5604d", decimals=2,
    )

# ---------------------------------------------------------------- 주요 이슈 채우기
with issues_slot:
    try:
        with st.spinner("주요 매체 헤드라인을 모아 이슈별로 정리하는 중"):
            try:
                cons_n = data.get_sp500_constituents()
                caps_n = data.get_market_caps(tuple(cons_n["ticker"]))
            except Exception:
                cons_n, caps_n = pd.DataFrame({"ticker": [], "name": []}), pd.Series(dtype=float)
            issues, engine, n_articles, n_outlets = news.top_issues(cons_n, caps_n, hours=news_hours)
        if not issues:
            st.info("가져온 헤드라인이 없습니다. 잠시 후 '데이터 새로고침'을 눌러 보세요.")
        else:
            cols = st.columns(2)
            for i, it in enumerate(issues):
                with cols[i % 2]:
                    issue_card(i + 1, it)
            note = (f"최근 {news_hours}시간 동안 {n_outlets}개 매체의 헤드라인 {n_articles}건을 이슈별로 묶어, "
                    "보도한 매체 수·시장 영향·최신성 순으로 정렬했습니다.")
            note += f" 번역: {engine}." if engine else " 번역 서비스에 연결하지 못해 원문으로 표시합니다."
            st.caption(note)
    except Exception as e:
        st.error(f"주요 이슈를 불러오지 못했습니다: {e}")
