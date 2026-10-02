"""미국 주식 대시보드 — 실행: streamlit run app.py"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="미국 시장 대시보드", page_icon="📈", layout="wide")

BASE = Path(__file__).resolve().parent


def page_file(name: str) -> Path:
    """페이지 파일을 views/ 폴더 또는 app.py와 같은 폴더에서 찾는다."""
    for p in (BASE / "views" / name, BASE / name):
        if p.exists():
            return p
    st.error(
        f"페이지 파일 `{name}`을 찾을 수 없습니다. "
        f"`views/{name}` 또는 app.py와 같은 폴더에 있는지 확인해 주세요."
    )
    st.stop()


pages = [
    st.Page(page_file("market_overview.py"), title="시장 개요", icon="🗺️", default=True),
    st.Page(page_file("stock_analysis.py"), title="종목 분석", icon="🔎", url_path="stock"),
    st.Page(page_file("event_calendar.py"), title="캘린더", icon="🗓️", url_path="calendar"),
]
st.navigation(pages, position="top").run()
