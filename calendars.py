"""경제지표·실적발표 주간 캘린더 HTML."""
import html as _h
from datetime import date, timedelta

import pandas as pd

KST = "Asia/Seoul"
NY = "America/New_York"

REGION_NAMES = {
    "US": "미국", "EU": "유로존", "EZ": "유로존", "CN": "중국", "JP": "일본", "GB": "영국",
    "UK": "영국", "DE": "독일", "FR": "프랑스", "IT": "이탈리아", "ES": "스페인", "KR": "한국",
    "CA": "캐나다", "AU": "호주", "NZ": "뉴질랜드", "CH": "스위스", "IN": "인도", "BR": "브라질",
    "MX": "멕시코", "SG": "싱가포르", "HK": "홍콩", "TW": "대만", "SE": "스웨덴", "NO": "노르웨이",
    "ZA": "남아공", "TR": "튀르키예", "RU": "러시아", "ID": "인도네시아",
}
DEFAULT_REGIONS = ["US", "EU", "EZ", "CN", "JP", "GB", "UK", "DE", "KR"]

# 시장 영향이 큰 지표 (이벤트 이름에 포함되면 '주요'로 표시)
MAJOR_KEYWORDS = [
    "cpi", "consumer price", "nonfarm", "non-farm", "payroll", "unemployment rate", "gdp",
    "pce", "interest rate", "rate decision", "fomc", "fed ", "retail sales", "ppi",
    "producer price", "ism", "pmi", "jolts", "jobless claims", "ecb", "boj", "boe",
    "core inflation", "inflation rate", "trade balance", "industrial production",
]

WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


def flag(code: str) -> str:
    code = {"EZ": "EU", "UK": "GB"}.get(str(code).upper(), str(code).upper())
    if len(code) != 2 or not code.isalpha():
        return "🌐"
    return chr(0x1F1E6 + ord(code[0]) - 65) + chr(0x1F1E6 + ord(code[1]) - 65)


def region_label(code: str) -> str:
    return f"{flag(code)} {REGION_NAMES.get(str(code).upper(), code)}"


def is_major(event: str) -> bool:
    e = f" {str(event).lower()} "
    return any(k in e for k in MAJOR_KEYWORDS)


def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "-"
    if isinstance(v, (int, float)):
        return f"{v:,.2f}".rstrip("0").rstrip(".")
    return _h.escape(str(v))


# ---------------------------------------------------------------- 공통 틀
def _palette(dark: bool) -> dict:
    if dark:
        return dict(bg="#1a1c22", head="#23262e", line="#2e323c", text="#e3e6ea", sub="#8b93a1",
                    today="#2b3a52", major="#e0a43a", card="#20232a")
    return dict(bg="#ffffff", head="#f3f4f6", line="#e2e5ea", text="#1f2328", sub="#6b7280",
                today="#e8f0fe", major="#c47f10", card="#fafbfc")


def week_html(week_start: date, day_items: dict, dark: bool, height: int, empty_text: str) -> str:
    """day_items: {date: [html 조각, ...]}. 주말은 일정이 있을 때만 표시."""
    p = _palette(dark)
    days = [week_start + timedelta(days=i) for i in range(7)]
    days = [d for d in days if d.weekday() < 5 or day_items.get(d)]
    today = date.today()

    cols = []
    for d in days:
        items = day_items.get(d, [])
        body = "".join(items) if items else f'<div class="empty">{empty_text}</div>'
        cls = "day today" if d == today else "day"
        n = sum(1 for x in items if not x.startswith('<div class="grp"'))
        cols.append(
            f'<div class="{cls}"><div class="dh"><span class="dn">{d.month}/{d.day}</span>'
            f'<span class="dw">{WEEKDAYS[d.weekday()]}</span><span class="cnt">{f"{n}건" if n else ""}</span></div>'
            f'<div class="db">{body}</div></div>'
        )

    css = f"""
html,body{{margin:0;padding:0;background:transparent;color:{p['text']};
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Apple SD Gothic Neo","Malgun Gothic",sans-serif;font-size:12px}}
.wrap{{display:grid;grid-template-columns:repeat({len(days)},minmax(150px,1fr));gap:6px;overflow-x:auto;height:{height}px}}
.day{{display:flex;flex-direction:column;min-height:0;border:1px solid {p['line']};border-radius:8px;background:{p['bg']};overflow:hidden}}
.day.today{{border-color:#3f7be0}}
.dh{{display:flex;align-items:baseline;gap:6px;padding:7px 9px;background:{p['head']};border-bottom:1px solid {p['line']}}}
.today .dh{{background:{p['today']}}}
.dn{{font-weight:700;font-size:14px}} .dw{{color:{p['sub']}}} .cnt{{margin-left:auto;color:{p['sub']};font-size:11px}}
.db{{overflow-y:auto;padding:6px;display:flex;flex-direction:column;gap:5px}}
.empty{{color:{p['sub']};padding:8px 2px}}
.it{{padding:6px 7px;border-radius:6px;background:{p['card']};border:1px solid {p['line']};border-left:3px solid {p['line']};line-height:1.4}}
.it.major{{border-left-color:{p['major']}}}
.it .tm{{color:{p['sub']};font-size:11px}}
.it .nm{{font-weight:600;word-break:keep-all}}
.it .nums{{color:{p['sub']};font-size:11px}}
.it .nums b{{color:{p['text']}}}
.grp{{font-size:11px;color:{p['sub']};font-weight:600;margin:4px 0 0}}
.er{{display:flex;align-items:center;gap:6px;padding:4px 6px;border-radius:6px;background:{p['card']};border:1px solid {p['line']};text-decoration:none;color:inherit}}
.er:hover{{border-color:#3f7be0}}
.er img{{width:20px;height:20px;border-radius:5px;background:#fff;object-fit:contain;flex:none}}
.er .tk{{font-weight:700}} .er .co{{color:{p['sub']};font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.er .eps{{margin-left:auto;text-align:right;font-size:11px;color:{p['sub']};white-space:nowrap}}
.pos{{color:#1e8e4e;font-weight:600}} .neg{{color:#c0392b;font-weight:600}}
"""
    js = """
const LOGOS=[t=>`https://financialmodelingprep.com/image-stock/${t}.png`,
             t=>`https://assets.parqet.com/logos/symbol/${t}?format=png`];
document.querySelectorAll('img[data-t]').forEach(img=>{
  let i=0; const t=img.dataset.t; img.src=LOGOS[0](t);
  img.onerror=()=>{i++; if(i<LOGOS.length) img.src=LOGOS[i](t); else img.style.visibility='hidden';};
});
document.querySelectorAll('a[data-t]').forEach(a=>{
  try{ a.href = window.parent.location.origin + '/stock?ticker=' + encodeURIComponent(a.dataset.t); }catch(e){}
});
"""
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}</style></head>'
            f'<body><div class="wrap">{"".join(cols)}</div><script>{js}</script></body></html>')


# ---------------------------------------------------------------- 경제지표
def economic_items(df: pd.DataFrame) -> dict:
    out = {}
    if df.empty:
        return out
    df = df.assign(local=df["time"].dt.tz_convert(KST)).sort_values("local")
    for r in df.itertuples():
        d = r.local.date()
        tm = r.local.strftime("%H:%M")
        period = f" ({_h.escape(str(r.period))})" if isinstance(r.period, str) and r.period else ""
        actual = "" if pd.isna(r.actual) else f" | 발표 <b>{_fmt(r.actual)}</b>"
        cls = "it major" if is_major(r.event) else "it"
        out.setdefault(d, []).append(
            f'<div class="{cls}"><div class="tm">{tm} {flag(r.region)} {_h.escape(REGION_NAMES.get(str(r.region).upper(), str(r.region)))}</div>'
            f'<div class="nm">{_h.escape(str(r.event))}{period}</div>'
            f'<div class="nums">예상 {_fmt(r.expected)} | 이전 {_fmt(r.last)}{actual}</div></div>'
        )
    return out


# ---------------------------------------------------------------- 실적발표
TIMING = {"BMO": "장 시작 전", "AMC": "장 마감 후"}


def earnings_items(df: pd.DataFrame) -> dict:
    out = {}
    if df.empty:
        return out
    df = df.assign(local=df["time"].dt.tz_convert(NY))
    df["slot"] = df["timing"].map(TIMING).fillna("시간 미정")
    order = {"장 시작 전": 0, "장 마감 후": 1, "시간 미정": 2}
    df = df.sort_values(["cap"], ascending=False)
    for d, g in df.groupby(df["local"].dt.date):
        parts = []
        for slot, sg in sorted(g.groupby("slot"), key=lambda kv: order[kv[0]]):
            parts.append(f'<div class="grp">{slot} ({len(sg)})</div>')
            for r in sg.itertuples():
                t = _h.escape(str(r.ticker))
                if not pd.isna(r.eps_act):
                    sp = r.surprise
                    cls = "pos" if not pd.isna(sp) and sp >= 0 else "neg"
                    sp_txt = "" if pd.isna(sp) else f' <span class="{cls}">{sp:+.1f}%</span>'
                    eps = f"실제 {r.eps_act:.2f}{sp_txt}<br>예상 {_fmt(r.eps_est)}"
                else:
                    eps = f"예상 EPS<br>{_fmt(r.eps_est)}"
                parts.append(
                    f'<a class="er" data-t="{t}" target="_blank"><img data-t="{t}" alt="">'
                    f'<div style="min-width:0"><div class="tk">{t}</div>'
                    f'<div class="co">{_h.escape(str(r.company or ""))}</div></div>'
                    f'<div class="eps">{eps}</div></a>'
                )
        out[d] = parts
    return out
