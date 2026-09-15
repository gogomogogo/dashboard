"""
간단 금융 대시보드 — Streamlit 버전
실행: streamlit run app.py
"""

import pandas as pd
import streamlit as st
import yfinance as yf
import altair as alt

# ---------------------------------------------------------------
# 1. 페이지 기본 설정
# ---------------------------------------------------------------
st.set_page_config(page_title="마켓 모니터", page_icon="📊", layout="wide")


# ---------------------------------------------------------------
# 2. 데이터 가져오기
#    @st.cache_data = 한 번 받아온 데이터를 1시간 동안 재사용.
#    이거 없으면 페이지 새로고침할 때마다 다시 받아와서 느려집니다.
# ---------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_yahoo(ticker: str, period: str = "2y") -> pd.DataFrame:
    """야후 파이낸스에서 주가/환율/원자재 가격을 가져옵니다."""
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if df.empty:
        return pd.DataFrame()
    out = df[["Close"]].copy()
    out.columns = ["value"]          # 컬럼 이름 통일
    out.index.name = "date"
    return out.reset_index()


@st.cache_data(ttl=3600)
def get_fred(series_id: str) -> pd.DataFrame:
    """
    FRED(세인트루이스 연준)에서 금리·경제지표를 가져옵니다.
    이 주소는 API 키가 없어도 CSV로 바로 받을 수 있습니다.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url)
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    # FRED는 결측치를 '.' 으로 주기 때문에 숫자로 바꾸면서 걸러냅니다
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna()


def drawdown(df: pd.DataFrame) -> pd.DataFrame:
    """전고점 대비 낙폭(%) 계산. 지금까지의 최고가 대비 몇 % 내려왔는지."""
    df = df.copy()
    df["value"] = (df["value"] / df["value"].cummax() - 1) * 100
    return df


# ---------------------------------------------------------------
# 3. 차트 그리는 함수 (한 번 만들어두고 계속 재사용)
# ---------------------------------------------------------------
def line_chart(df: pd.DataFrame, color: str = "#2563eb", zero_line: bool = False):
    if df.empty:
        st.warning("데이터를 불러오지 못했습니다.")
        return

    chart = (
        alt.Chart(df)
        .mark_area(
            line={"color": color, "strokeWidth": 2},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color=color, offset=0),
                    alt.GradientStop(color="white", offset=1),
                ],
                x1=1, x2=1, y1=1, y2=0,
            ),
            opacity=0.25,
        )
        .encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("value:Q", title=None, scale=alt.Scale(zero=False)),
            tooltip=["date:T", alt.Tooltip("value:Q", format=".2f")],
        )
        .properties(height=240)
    )

    if zero_line:  # 0선 표시 (금리차, 낙폭 차트에 유용)
        rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
            color="#999", strokeDash=[4, 4]
        ).encode(y="y:Q")
        chart = chart + rule

    st.altair_chart(chart, use_container_width=True)


def show_metric(label: str, df: pd.DataFrame, suffix: str = ""):
    """맨 위 요약 숫자 카드. 마지막 값과 전일 대비 변화를 보여줍니다."""
    if df.empty or len(df) < 2:
        st.metric(label, "—")
        return
    latest = float(df["value"].iloc[-1])
    prev = float(df["value"].iloc[-2])
    st.metric(label, f"{latest:,.2f}{suffix}", f"{latest - prev:+,.2f}")


# ---------------------------------------------------------------
# 4. 화면 구성 — 여기부터가 실제 페이지입니다
# ---------------------------------------------------------------
st.title("마켓 모니터")
st.caption("출처: Yahoo Finance, FRED · 정보 제공 목적이며 투자 권유가 아닙니다")

# 지금 필요한 데이터를 한 번에 받아옵니다
sp500 = get_yahoo("^GSPC")
kospi = get_yahoo("^KS11")
usdkrw = get_yahoo("KRW=X")
gold = get_yahoo("GC=F")
dgs10 = get_fred("DGS10")     # 미국 10년물 국채금리
spread = get_fred("T10Y2Y")   # 장단기 금리차
vix = get_fred("VIXCLS")      # VIX 변동성지수

# --- 요약 카드 한 줄 ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    show_metric("S&P500", sp500)
with c2:
    show_metric("코스피", kospi)
with c3:
    show_metric("원달러", usdkrw, "원")
with c4:
    show_metric("VIX", vix)

st.divider()

# --- 개별 섹션들 ---
left, right = st.columns(2)

with left:
    st.subheader("S&P500 전고점 대비 낙폭")
    line_chart(drawdown(sp500), color="#dc2626", zero_line=True)
    st.caption("0%는 사상 최고가. -20% 아래면 약세장으로 봅니다.")

with right:
    st.subheader("코스피 전고점 대비 낙폭")
    line_chart(drawdown(kospi), color="#dc2626", zero_line=True)
    st.caption("S&P500과 나란히 보면 한국 증시의 상대 강도가 보입니다.")

left, right = st.columns(2)

with left:
    st.subheader("미국 10년물 국채금리")
    line_chart(dgs10, color="#2563eb")
    st.caption("주식 밸류에이션의 기준이 되는 금리입니다.")

with right:
    st.subheader("장단기 금리차 (10년 - 2년)")
    line_chart(spread, color="#7c3aed", zero_line=True)
    st.caption("0 아래로 내려가면 금리 역전. 과거 경기침체의 선행 신호였습니다.")

left, right = st.columns(2)

with left:
    st.subheader("원달러 환율")
    line_chart(usdkrw, color="#059669")

with right:
    st.subheader("금 (USD/온스)")
    line_chart(gold, color="#d97706")
