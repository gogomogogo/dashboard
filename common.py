"""페이지 공통 도우미."""
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

import streamlit as st

# 데이터 불러오기를 시간 제한과 함께 돌리는 공용 작업자.
# 응답이 끝없이 늦어지는 서버가 있어도 페이지 전체가 멈추지 않게 한다.
_POOL = ThreadPoolExecutor(max_workers=16, thread_name_prefix="loader")


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


def _log(label: str, seconds: float, status: str):
    st.session_state.setdefault("_timings", {})[label] = (seconds, status)


def timed(label: str, fn, timeout: float = 40):
    """fn()을 최대 timeout초까지만 기다린다. 넘으면 그 칸만 건너뛰고 페이지는 계속 그린다.
    걸린 시간은 사이드바 '로딩 진단'에 기록된다."""
    t0 = time.time()
    future = _POOL.submit(fn)
    try:
        result = future.result(timeout=timeout)
    except FutureTimeout:
        _log(label, time.time() - t0, "시간 초과")
        raise RuntimeError(f"{timeout:.0f}초 안에 응답이 없어 건너뛰었습니다. 잠시 후 새로고침해 보세요.")
    except Exception:
        _log(label, time.time() - t0, "오류")
        raise
    _log(label, time.time() - t0, "완료")
    return result


def start_timings():
    """페이지 맨 위에서 호출: 이번 실행의 기록을 비운다."""
    st.session_state["_timings"] = {}
    st.session_state["_page_t0"] = time.time()


def show_timings():
    """페이지 맨 아래에서 호출: 사이드바에 칸별 로딩 시간을 보여준다."""
    rows = st.session_state.get("_timings", {})
    total = time.time() - st.session_state.get("_page_t0", time.time())
    with st.sidebar.expander(f"로딩 진단 (전체 {total:.1f}초)", expanded=False):
        if not rows:
            st.caption("기록 없음")
        for label, (sec, status) in rows.items():
            color = {"완료": "green", "오류": "orange", "시간 초과": "red"}[status]
            st.markdown(f"{label}: **{sec:.1f}초** :{color}[{status}]")
        st.caption("캐시된 칸은 0초에 가깝게 나옵니다. 오래 걸린 칸을 알려주시면 원인을 찾기 쉽습니다.")
