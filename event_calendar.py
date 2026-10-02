"""캘린더: 주요국 경제지표 발표 일정, 미국 실적발표 일정 (주 단위)."""
from datetime import date, timedelta

import streamlit as st

import calendars as cal
import data
from common import embed_html, is_dark

st.title("캘린더")

kind = st.segmented_control("종류", ["경제지표", "실적발표"], default="경제지표",
                            key="cal_kind", label_visibility="collapsed") or "경제지표"

# ---------------------------------------------------------------- 주 이동
if "week_offset" not in st.session_state:
    st.session_state.week_offset = 0


def shift(n):
    st.session_state.week_offset = 0 if n == 0 else st.session_state.week_offset + n


this_monday = date.today() - timedelta(days=date.today().weekday())
week_start = this_monday + timedelta(weeks=st.session_state.week_offset)
week_end = week_start + timedelta(days=6)

nav = st.columns([1, 1, 1, 5], vertical_alignment="center")
nav[0].button("← 이전 주", on_click=shift, args=(-1,), width="stretch")
nav[1].button("이번 주", on_click=shift, args=(0,), width="stretch",
              disabled=st.session_state.week_offset == 0)
nav[2].button("다음 주 →", on_click=shift, args=(1,), width="stretch")
nav[3].markdown(f"**{week_start:%Y.%m.%d} ~ {week_end:%m.%d}**")

# Yahoo는 UTC 기준이라 앞뒤로 하루씩 넉넉히 받아서 현지 날짜로 다시 나눈다
q_start = (week_start - timedelta(days=1)).isoformat()
q_end = (week_end + timedelta(days=1)).isoformat()


def in_week(items: dict) -> dict:
    return {d: v for d, v in items.items() if week_start <= d <= week_end}


# ---------------------------------------------------------------- 경제지표
if kind == "경제지표":
    try:
        with st.spinner("경제지표 일정을 불러오는 중"):
            econ = data.get_economic_calendar(q_start, q_end)
    except Exception as e:
        st.error(f"경제지표 일정을 불러오지 못했습니다: {e}")
        st.stop()

    regions = sorted(econ["region"].dropna().unique()) if not econ.empty else []
    f1, f2 = st.columns([4, 1], vertical_alignment="bottom")
    picked = f1.multiselect(
        "국가", regions, default=[r for r in regions if r in cal.DEFAULT_REGIONS] or regions,
        format_func=cal.region_label, key="regions",
    )
    major_only = f2.toggle("주요 지표만", value=True, key="major_only",
                           help="CPI, 고용, GDP, 금리 결정, PMI 등 시장 영향이 큰 지표만 보여줍니다.")

    view = econ[econ["region"].isin(picked)] if not econ.empty else econ
    if major_only and not view.empty:
        view = view[view["event"].map(cal.is_major)]

    items = in_week(cal.economic_items(view))
    embed_html(cal.week_html(week_start, items, is_dark(), 720, "예정된 발표 없음"), height=725)
    st.caption(
        f"시간은 한국 시간(KST) 기준입니다. 왼쪽에 노란 선이 있는 항목은 주요 지표입니다. "
        f"출처 {econ['source'].iloc[0] if not econ.empty else '-'}"
    )

# ---------------------------------------------------------------- 실적발표
else:
    caps = {"$2B 이상": 2e9, "$10B 이상": 1e10, "$50B 이상": 5e10, "$200B 이상": 2e11}
    f1, f2 = st.columns([1, 3], vertical_alignment="bottom")
    cap_label = f1.selectbox("시가총액", list(caps), index=1, key="min_cap")
    sp_only = f2.toggle("S&P 500 종목만", value=False, key="sp_only")

    try:
        with st.spinner("실적발표 일정을 불러오는 중"):
            earn = data.get_earnings_calendar(q_start, q_end, caps[cap_label])
    except Exception as e:
        st.error(f"실적발표 일정을 불러오지 못했습니다: {e}")
        st.stop()

    if sp_only and not earn.empty:
        try:
            members = set(data.get_sp500_constituents()["ticker"])
            earn = earn[earn["ticker"].isin(members)]
        except Exception:
            st.warning("S&P 500 목록을 불러오지 못해 전체 종목을 표시합니다.")

    items = in_week(cal.earnings_items(earn))
    embed_html(cal.week_html(week_start, items, is_dark(), 720, "예정된 발표 없음"), height=725)
    st.caption(
        "날짜는 미국 동부 시간 기준입니다. '장 마감 후' 발표는 한국 시간으로 다음 날 아침입니다. "
        "종목을 클릭하면 새 탭에서 종목 분석이 열립니다. "
        f"출처 {earn['source'].iloc[0] if not earn.empty else '-'}"
    )
