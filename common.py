"""페이지 공통 도우미."""
import streamlit as st


def embed_html(html: str, height: int):
    """Streamlit 버전에 맞춰 HTML을 iframe으로 표시."""
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=height)


def is_dark() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False
