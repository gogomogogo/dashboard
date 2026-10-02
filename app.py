"""미국 주식 대시보드 — 실행: streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="미국 시장 대시보드", page_icon="📈", layout="wide")

pages = [
    st.Page("views/overview.py", title="시장 개요", icon="🗺️", default=True),
    st.Page("views/stock.py", title="종목 분석", icon="🔎", url_path="stock"),
    st.Page("views/calendar.py", title="캘린더", icon="🗓️", url_path="calendar"),
]
st.navigation(pages, position="top").run()
